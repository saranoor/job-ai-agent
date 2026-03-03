import os
from typing import Optional, List

from docx import Document  # pip install python-docx
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from dotenv import load_dotenv
from serpapi import GoogleSearch


load_dotenv()


class JobMatch(BaseModel):
    title: Optional[str]
    company: Optional[str]
    location: Optional[str]
    salary: Optional[str] = None
    reason: str


class JobReport(BaseModel):
    top_skills: List[str]
    summary: str
    best_job: Optional[JobMatch]
    other_good_jobs: List[JobMatch] = Field(default_factory=list)

class MissionState(BaseModel):
    sent_count: int = 0
    checked_jobs: list[str] = Field(default_factory=list)

provider = AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY"))

model = AnthropicModel(
    "claude-haiku-4-5",
)

job_agent = Agent(
    model,
    output_type=JobReport,
    system_prompt=(
        "You are a job market analyst and career coach.\n"
        "You will receive:\n"
        "1) The full text of a candidate's resume.\n"
        "2) Their target role and location.\n"
        "3) A tool `search_jobs` that can search live job listings.\n\n"
        "Your tasks:\n"
        "- Infer the candidate's top skills from the resume.\n"
        "- Use `search_jobs` with an appropriate query to find relevant roles.\n"
        "- Select the SINGLE best-matching job for this candidate and explain why.\n"
        "- Send a WhatsApp message to the user about the best job match using the `send_whatsapp_alert` tool.\n"
        # "- Optionally list a few other strong matches.\n"
        "Return your answer in the `JobReport` structure."
    ),
)


@job_agent.tool_plain
def search_jobs(query: str) -> list[dict]:
    """
    Search for job listings on Google.

    Args:
        query: The job title and location (e.g., 'Python Developer in New York')
    """
    search = GoogleSearch(
        {
            "engine": "google_jobs",
            "q": query,
            "api_key": os.getenv("SERPAPI_KEY"),
        }
    )
    results = search.get_dict()

    raw_jobs = results.get("jobs_results", [])

    clean_jobs: list[dict] = []
    for job in raw_jobs[:20]:  # Limit to 20
        clean_jobs.append(
            {
                "title": job.get("title"),
                "company": job.get("company_name"),
                "location": job.get("location"),
                "description": job.get("description", "")[:800],
                "salary": job.get("detected_extensions", {}).get("salary"),
            }
        )
    return clean_jobs


@job_agent.tool_plain
def send_whatsapp_alert(job_title: str, company: str, reason: str) -> str:
    """
    Sends a WhatsApp message to the user about a high-match job.
    """
    print(f"--- AGENT ACTION: Sending {job_title} to WhatsApp... ---")
    return "SUCCESS: Message sent to user."

def extract_resume_text(docx_path: str) -> str:
    """Read a .docx resume file and return plain text."""
    document = Document(docx_path)
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def main() -> None:
    resume_path = input(
        "Enter the path to your resume (.docx), e.g. resume.docx: "
    ).strip('"').strip()
    if not os.path.isfile(resume_path):
        raise FileNotFoundError(f"Resume file not found: {resume_path}")

    target_role = input(
        "What role are you targeting? (e.g. Data Scientist, Backend Engineer): "
    ).strip()
    location = input(
        "Where are you looking for jobs? (e.g. Texas, Remote, London): "
    ).strip()

    resume_text = extract_resume_text(resume_path)

    prompt = (
        "You are matching this candidate to jobs.\n\n"
        f"Candidate resume:\n{resume_text}\n\n"
        f"Target role: {target_role}\n"
        f"Location preference: {location}\n\n"
        "1) Infer their top skills from the resume.\n"
        "2) Use `search_jobs` to find relevant roles.\n"
        "3) Choose the SINGLE best job match and explain why it fits.\n"
        "4) Optionally add a few other strong matches.\n"
    )

    result = job_agent.run_sync(prompt)
    report: JobReport = result.output

    print("\n--------------------------------")
    print("Top skills inferred from your resume:")
    for skill in report.top_skills:
        print(f"- {skill}")

    print("\nSummary:")
    print(report.summary)

    if report.best_job:
        print("\nBest matching job for you:")
        print(f"- Title: {report.best_job.title}")
        print(f"- Company: {report.best_job.company}")
        print(f"- Location: {report.best_job.location}")
        if report.best_job.salary:
            print(f"- Salary: {report.best_job.salary}")
        print(f"- Why this fits you: {report.best_job.reason}")

    if report.other_good_jobs:
        print("\nOther good matches:")
        for job in report.other_good_jobs:
            print(
                f"- {job.title} at {job.company} ({job.location})"
                f"{' | ' + job.salary if job.salary else ''}"
            )


if __name__ == "__main__":
    main()