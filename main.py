from typing import Literal
from pydantic import BaseModel, Field
import os
import pandas as pd
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from PyPDF2 import PdfReader
from docx import Document

class JobRequirements(BaseModel):
    """
    Extracted key requirements from job description to reduce token usage.
    """
    key_skills: list[str] = Field(..., description="List of key technical and soft skills required")
    experience_requirements: str = Field(..., description="Experience requirements and years needed")
    role_responsibilities: str = Field(..., description="Main responsibilities and duties")
    qualifications: str = Field(..., description="Educational and certification requirements")

class ResumeEvaluation(BaseModel):
    """
    Output class for a resume evaluation based on job requirements.
    """
    name: str = Field(..., description="The name of the candidate whose resume was evaluated.")
    contact_number: str = Field(..., description="The contact number of the candidate.")
    email: str = Field(..., description="The email address of the candidate.")
    experience_score: int = Field(..., ge=0, le=10, description="Score the total years of relevant experience out of 10.")
    skills_score: int = Field(..., ge=0, le=10, description="Skills match score out of 10 based on job requirements.")
    recommendation: Literal["Strongly Recommended", "Recommended", "Consider", "Not Suitable"] = Field(..., description="The final recommendation based on the evaluation.")

class ResumeEvaluator:
    def __init__(self, api_key=None):
        load_dotenv()
        self.model = AzureChatOpenAI(
            azure_endpoint="https://aixqp.openai.azure.com/",
            azure_deployment="gpt-4.1",
            api_version="2025-01-01-preview",
            api_key=api_key or os.getenv("AZURE_OPENAI_API_KEY")
        )
        
        # Prompt for extracting job requirements (used once)
        self.job_analysis_prompt = PromptTemplate(
            input_variables=["job_description"],
            template="""
            Analyze the following job description and extract the key requirements for efficient resume evaluation.

            Job Description:
            {job_description}

            Extract and summarize:
            1. Key skills (both technical and soft skills)
            2. Experience requirements (years and type)
            3. Main role responsibilities
            4. Educational/certification qualifications

            Focus on the most important requirements that would be used to evaluate candidates.
            """
        )
        
        # Efficient prompt for resume evaluation (reuses extracted requirements)
        self.evaluation_prompt = PromptTemplate(
            input_variables=["key_skills", "experience_requirements", "role_responsibilities", "qualifications", "resume_text"],
            template="""
            You are an expert HR recruiter. Evaluate this resume against the extracted job requirements.

            KEY SKILLS REQUIRED: {key_skills}
            EXPERIENCE REQUIREMENTS: {experience_requirements}
            ROLE RESPONSIBILITIES: {role_responsibilities}
            QUALIFICATIONS: {qualifications}

            Resume to Evaluate:
            {resume_text}

            Instructions:
            1. Extract candidate's name, phone number, and email from the resume
            2. Score relevant experience (0-10) based on years and type matching requirements
            3. Score skills match (0-10) based on how well candidate's skills align with required skills
            4. Provide recommendation using total score (experience + skills):
               - 16-20: Strongly Recommended
               - 11-15: Recommended  
               - 6-10: Consider
               - 0-5: Not Suitable

            Be objective and base scores on concrete evidence from the resume.
            If contact info is not found, use "Not Provided".
            """
        )
        
        self.job_analyzer = self.model.with_structured_output(JobRequirements)
        self.resume_evaluator = self.model.with_structured_output(ResumeEvaluation)
        
        self.job_analysis_chain = self.job_analysis_prompt | self.job_analyzer
        self.evaluation_chain = self.evaluation_prompt | self.resume_evaluator

    def extract_text(self, file_path: str) -> str:
        """Extract text from PDF or DOCX files"""
        text = ""
        try:
            if file_path.lower().endswith('.pdf'):
                reader = PdfReader(file_path)
                for page in reader.pages:
                    text += page.extract_text() or ""
            elif file_path.lower().endswith(('.docx', '.doc')):
                doc = Document(file_path)
                for para in doc.paragraphs:
                    text += para.text + "\n"
        except Exception as e:
            print(f"Error extracting text from {file_path}: {str(e)}")
        return text

    def extract_job_requirements(self, job_description: str) -> JobRequirements:
        """Extract key requirements from job description once"""
        response = self.job_analysis_chain.invoke({"job_description": job_description})
        return response

    def evaluate_resume(self, job_requirements: JobRequirements, resume_text: str):
        """Evaluate a single resume against the extracted job requirements"""
        response = self.evaluation_chain.invoke({
            "key_skills": ", ".join(job_requirements.key_skills),
            "experience_requirements": job_requirements.experience_requirements,
            "role_responsibilities": job_requirements.role_responsibilities,
            "qualifications": job_requirements.qualifications,
            "resume_text": resume_text
        })
        return response.model_dump()

    def process_folder(self, folder_path: str, job_description_path: str, output_path: str = "resume_evaluation_results.xlsx"):
        """Process all resumes in a folder against a job description"""
        # Extract job description text
        job_description = self.extract_text(job_description_path)
        if not job_description:
            raise ValueError("Could not extract text from job description file")

        print("Extracting job requirements...")
        # Extract job requirements ONCE (saves tokens)
        job_requirements = self.extract_job_requirements(job_description)
        print(f"Key skills identified: {', '.join(job_requirements.key_skills[:5])}...")

        results = []
        resume_files = []
        
        # Get all resume files from the folder
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.pdf', '.doc', '.docx')):
                resume_files.append(filename)

        print(f"Found {len(resume_files)} resume files to process")

        for i, filename in enumerate(resume_files, 1):
            file_path = os.path.join(folder_path, filename)
            try:
                print(f"Processing {i}/{len(resume_files)}: {filename}")
                resume_text = self.extract_text(file_path)
                
                if not resume_text.strip():
                    print(f"Warning: No text extracted from {filename}")
                    results.append({
                        "Name": filename,
                        "Contact Number": "Not Provided",
                        "Email": "Not Provided",
                        "Experience Score": 0,
                        "Skills Score": 0,
                        "Recommendation": "Not Suitable",
                        "Error": "Could not extract text"
                    })
                    continue

                # Evaluate using extracted requirements (much more efficient)
                evaluation = self.evaluate_resume(job_requirements, resume_text)
                
                results.append({
                    "Name": evaluation.get("name", filename),
                    "Contact Number": evaluation.get("contact_number", "Not Provided"),
                    "Email": evaluation.get("email", "Not Provided"),
                    "Experience Score": evaluation.get("experience_score", 0),
                    "Skills Score": evaluation.get("skills_score", 0),
                    "Recommendation": evaluation.get("recommendation", "Not Suitable")
                })
                
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                results.append({
                    "Name": filename,
                    "Contact Number": "Not Provided",
                    "Email": "Not Provided", 
                    "Experience Score": 0,
                    "Skills Score": 0,
                    "Recommendation": "Not Suitable",
                    "Error": str(e)
                })

        # Create DataFrame and save to Excel
        df = pd.DataFrame(results)
        df.to_excel(output_path, index=False)
        print(f"Results saved to {output_path}")
        return df