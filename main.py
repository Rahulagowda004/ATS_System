from typing import Literal
from pydantic import BaseModel, Field
import os
import pandas as pd
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from PyPDF2 import PdfReader
from docx import Document

class ResumeEvaluation(BaseModel):
    """
    Output class for a resume evaluation based on a specific scoring rubric.
    """
    name: str = Field(..., description="The name of the candidate whose resume was evaluated.")
    core_experience_legal_ops: int = Field(..., ge=0, le=10, description="Points for 6-10 years of experience in Legal Ops/IP/Startup-facing roles (max 10).")
    core_experience_patent_filing: int = Field(..., ge=0, le=10, description="Points for experience with patent filing coordination (India, PCT, USPTO, EPO) (max 10).")
    core_experience_contracts: int = Field(..., ge=0, le=10, description="Points for experience drafting and enforcing contracts (NDAs, MSAs, investor agreements) (max 10).")
    specialized_knowledge_patent_law: int = Field(..., ge=0, le=10, description="Points for knowledge of Indian + International Patent Law & PCT process (max 10).")
    specialized_knowledge_fundraising: int = Field(..., ge=0, le=10, description="Points for knowledge of fundraising legalities (SAFE/convertible notes, investor term sheets) (max 10).")
    skills_legal_drafting: int = Field(..., ge=0, le=10, description="Points for legal drafting, research, and litigation support skills (max 10).")
    skills_organizational: int = Field(..., ge=0, le=10, description="Points for organizational and multitasking skills (repositories, audit-ready records) (max 10).")
    cultural_fit_founder: int = Field(..., ge=0, le=5, description="Points for working closely with Founders/CXOs (max 5).")
    cultural_fit_confidentiality: int = Field(..., ge=0, le=5, description="Points for confidentiality, accuracy, and maturity (max 5).")
    cultural_fit_balance: int = Field(..., ge=0, le=5, description="Points for balancing risk governance with innovation speed (max 5).")
    education_degree: int = Field(..., ge=0, le=5, description="Points for LLB/LLM or paralegal/legal qualification (max 5).")
    education_certifications: int = Field(..., ge=0, le=5, description="Points for certifications, memberships, and publications in IP/Patent Law (max 5).")
    bonus_prior_work: int = Field(..., ge=0, le=3, description="Bonus points for prior work with VC/PE portfolio companies/tech startups (max 3).")
    bonus_international_exposure: int = Field(..., ge=0, le=2, description="Bonus points for international exposure (cross-border filings) (max 2).")
    total_score: int = Field(..., ge=0, le=100, description="The calculated total score for the candidate.")
    recommendation: Literal["Strongly Recommended for Interview", "Recommended for Interview", "Consider with Caution", "Not Suitable"] = Field(..., description="The final recommendation based on the total score and scoring key.")
    justification: str = Field(..., description="A brief justification for the scores and final recommendation.")

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
            input_variables=["resume_text"],
            template="""
You are an expert in legal operations and intellectual property. Evaluate the following resume for a Legal Ops/IP/Startup-facing role using the criteria below. Assign points for each criterion and provide a total score and recommendation as per the scoring key.

Job Description:
Title: Legal & IP Operations Executive – The Legal Architect Protecting iTCart’s AI Legacy, Patents, and Global Expansion
Department: Office of the Founder | Legal, IP & Risk Governance
Employment Type: Full-Time | Strategic Legal Operations | Confidential Trust Role

About the Role
This is not a law firm-style desk job. This is a mission-critical execution seat at the center of one of India’s most important emerging deep-tech companies.
You will serve as the Legal & IP Operations Executive to the Founder, with end-to-end ownership over everything that legally protects iTCart’s inventions, operations, partnerships, investments, and future.
Your primary mission is to secure and defend the global patent rights of AiXHub, while enabling high-speed legal alignment across PoVs, NDAs, investor engagements, channel alliances, and public messaging.
You will act as the single point of trust between iTCart’s legal strategy and business execution — ensuring zero slippage, full compliance, and forward-leaning IP defensibility.

Key Responsibilities
Patent & IP Filing Coordination
Liaise with IPExcel and global attorneys to file, track, and enforce patent applications (India, PCT, USPTO, EPO, etc.).
Maintain all filing artifacts, diagrams, inventor disclosures, claim updates, and final applications in audit-ready format.
Assist in IP strategy reviews and prepare defenses against prior art or competitive infringements.
NDA, MSA & Legal Operations
Draft, review, and enforce NDAs, MSAs, partnership contracts, and investor terms with speed and risk clarity.
Track all agreements across PoV clients, partners, employees, and contractors in a secure legal repository.
Identify legal gaps, process weaknesses, or misaligned redlines that could harm iTCart’s defensibility.
Litigation & Legal Research Support
Support active and emerging legal strategies such as Abacus’s legal dispute, competitive tracking, and evidentiary packaging.
Collaborate with external counsel and Founder to prepare briefs, summaries, and legal positions when needed.
Investor-Ready Legal Enablement
Build and maintain a “Legal Evidence Room” with pre-cleared:
Patent IP filings
NDA enforcement logs
Company-level compliance trackers
Cap table, ESOP, employment agreement alignment
Support legal sections of pitch decks, diligence documents, and BOD briefings.
Legal Risk Governance & Policy Drafting
Assist in drafting internal IP policies, AI compliance guidelines, contributor terms, and product disclaimers.
Partner with tech and GTM leads to ensure legal readiness of external materials: whitepapers, decks, investor FAQs, etc.

Who You Are
6–10 years of experience in startup legal operations, IP law coordination, or founder-facing legal roles.
Understands the urgency and nuance of working directly with a CTO/Founder on sensitive and high-velocity matters.
Operates with maturity, confidentiality, and fierce accuracy.
Able to move between patent filings, redlines, and investor clauses without missing a beat.

Preferred Qualifications
Familiarity with Indian and international patent law and PCT process.
Experience with investor term sheets, SAFE/convertible notes, or fundraising rounds.
Prior work with startups, VC/PE portfolio companies, or tech-focused legal teams.
Legal education or paralegal qualification preferred, but not mandatory if practical exposure is strong.
Cultural DNA We Look For
Surgical with language, but adaptive with business reality.
Treats confidentiality as sacred.
Enjoys working closely with a Founder on legal and strategic control of IP.
Relentless about reducing risk — but not at the cost of innovation speed.
Believes the legal arm of a tech company is not a blocker, but a defender of vision.
Perks & Pathways
Direct access to the Founder, IP attorneys, investor conversations, and board preparation.
Career path toward Head of Legal / Director of IP Ops as iTCart scales globally.
Personal mentorship in AI+IP law strategy, litigation exposure, and enterprise compliance structuring.

---

Criteria (Max Points):
- Core Experience: Legal Ops/IP/startup-facing roles (6–10 years) (10)
- Core Experience: Patent filing coordination (India, PCT, USPTO, EPO) (10)
- Core Experience: Drafting & enforcing contracts (NDAs, MSAs, investor agreements) (10)
- Specialized Knowledge: Indian + International Patent Law & PCT process (10)
- Specialized Knowledge: Fundraising legalities (SAFE/convertible notes, investor term sheets) (10)
- Skills: Legal drafting, research & litigation support (10)
- Skills: Organizational & multitasking (repositories, audit-ready records, multiple priorities) (10)
- Cultural Fit: Worked closely with Founders / CXOs (5)
- Cultural Fit: Confidentiality, accuracy, maturity (5)
- Cultural Fit: Balancing risk governance with innovation speed (5)
- Education: LLB/LLM or paralegal/legal qualification (5)
- Education: Certifications, memberships, publications in IP/Patent Law (5)
- Bonus: Prior work with VC/PE portfolio companies / tech startups (3)
- Bonus: International exposure (cross-border filings, global counsel coordination) (2)

Scoring Key:
- 85–100: Strongly Recommended for Interview
- 70–84: Recommended for Interview
- 50–69: Consider with Caution
- <50: Not Suitable

---

Important Instructions:
- Do **not penalize for formatting or writing style** of the resume; evaluate only the content relevance.  
- If information is missing, assume 0 points for that criterion. Do not speculate or infer beyond what is explicitly stated.  
- Provide partial points only when there is clear supporting evidence.  
- Output must be in a structured table with columns: *Criterion | Max Points | Score | Notes*.  
- Conclude with:  
   1. Total Score  
   2. Recommendation (per scoring key)  
   3. Brief justification for the score  

---

Resume for Evaluation:
{resume_text}
"""
        )
        self.llm = self.model.with_structured_output(ResumeEvaluation)
        self.chain = self.prompt | self.llm
        self.column_map = {
            "Candidate Name": "name",
            "Core Experience: 6–10 years in Legal Ops / IP / Startup-facing roles": "core_experience_legal_ops",
            "Core Experience: Patent filing coordination (India, PCT, USPTO, EPO)": "core_experience_patent_filing",
            "Core Experience: Drafting & enforcing contracts (NDAs, MSAs, investor agreements)": "core_experience_contracts",
            "Specialized Knowledge: Indian + International Patent Law & PCT process": "specialized_knowledge_patent_law",
            "Specialized Knowledge: Fundraising legalities (SAFE/convertible notes, investor term sheets)": "specialized_knowledge_fundraising",
            "Skills: Legal drafting, research & litigation support": "skills_legal_drafting",
            "Skills: Organizational & multitasking (repositories, audit-ready records, multiple priorities)": "skills_organizational",
            "Cultural Fit: Worked closely with Founders / CXOs": "cultural_fit_founder",
            "Cultural Fit: Confidentiality, accuracy, maturity": "cultural_fit_confidentiality",
            "Cultural Fit: Balancing risk governance with innovation speed": "cultural_fit_balance",
            "Education: LLB/LLM or paralegal/legal qualification": "education_degree",
            "Education: Certifications, memberships, publications in IP/Patent Law": "education_certifications",
            "Bonus: Prior work with VC/PE portfolio companies / tech startups": "bonus_prior_work",
            "Bonus: International exposure (cross-border filings, global counsel coordination)": "bonus_international_exposure",
            "Total Score": "total_score",
            "recommendation": "recommendation",
            "justification": "justification"
        }

    def extract_text(self, file_path: str) -> str:
        text = ""
        if file_path.lower().endswith('.pdf'):
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() or ""
        elif file_path.lower().endswith('.docx'):
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        return text

    def evaluate_resume(self, resume_text: str):
        response = self.chain.invoke({"resume_text": resume_text})
        return response.model_dump()

    def process_directory(self, dir_path: str, template_path: str = "template.xlsx", output_path: str = "ATS_details.xlsx"):
        mapped_results = []
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            try:
                text = self.extract_text(file_path)
                if not text:
                    continue
                response_dict = self.evaluate_resume(text)
                df = pd.read_excel(template_path)
                for col in df.columns:
                    key = self.column_map.get(col)
                    if key and key in response_dict:
                        df.at[0, col] = response_dict[key]
                df["name"] = filename  # Optionally set filename as candidate name if needed
                mapped_results.append(df.iloc[0].to_dict())
            except Exception as e:
                mapped_results.append({"name": filename, "error": str(e)})
        result_df = pd.DataFrame(mapped_results)
        result_df.to_excel(output_path, index=False)
        return result_df


