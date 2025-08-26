import streamlit as st
import os
import zipfile
import tempfile
from main import ResumeEvaluator

API_KEY_FILE = ".api_key"

def load_api_key():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    return ""

def extract_zip(zip_file, extract_to):
    """Extract ZIP file to specified directory"""
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def main():
    st.set_page_config(
        page_title="Resume ATS Evaluator",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 Resume ATS Evaluation System")
    st.markdown("Upload a folder of resumes and a job description to get automated evaluations")
    
    # Sidebar for API key
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Load API key from file if not in session state
        if "api_key" not in st.session_state:
            st.session_state.api_key = load_api_key()
            
        api_key = st.text_input(
            "Azure OpenAI API Key",
            type="password",
            placeholder="Enter your API key here...",
            help="Your Azure OpenAI API key for processing resumes",
            key="api_key"
        )

        if api_key:
            st.success("✅ API key configured")
        else:
            st.warning("⚠️ Please enter your API key")

    # Main content
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("📋 Job Description")
        job_description_file = st.file_uploader(
            "Upload Job Description",
            type=['pdf', 'doc', 'docx'],
            help="Upload the job description file (PDF, DOC, or DOCX)"
        )
        
        if job_description_file:
            st.success(f"✅ Job description uploaded: {job_description_file.name}")

    with col2:
        st.header("📁 Resume Files")
        
        # Option 1: Upload individual files
        resume_files = st.file_uploader(
            "Upload Resume Files",
            accept_multiple_files=True,
            type=['pdf', 'doc', 'docx'],
            help="Upload multiple resume files or a ZIP containing resumes"
        )
        
        # Option 2: Upload ZIP file
        st.markdown("**OR**")
        zip_file = st.file_uploader(
            "Upload ZIP file containing resumes",
            type=['zip'],
            help="Upload a ZIP file containing all resume files"
        )

    # Display uploaded files info
    if resume_files:
        st.info(f"📄 {len(resume_files)} individual resume files uploaded")
    elif zip_file:
        st.info(f"📦 ZIP file uploaded: {zip_file.name}")

    # Process button
    if job_description_file and (resume_files or zip_file):
        if st.button("🚀 Evaluate Resumes", disabled=not api_key, type="primary"):
            if not api_key:
                st.error("❌ Please provide an API key in the sidebar")
                return

            with st.spinner("Processing resumes... This may take a few minutes."):
                try:
                    # Create temporary directories
                    with tempfile.TemporaryDirectory() as temp_dir:
                        resume_dir = os.path.join(temp_dir, "resumes")
                        os.makedirs(resume_dir, exist_ok=True)
                        
                        # Save job description
                        job_desc_path = os.path.join(temp_dir, f"job_description.{job_description_file.name.split('.')[-1]}")
                        with open(job_desc_path, "wb") as f:
                            f.write(job_description_file.getbuffer())

                        # Handle resume files
                        if zip_file:
                            # Extract ZIP file
                            zip_path = os.path.join(temp_dir, "resumes.zip")
                            with open(zip_path, "wb") as f:
                                f.write(zip_file.getbuffer())
                            extract_zip(zip_path, resume_dir)
                        else:
                            # Save individual files
                            for resume_file in resume_files:
                                file_path = os.path.join(resume_dir, resume_file.name)
                                with open(file_path, "wb") as f:
                                    f.write(resume_file.getbuffer())

                        # Initialize evaluator
                        evaluator = ResumeEvaluator(api_key=api_key)
                        
                        # Process resumes
                        output_path = os.path.join(temp_dir, "evaluation_results.xlsx")
                        result_df = evaluator.process_folder(
                            folder_path=resume_dir,
                            job_description_path=job_desc_path,
                            output_path=output_path
                        )
                        
                        # Show results
                        st.success(f"✅ Successfully evaluated {len(result_df)} resume(s)!")
                        
                        # Display summary statistics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Resumes", len(result_df))
                        with col2:
                            strongly_recommended = len(result_df[result_df['Recommendation'] == 'Strongly Recommended'])
                            st.metric("Strongly Recommended", strongly_recommended)
                        with col3:
                            recommended = len(result_df[result_df['Recommendation'] == 'Recommended'])
                            st.metric("Recommended", recommended)
                        with col4:
                            avg_score = result_df['Skills Score'].mean() if 'Skills Score' in result_df.columns else 0
                            st.metric("Avg Skills Score", f"{avg_score:.1f}")

                        # Display results table
                        st.header("📊 Evaluation Results")
                        st.dataframe(result_df, use_container_width=True)
                        
                        # Download button
                        with open(output_path, "rb") as file:
                            st.download_button(
                                label="📥 Download Excel Results",
                                data=file,
                                file_name="resume_evaluation_results.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary"
                            )
                            
                except Exception as e:
                    st.error(f"❌ Error processing resumes: {str(e)}")
                    st.exception(e)
    else:
        if not job_description_file:
            st.info("👆 Please upload a job description file")
        if not (resume_files or zip_file):
            st.info("👆 Please upload resume files or a ZIP file containing resumes")

if __name__ == "__main__":
    main()