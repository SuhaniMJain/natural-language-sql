"""Defense-in-depth MVP validation for AI-generated read-only SQL.

This validator is not a perfect security boundary. Production systems should
also use database permissions and read-only controls before executing SQL.
"""

import re


_DANGEROUS_KEYWORDS = (
	"INSERT",
	"UPDATE",
	"DELETE",
	"DROP",
	"ALTER",
	"CREATE",
	"TRUNCATE",
	"PRAGMA",
	"ATTACH",
	"DETACH",
	"REPLACE",
	"VACUUM",
	"REINDEX",
)
_DANGEROUS_PATTERN = re.compile(
	r"\b(?:" + "|".join(_DANGEROUS_KEYWORDS) + r")\b",
	re.IGNORECASE,
)
_SELECT_PATTERN = re.compile(r"^SELECT\b", re.IGNORECASE)


def _remove_comments(sql: str) -> str:
	"""Remove SQL comments without changing quoted strings or identifiers."""
	result: list[str] = []
	quote: str | None = None
	index = 0

	while index < len(sql):
		character = sql[index]

		if quote:
			result.append(character)
			if character == quote:
				if index + 1 < len(sql) and sql[index + 1] == quote:
					result.append(sql[index + 1])
					index += 1
				else:
					quote = None
			index += 1
			continue

		if character in ("'", '"', "`"):
			quote = character
			result.append(character)
			index += 1
			continue

		if character == "[":
			quote = "]"
			result.append(character)
			index += 1
			continue

		if sql.startswith("--", index):
			result.append(" ")
			index += 2
			while index < len(sql) and sql[index] not in "\r\n":
				index += 1
			continue

		if sql.startswith("/*", index):
			end = sql.find("*/", index + 2)
			if end == -1:
				raise ValueError("SQL contains an unterminated block comment.")
			result.append(" ")
			index = end + 2
			continue

		result.append(character)
		index += 1

	return "".join(result)


def _mask_quoted_text(sql: str) -> str:
	"""Replace quoted contents with spaces for structural SQL checks."""
	result: list[str] = []
	quote: str | None = None

	for character in sql:
		if quote:
			if character == quote:
				result.append(character)
				quote = None
			else:
				result.append(" ")
			continue

		if character in ("'", '"', "`"):
			quote = character
			result.append(character)
		elif character == "[":
			quote = "]"
			result.append(character)
		else:
			result.append(character)

	return "".join(result)


def validate_sql(sql: str) -> str:
	"""Validate and return one cleaned, read-only SELECT query.

	Comments are removed before validation, and quoted values are ignored when
	checking statement separators and dangerous keywords. This does not execute
	the SQL or connect to a database.

	Raises:
		ValueError: If the SQL is empty, not a SELECT, unsafe, or contains more
			than one statement.
	"""
	if not isinstance(sql, str) or not sql.strip():
		raise ValueError("SQL cannot be empty.")

	cleaned_sql = _remove_comments(sql).strip()
	if not cleaned_sql:
		raise ValueError("SQL cannot contain only comments.")

	structural_sql = _mask_quoted_text(cleaned_sql)
	semicolon_positions = [
		index for index, character in enumerate(structural_sql) if character == ";"
	]
	if len(semicolon_positions) > 1:
		raise ValueError("Only one SQL statement is allowed.")
	if semicolon_positions:
		semicolon_index = semicolon_positions[0]
		if structural_sql[semicolon_index + 1 :].strip():
			raise ValueError("Only a single trailing semicolon is allowed.")
		cleaned_sql = cleaned_sql[:semicolon_index].rstrip()
		structural_sql = structural_sql[:semicolon_index].rstrip()

	if not _SELECT_PATTERN.match(structural_sql):
		raise ValueError("Only read-only SELECT queries are allowed.")
	if _DANGEROUS_PATTERN.search(structural_sql):
		raise ValueError("SQL contains a prohibited database-modifying keyword.")

	return cleaned_sql
