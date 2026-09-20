"""Execute already-validated read-only SQL queries against SQLite."""

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.database import validate_database_path


def _get_read_only_engine(database_path: Path) -> Engine:
	"""Create a SQLAlchemy engine that opens SQLite in read-only mode."""
	read_only_url = f"sqlite+pysqlite:///file:{database_path.as_posix()}?mode=ro&uri=true"
	return create_engine(read_only_url)


def execute_query(database_path: str, sql: str) -> pd.DataFrame:
	"""Execute an already-validated read-only query and return its DataFrame.

	The caller is responsible for validating the SQL with the application's
	SQL validator before calling this function. The SQLite connection is also
	opened in read-only mode so this function cannot modify the database.

	Raises:
		ValueError: If the database path or SQL query is empty or invalid.
		RuntimeError: If SQLite cannot execute the query.
	"""
	if not isinstance(sql, str) or not sql.strip():
		raise ValueError("SQL query cannot be empty.")

	path = validate_database_path(database_path).resolve()
	engine = _get_read_only_engine(path)

	try:
		with engine.connect() as connection:
			return pd.read_sql_query(text(sql), connection)
	except (SQLAlchemyError, pd.errors.DatabaseError) as error:
		error_message = str(error)
		lower_message = error_message.lower()
		if "no such table" in lower_message:
			raise RuntimeError(f"Database table not found: {error_message}") from error
		if "no such column" in lower_message:
			raise RuntimeError(f"Database column not found: {error_message}") from error
		if "syntax error" in lower_message:
			raise ValueError(f"Invalid SQL query: {error_message}") from error
		raise RuntimeError(f"Database query execution failed: {error_message}") from error
	finally:
		engine.dispose()
