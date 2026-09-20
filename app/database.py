"""Helpers for connecting to and inspecting SQLite databases."""

from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine


def validate_database_path(database_path: str) -> Path:
	"""Validate a SQLite database path and return it as a ``Path``.

	Args:
		database_path: Path to an existing SQLite database file.

	Raises:
		ValueError: If the path does not exist or does not point to a file.
	"""
	path = Path(database_path)

	if not path.exists():
		raise ValueError(f"Database path does not exist: {database_path}")
	if not path.is_file():
		raise ValueError(f"Database path is not a file: {database_path}")

	return path


def get_engine(database_path: str) -> Engine:
	"""Create a SQLAlchemy engine for an existing SQLite database file."""
	path = validate_database_path(database_path).resolve()
	return create_engine(f"sqlite:///{path.as_posix()}")


def get_schema(database_path: str) -> dict[str, dict[str, list[dict[str, str]]]]:
	"""Inspect a SQLite database and return its tables and columns.

	The returned dictionaries contain only JSON-serializable values. Table
	names and column names come directly from SQLAlchemy's database inspector.
	"""
	engine = get_engine(database_path)
	try:
		inspector = inspect(engine)
		schema: dict[str, dict[str, list[dict[str, str]]]] = {}

		for table_name in inspector.get_table_names():
			columns = [
				{
					"name": column["name"],
					"type": str(column["type"]).upper(),
				}
				for column in inspector.get_columns(table_name)
			]
			schema[table_name] = {"columns": columns}

		return schema
	finally:
		engine.dispose()
