"""FastAPI endpoints for the Natural Language to SQL assistant."""

from pathlib import Path
import shutil
import tempfile
from typing import Any
from uuid import uuid4

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from app.database import get_schema
from app.explanation import generate_explanation
from app.query_executor import execute_query
from app.sql_generator import generate_sql
from app.sql_validator import validate_sql


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = str(PROJECT_ROOT / "data" / "database.db")

app = FastAPI(title="Natural Language SQL Assistant")

# MVP session storage. This can later be replaced with a proper upload store.
uploaded_databases: dict[str, Path] = {}


class QueryRequest(BaseModel):
	"""Request body for a natural-language database question."""

	database_id: str
	question: str


class QueryResponse(BaseModel):
	"""Response containing the pipeline SQL and query results."""

	question: str
	generated_sql: str
	validated_sql: str
	results: list[dict[str, Any]]
	row_count: int
	explanation: str


class UploadResponse(BaseModel):
	"""Response returned after a SQLite database upload."""

	database_id: str
	database_schema: dict[str, dict[str, list[dict[str, str]]]] = Field(alias="schema")


@app.get("/health")
def health() -> dict[str, str]:
	"""Report that the API is running."""
	return {"status": "ok", "message": "Natural Language SQL API is running."}


@app.get("/schema")
def schema() -> dict[str, dict[str, list[dict[str, str]]]]:
	"""Return the dynamically inspected demo database schema."""
	try:
		return get_schema(DATABASE_PATH)
	except ValueError as error:
		raise HTTPException(status_code=404, detail=str(error)) from error
	except Exception as error:
		raise HTTPException(status_code=500, detail=f"Could not load database schema: {error}") from error


@app.post("/upload", response_model=UploadResponse)
async def upload_database(file: UploadFile = File(...)) -> UploadResponse:
	"""Save and inspect a temporary user-uploaded SQLite database."""
	if not file.filename or Path(file.filename).suffix.lower() != ".db":
		raise HTTPException(status_code=400, detail="Please upload a SQLite database file with a .db extension.")

	temporary_path: Path | None = None
	try:
		# The file is temporary and is not exposed to the client.
		with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temporary_file:
			temporary_path = Path(temporary_file.name)
			shutil.copyfileobj(file.file, temporary_file)

		# Schema inspection confirms that the uploaded file is a readable SQLite database.
		detected_schema = get_schema(str(temporary_path))
		database_id = uuid4().hex
		uploaded_databases[database_id] = temporary_path
		return UploadResponse(database_id=database_id, schema=detected_schema)
	except Exception as error:
		if temporary_path is not None:
			temporary_path.unlink(missing_ok=True)
		raise HTTPException(status_code=400, detail=f"Could not read the uploaded SQLite database: {error}") from error
	finally:
		await file.close()


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
	"""Run the natural-language-to-SQL pipeline for one user question."""
	# Resolve the client-provided ID through the server-side temporary mapping.
	database_path = uploaded_databases.get(request.database_id)
	if database_path is None or not database_path.is_file():
		uploaded_databases.pop(request.database_id, None)
		raise HTTPException(status_code=404, detail="The database_id does not exist or has expired.")

	if not request.question.strip():
		raise HTTPException(status_code=400, detail="Question cannot be empty.")

	try:
		# Keep the raw generated SQL separate; only the validated SQL is executed.
		database_schema = get_schema(str(database_path))
		generated_sql = generate_sql(request.question, database_schema)
		validated_sql = validate_sql(generated_sql)
		data_frame = execute_query(str(database_path), validated_sql)

		# Replace missing values before converting Pandas data into JSON records.
		records = data_frame.astype(object).where(pd.notna(data_frame), None).to_dict(orient="records")
		explanation = generate_explanation(
			question=request.question,
			sql=validated_sql,
			results=records,
		)
		return QueryResponse(
			question=request.question,
			generated_sql=generated_sql,
			validated_sql=validated_sql,
			results=jsonable_encoder(records),
			row_count=len(data_frame),
			explanation=explanation,
		)
	except ValueError as error:
		raise HTTPException(status_code=400, detail=str(error)) from error
	except RuntimeError as error:
		raise HTTPException(status_code=500, detail=str(error)) from error
	except Exception as error:
		raise HTTPException(status_code=500, detail=f"Query request failed: {error}") from error
