"""Temporary manual check for the core Natural Language to SQL pipeline."""

from app.database import get_schema
from app.query_executor import execute_query
from app.sql_generator import generate_sql
from app.sql_validator import validate_sql


def main() -> None:
    """Run schema discovery, generation, validation, and query execution."""
    database_path = "data/database.db"
    question = "Show me the top 5 customers by total spending."

    try:
        schema = get_schema(database_path)
        generated_sql = generate_sql(question, schema)
        print(f"Generated SQL:\n{generated_sql}")

        validated_sql = validate_sql(generated_sql)
        print(f"Validated SQL:\n{validated_sql}")

        result = execute_query(database_path, validated_sql)
        print("Resulting DataFrame:")
        print(result)
        print(f"Rows returned: {len(result)}")
    except Exception as error:
        raise SystemExit(f"End-to-end pipeline failed: {error}") from error


if __name__ == "__main__":
    main()
