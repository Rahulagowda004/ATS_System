import pandas as pd

# Create a template DataFrame with the required columns
columns = [
    "Candidate Name",
    "Core Experience: 6–10 years in Legal Ops / IP / Startup-facing roles",
    "Core Experience: Patent filing coordination (India, PCT, USPTO, EPO)",
    "Core Experience: Drafting & enforcing contracts (NDAs, MSAs, investor agreements)",
    "Specialized Knowledge: Indian + International Patent Law & PCT process",
    "Specialized Knowledge: Fundraising legalities (SAFE/convertible notes, investor term sheets)",
    "Skills: Legal drafting, research & litigation support",
    "Skills: Organizational & multitasking (repositories, audit-ready records, multiple priorities)",
    "Cultural Fit: Worked closely with Founders / CXOs",
    "Cultural Fit: Confidentiality, accuracy, maturity",
    "Cultural Fit: Balancing risk governance with innovation speed",
    "Education: LLB/LLM or paralegal/legal qualification",
    "Education: Certifications, memberships, publications in IP/Patent Law",
    "Bonus: Prior work with VC/PE portfolio companies / tech startups",
    "Bonus: International exposure (cross-border filings, global counsel coordination)",
    "Total Score",
    "recommendation",
    "justification"
]

# Create an empty DataFrame with these columns
df = pd.DataFrame(columns=columns)

# Save to Excel
df.to_excel("template.xlsx", index=False)