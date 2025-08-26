import streamlit as st
import os
import tempfile
import pandas as pd
from main import ResumeEvaluator

API_KEY_FILE = ".api_key"

def load_api_key():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    return ""

def main():
    st.set_page_config(
        page_title="Resume ATS Evaluator",
        page_icon="📄",
        layout="wide"
    )
    
    # Simple header
    st.title("📄 Resume ATS Evaluator")
    st.markdown("**Upload job description and resume files for automated evaluation**")
    st.divider()
    
    # API Key in sidebar
    with st.sidebar:
        st.header("Settings")
        
        if "api_key" not in st.session_state:
            st.session_state.api_key = load_api_key()
            
        api_key = st.text_input(
            "Azure OpenAI API Key",
            type="password",
            placeholder="Enter your API key...",
            key="api_key"
        )

        if api_key:
            st.success("✅ API Key Set")
        else:
            st.warning("⚠️ API Key Required")
            
        st.divider()
        
        st.subheader("Instructions")
        st.markdown("""
        1. Enter API key above
        2. Upload job description
        3. Upload resume files
        4. Click process
        5. Download results
        """)
        
        st.divider()
        
        st.subheader("💡 Optimization")
        st.info("This system extracts job requirements once and reuses them for all resumes, saving tokens and reducing costs!")

    # File uploads in two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Job Description")
        job_description_file = st.file_uploader(
            "Upload job description file",
            type=['pdf', 'doc', 'docx'],
            key="job_desc"
        )
        
        if job_description_file:
            st.success(f"✅ {job_description_file.name}")

    with col2:
        st.subheader("📄 Resume Files")
        resume_files = st.file_uploader(
            "Upload resume files",
            accept_multiple_files=True,
            type=['pdf', 'doc', 'docx'],
            key="resumes"
        )
        
        if resume_files:
            st.success(f"✅ {len(resume_files)} files uploaded")
            with st.expander("View files"):
                for i, file in enumerate(resume_files, 1):
                    st.write(f"{i}. {file.name}")

    st.divider()
    
    # Process button
    if api_key and job_description_file and resume_files:
        if st.button("🚀 Process Resumes", type="primary", use_container_width=True):
            process_resumes(api_key, job_description_file, resume_files)
    else:
        # Show what's missing
        missing = []
        if not api_key:
            missing.append("API key")
        if not job_description_file:
            missing.append("job description")
        if not resume_files:
            missing.append("resume files")
        
        st.info(f"Please provide: {', '.join(missing)}")

def process_resumes(api_key, job_description_file, resume_files):
    """Process the uploaded resumes with optimized token usage"""
    
    progress_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    try:
        status_text.info("🔄 Setting up processing...")
        progress_bar.progress(10)
        
        # Create temporary directories
        with tempfile.TemporaryDirectory() as temp_dir:
            resume_dir = os.path.join(temp_dir, "resumes")
            os.makedirs(resume_dir, exist_ok=True)
            
            status_text.info("💾 Saving files...")
            progress_bar.progress(20)
            
            # Save job description
            job_desc_path = os.path.join(temp_dir, f"job_description.{job_description_file.name.split('.')[-1]}")
            with open(job_desc_path, "wb") as f:
                f.write(job_description_file.getbuffer())

            # Save resume files
            for resume_file in resume_files:
                file_path = os.path.join(resume_dir, resume_file.name)
                with open(file_path, "wb") as f:
                    f.write(resume_file.getbuffer())

            status_text.info("🧠 Analyzing job requirements...")
            progress_bar.progress(40)
            
            # Process resumes with optimized approach
            evaluator = ResumeEvaluator(api_key=api_key)
            
            status_text.info("🤖 Evaluating resumes...")
            progress_bar.progress(60)
            
            output_path = os.path.join(temp_dir, "evaluation_results.xlsx")
            result_df = evaluator.process_folder(
                folder_path=resume_dir,
                job_description_path=job_desc_path,
                output_path=output_path
            )
            
            status_text.info("📊 Preparing results...")
            progress_bar.progress(90)
            
            # Read Excel file for download
            with open(output_path, "rb") as f:
                excel_data = f.read()
            
            # Store in session state
            st.session_state.results = {
                'dataframe': result_df,
                'excel_data': excel_data
            }
            
            progress_bar.progress(100)
            status_text.success("✅ Processing complete!")
            
            # Clear progress after a moment
            import time
            time.sleep(1)
            progress_container.empty()
            
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        progress_container.empty()

def display_simple_results():
    """Display results in a simple format"""
    if 'results' not in st.session_state:
        return
        
    result_df = st.session_state.results['dataframe']
    excel_data = st.session_state.results['excel_data']
    
    st.divider()
    st.subheader("📊 Results")
    
    # Simple summary in one row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total", len(result_df))
    
    with col2:
        strong = len(result_df[result_df['Recommendation'] == 'Strongly Recommended']) if 'Recommendation' in result_df.columns else 0
        st.metric("Strong", strong)
    
    with col3:
        recommended = len(result_df[result_df['Recommendation'] == 'Recommended']) if 'Recommendation' in result_df.columns else 0
        st.metric("Good", recommended)
    
    with col4:
        # Calculate average of both scores
        exp_score = result_df['Experience Score'].mean() if 'Experience Score' in result_df.columns else 0
        skills_score = result_df['Skills Score'].mean() if 'Skills Score' in result_df.columns else 0
        avg_score = (exp_score + skills_score) / 2
        st.metric("Avg Score", f"{avg_score:.1f}/10")
    
    # Simple table with better column configuration
    st.subheader("Detailed Results")
    
    # Configure columns for better display
    column_config = {
        "Experience Score": st.column_config.ProgressColumn(
            "Experience Score",
            help="Experience match score out of 10",
            min_value=0,
            max_value=10,
        ),
        "Skills Score": st.column_config.ProgressColumn(
            "Skills Score", 
            help="Skills match score out of 10",
            min_value=0,
            max_value=10,
        )
    }
    
    st.dataframe(
        result_df, 
        use_container_width=True, 
        hide_index=True,
        column_config=column_config
    )
    
    # Download button
    st.subheader("Download")
    st.download_button(
        label="📥 Download Excel File",
        data=excel_data,
        file_name="resume_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True
    )

if __name__ == "__main__":
    main()
    display_simple_results()