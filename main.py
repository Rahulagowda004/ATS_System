from typing import Literal
from pydantic import BaseModel, Field
import os
import pandas as pd
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from PyPDF2 import PdfReader
from docx import Document
import re

class ResumeEvaluation(BaseModel):
    """
    Output class for a resume evaluation based on a job description.
    """
    name: str = Field(..., description="The name of the candidate whose resume was evaluated.")
    contact_number: int = Field(..., description="The contact number of the candidate.")
    email: str = Field(..., description="The email address of the candidate.")
    experience_score: int = Field(..., ge=0, le=10, description="Score the total years of relevant experience.")
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
        self.prompt = PromptTemplate(
            input_variables=["job_description", "resume_text"],
            template="""
            You are an expert HR recruiter. Evaluate the following resume against the provided job description.

            Job Description:
            {job_description}

            Resume to Evaluate:
            {resume_text}

            Instructions:
            1. Extract the candidate's name, contact number, and email from the resume
            2. Score the total years of relevant experience out of 10 based on the job requirements
            3. Score the skills match out of 10 based on how well the candidate's skills align with job requirements
            4. Provide a recommendation using this scoring guide:
            - 16-20: Strongly Recommended
            - 11-15: Recommended
            - 6-10: Consider
            - 0-5: Not Suitable

            Important Notes:
            - Focus only on relevant experience that matches the job requirements
            - Consider both technical and soft skills mentioned in the job description
            - Be objective and base scores on concrete evidence from the resume
            - If candidate name is not clear, use "Unknown Candidate"
            """
        )
        self.llm = self.model.with_structured_output(ResumeEvaluation)
        self.chain = self.prompt | self.llm

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

    def evaluate_resume(self, job_description: str, resume_text: str):
        """Evaluate a single resume against the job description"""
        response = self.chain.invoke({
            "job_description": job_description, 
            "resume_text": resume_text
        })
        return response.model_dump()

    def process_folder(self, folder_path: str, job_description_path: str, output_path: str = "resume_evaluation_results.xlsx"):
        """Process all resumes in a folder against a job description"""
        # Extract job description
        job_description = self.extract_text(job_description_path)
        if not job_description:
            raise ValueError("Could not extract text from job description file")

        results = []
        resume_files = []
        
        # Get all resume files from the folder
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.pdf', '.doc', '.docx')):
                resume_files.append(filename)

        print(f"Found {len(resume_files)} resume files to process")

        for filename in resume_files:
            file_path = os.path.join(folder_path, filename)
            try:
                print(f"Processing: {filename}")
                resume_text = self.extract_text(file_path)
                
                if not resume_text.strip():
                    print(f"Warning: No text extracted from {filename}")
                    results.append({
                        "Name": filename,
                        "Contact Number": None,
                        "Email": None,
                        "Score Experience": 0,
                        "Skills Score": 0,
                        "Recommendation": "Not Suitable",
                        "Error": "Could not extract text"
                    })
                    continue

                evaluation = self.evaluate_resume(job_description, resume_text)
                
                results.append({
                    "Name": evaluation.get("name", filename),
                    "Contact Number": evaluation.get("contact_number", None),
                    "Email": evaluation.get("email", None),
                    "Score Experience": evaluation.get("experience_score", 0),
                    "Skills Score": evaluation.get("skills_score", 0),
                    "Recommendation": evaluation.get("recommendation", "Not Suitable")
                })
                
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                results.append({
                    "Name": filename,
                    "Experience Years": 0,
                    "Skills Score": 0,
                    "Recommendation": "Not Suitable",
                    "Error": str(e)
                })

        # Create DataFrame and save to Excel
        df = pd.DataFrame(results)
        df.to_excel(output_path, index=False)
        print(f"Results saved to {output_path}")
        return df