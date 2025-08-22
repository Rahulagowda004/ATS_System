import streamlit as st
import os
from typing import List
from main import ResumeEvaluator
API_KEY_FILE = ".api_key"

def load_api_key():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    return ""

def main():
    st.set_page_config(
        page_title="Resume ATS",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 Resume ATS System")
    
    # Main content area
    st.header("📁 Upload Resume Files")
    
    # Maintain uploaded files in session state
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []

    uploaded_files = st.file_uploader(
        "Choose files",
        accept_multiple_files=True,
        type=['pdf', 'doc', 'docx'],
        help="Upload multiple resume files. Supported formats: PDF, DOC, DOCX"
    )

    # Update session state if new files are uploaded
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
    uploaded_files = st.session_state.uploaded_files

    # Sidebar for API key
    with st.sidebar:
        st.header("⚙️ Configuration")
        # Load API key from file if not in session state
        if "api_key" not in st.session_state:
            st.session_state.api_key = load_api_key()
        api_key = st.text_input(
            "API Key",
            type="password",
            placeholder="Enter your API key here...",
            help="Your API key for processing resumes",
            key="api_key"  # Remove value=st.session_state.api_key
        )

        if api_key:
            st.success("✅ API key configured")
        else:
            st.warning("⚠️ Please enter your API key")
        
        # Display uploaded files in sidebar
        if uploaded_files:
            st.header("📋 Uploaded Files")
            for i, file in enumerate(uploaded_files, 1):
                with st.expander(f"📄 {file.name}"):
                    st.write(f"**File:** {file.name}")
                   
    
    if uploaded_files:
        st.success(f"📄 {len(uploaded_files)} resumes uploaded successfully!")
        
        # Process button
        if st.button("🚀 Process Resumes", disabled=not api_key, type="primary"):
            if api_key:
                with st.spinner("Processing resumes..."):
                    try:
                        # Create a temporary directory to save uploaded files
                        temp_dir = "temp_resumes"
                        os.makedirs(temp_dir, exist_ok=True)
                        
                        # Save uploaded files to temp directory
                        for uploaded_file in uploaded_files:
                            file_path = os.path.join(temp_dir, uploaded_file.name)
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                        
                        # Initialize evaluator with API key
                        evaluator = ResumeEvaluator(api_key=api_key)
                        
                        # Process the directory
                        result_df = evaluator.process_directory(
                            dir_path=temp_dir,
                            template_path="template.xlsx",
                            output_path="ATS_details.xlsx"
                        )
                        
                        # Clean up temp files
                        for file in os.listdir(temp_dir):
                            os.remove(os.path.join(temp_dir, file))
                        os.rmdir(temp_dir)
                        
                        # Show success message and download button
                        st.success(f"✅ Successfully processed {len(uploaded_files)} resume(s)!")
                        
                        with open("ATS_details.xlsx", "rb") as file:
                            st.download_button(
                                label="📥 Download Results",
                                data=file,
                                file_name="ATS_details.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                            
                    except Exception as e:
                        st.error(f"❌ Error processing resumes: {str(e)}")
            else:
                st.error("❌ Please provide an API key in the sidebar")
    else:
        st.info("👆 Please upload resume files to get started")

if __name__ == "__main__":
    main()

