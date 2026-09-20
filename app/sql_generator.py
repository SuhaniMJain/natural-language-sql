"""Generate SQLite queries from natural-language questions with Gemini."""

import json
import os

from dotenv import load_dotenv
from google import genai


GEMINI_MODEL = "gemini-3.6-flash"


def _clean_model_response(response_text: object) -> str:
	"""Return SQL text after removing whitespace and optional code fences."""
	if not isinstance(response_text, str):
		raise ValueError("Gemini returned a malformed response without SQL text.")

	sql = response_text.strip()
	if not sql:
		raise ValueError("Gemini returned an empty SQL response.")

	if sql.startswith("```"):
		lines = sql.splitlines()
		if len(lines) < 3 or lines[-1].strip() != "```":
			raise ValueError("Gemini returned malformed Markdown SQL code fences.")
		sql = "\n".join(lines[1:-1]).strip()
	elif "```" in sql:
		raise ValueError("Gemini returned malformed Markdown SQL code fences.")

	if not sql:
		raise ValueError("Gemini returned an empty SQL response.")

	return sql


def generate_sql(question: str, schema: dict) -> str:
	"""Generate one read-only SQLite query for a natural-language question.

	The schema is passed at runtime so the generator can work with each
	user's uploaded database instead of assuming a fixed demo schema. The
	generated SQL will still be validated later before it is executed.
	"""
	if not question.strip():
		raise ValueError("The question cannot be empty.")
	if not isinstance(schema, dict):
		raise ValueError("The database schema must be provided as a dictionary.")

	load_dotenv()
	api_key = os.getenv("GEMINI_API_KEY")
	if not api_key:
		raise ValueError("GEMINI_API_KEY is missing. Add it to your .env file.")

	try:
		schema_text = json.dumps(schema, indent=2, sort_keys=True)
	except (TypeError, ValueError) as error:
		raise ValueError("The database schema must be JSON-serializable.") from error

	prompt = f"""You convert natural-language questions into SQLite queries.

Database schema:
{schema_text}

User question:
{question.strip()}

Instructions:
- Generate SQLite-compatible SQL.
- Generate ONLY one read-only SELECT query.
- Use ONLY tables and columns present in the supplied schema.
- Never invent tables or columns.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, PRAGMA,
  ATTACH, DETACH, or any other database-modifying statement.
- Do not return explanations.
- Do not return Markdown code fences.
- Return only the SQL query.
"""

	try:
		client = genai.Client(api_key=api_key)
		interaction = client.interactions.create(
			model=GEMINI_MODEL,
			input=prompt,
		)
		response_text = interaction.output_text
	except Exception as error:
		raise RuntimeError(f"Gemini API request failed: {error}") from error

	return _clean_model_response(response_text)
