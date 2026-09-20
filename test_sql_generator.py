"""Temporary manual check for natural-language SQL generation."""

from pathlib import Path

from app.database import get_schema
from app.sql_generator import generate_sql


question = "Show me the top 5 customers by total spending."
database_path = Path(__file__).resolve().parent / "data" / "database.db"
schema = get_schema(str(database_path))
generated_sql = generate_sql(question, schema)

print(f"Question: {question}")
print(f"Generated SQL:\n{generated_sql}")
