"""Explain validated SQL and its results with deterministic local logic.

This module does not generate, validate, or execute SQL. It turns an already
validated SQL query and its returned rows into a short, user-friendly
explanation without calling an external API.
"""

import re
from typing import Any


def _humanize_name(name: str) -> str:
	"""Turn a database column name into readable words."""
	return name.replace("_", " ").strip()


def _format_value(value: Any) -> str:
	"""Format common result values without inventing additional information."""
	if isinstance(value, float):
		return f"{value:,.2f}"
	if isinstance(value, int):
		return f"{value:,}"
	return str(value)


def _find_metric_column(results: list[dict]) -> str | None:
	"""Find a useful numeric result column for a concise summary."""
	for key, value in results[0].items():
		if isinstance(value, (int, float)) and not key.lower().endswith("id"):
			return key
	return None


def _find_label_column(results: list[dict], metric_column: str | None) -> str | None:
	"""Find a readable label column, preferring names over identifiers."""
	preferred_names = ("name", "product_name", "category", "city", "label")
	for preferred_name in preferred_names:
		for key, value in results[0].items():
			if key.lower() == preferred_name and isinstance(value, str):
				return key

	for key, value in results[0].items():
		if key != metric_column and isinstance(value, str):
			return key
	return None


def _describe_query(sql: str) -> str:
	"""Describe common SQL patterns as one beginner-friendly explanation."""
	lower_sql = sql.lower()
	from_match = re.search(r"\bfrom\s+([\w\"]+)", lower_sql)
	tables = [from_match.group(1).strip('"') if from_match else "the data"]
	tables.extend(match.strip('"') for match in re.findall(r"\bjoin\s+([\w\"]+)", lower_sql))

	if len(tables) > 1:
		data_phrase = f"{tables[0]} and their related {', '.join(tables[1:])}"
	else:
		data_phrase = tables[0]

	parts = [f"The query looks at {data_phrase}"]
	if re.search(r"\bjoin\b", lower_sql):
		parts[-1] += " and connects related records"

	aggregates = []
	for function_name, wording in (
		("sum", "adds up the relevant amounts"),
		("count", "counts the matching records"),
		("avg", "calculates an average"),
		("min", "finds the lowest value"),
		("max", "finds the highest value"),
	):
		if re.search(rf"\b{function_name}\s*\(", lower_sql):
			aggregates.append(wording)
	if aggregates:
		parts.append(" and ".join(aggregates))

	if re.search(r"\bwhere\b", lower_sql):
		parts.append("keeps only records matching the requested conditions")
	if re.search(r"\bgroup\s+by\b", lower_sql):
		parts.append("organizes the calculation for each group")
	if re.search(r"\border\s+by\b", lower_sql):
		order_match = re.search(r"\border\s+by\s+([\w\"]+)(?:\s+(asc|desc))?", lower_sql)
		if order_match and order_match.group(2) == "desc":
			parts.append("arranges the results from highest to lowest")
		elif order_match and order_match.group(2) == "asc":
			parts.append("arranges the results from lowest to highest")
		else:
			parts.append("arranges the results in the requested order")

	limit_match = re.search(r"\blimit\s+(\d+)", lower_sql)
	if limit_match:
		parts.append(f"shows only the first {limit_match.group(1)} results")

	if len(parts) == 1:
		return f"{parts[0]}."
	return f"{parts[0]}, " + ", ".join(parts[1:]) + "."


def _describe_results(results: list[dict]) -> str:
	"""Summarize useful values from the returned rows without dumping them."""
	metric_column = _find_metric_column(results)
	label_column = _find_label_column(results, metric_column)
	if metric_column and label_column:
		metric_name = _humanize_name(metric_column)
		first = results[0]
		first_text = f"{first[label_column]} has the highest {metric_name} at {_format_value(first[metric_column])}"
		if len(results) > 1:
			second = results[1]
			return f"{first_text}, followed by {second[label_column]} at {_format_value(second[metric_column])}."
		return f"{first_text}."

	if len(results) == 1:
		values = ", ".join(
			f"{_humanize_name(key)}: {_format_value(value)}"
			for key, value in results[0].items()
		)
		return f"The query returned one matching record with {values}."

	return f"The query returned {len(results)} matching records."


def generate_explanation(question: str, sql: str, results: list[dict]) -> str:
	"""Return a short local explanation of a validated SQL query and its rows."""
	if not isinstance(question, str) or not question.strip():
		raise ValueError("The question cannot be empty.")
	if not isinstance(sql, str) or not sql.strip():
		raise ValueError("The SQL query cannot be empty.")
	if not isinstance(results, list):
		raise ValueError("Query results must be provided as a list.")

	if not results:
		return (
			"How this query works: The query ran successfully, but it did not find any matching records.\n\n"
			"What the results tell us: No results were returned."
		)

	return (
		f"How this query works: {_describe_query(sql)}\n\n"
		f"What the results tell us: {_describe_results(results)}"
	)