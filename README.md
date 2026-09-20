# AI-Powered Natural Language to SQL Analytics Assistant

An AI-powered analytics assistant that allows users to query databases using natural language instead of writing SQL manually.

The application uses **Gemini** to convert user questions into **SQLite-compatible SQL** based on the actual database schema. The generated query is validated for read-only execution before being executed against the database, and the results are displayed through an interactive **Streamlit** interface with a simple explanation.

### Key Features

* Natural-language to SQL generation
* Schema-aware SQL generation
* Read-only SQL validation
* SQLite query execution
* `.db` file upload support
* Results and SQL visualization
* Simple query/result explanations
* FastAPI backend and Streamlit frontend

### Tech Stack

**Python · FastAPI · Streamlit · SQLite · SQLAlchemy · Pandas · Pydantic · Gemini API**

### Architecture

```text
User Question
     ↓
Streamlit
     ↓
FastAPI
     ↓
Schema + Gemini
     ↓
SQL Validation
     ↓
SQLite
     ↓
Results + Explanation
```

> **Note:** The included database uses synthetic demo business data. This project is an educational/portfolio MVP focused on natural-language database querying and LLM-powered SQL generation.
