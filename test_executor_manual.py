"""Temporary manual check for the query executor."""

from app.query_executor import execute_query


database_path = "data/database.db"
sql = "SELECT name, city FROM customers;"


def main() -> None:
    """Execute a simple read-only query and print its result details."""
    result = execute_query(database_path, sql)
    print("Query executed successfully.")
    print(result)
    print(f"Rows returned: {len(result)}")
    print(f"Column names: {list(result.columns)}")


if __name__ == "__main__":
    main()
