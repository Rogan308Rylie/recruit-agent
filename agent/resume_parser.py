import json
import os
import pdfplumber
from docx import Document
from dotenv import load_dotenv
from groq import Groq
from models.schemas import ParsedResume
from prompts.prompts import RESUME_PARSER_PROMPT, clean_llm_response

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def parse_resume(file_path: str) -> ParsedResume:
    if file_path.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif file_path.endswith(".docx"):
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format. Use PDF or DOCX.")

    text = text.replace("{", "{{").replace("}", "}}")

    prompt = RESUME_PARSER_PROMPT.format(resume_text=text)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    raw = clean_llm_response(response.choices[0].message.content)

    data = json.loads(raw)
    return ParsedResume(**data)