import json
import os
from dotenv import load_dotenv
from groq import Groq
from models.schemas import ParsedJD
from prompts.prompts import JD_PARSER_PROMPT

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def parse_jd(jd_text: str) -> ParsedJD:
    prompt = JD_PARSER_PROMPT.format(jd_text=jd_text)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    data = json.loads(raw)
    return ParsedJD(**data)