"""Modern Streamlit frontend for the Natural Language to SQL assistant."""

import json
import html
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd
import streamlit as st


BACKEND_URL = "http://127.0.0.1:8000"
EXAMPLE_QUESTIONS = [
	("Top customers", "Top 5 customers by total spending"),
	("Orders by customer", "Number of orders by customer"),
	("Average price", "Average product price by category"),
	("Recent orders", "Show orders placed after a specific date"),
]


def initialize_session_state() -> None:
	"""Initialize values that need to survive Streamlit reruns."""
	defaults = {
		"database_id": None,
		"schema": None,
		"question": "",
		"query_response": None,
		"upload_signature": None,
	}
	for key, value in defaults.items():
		if key not in st.session_state:
			st.session_state[key] = value


def apply_custom_css() -> None:
	"""Apply the small set of styles needed for the visual hierarchy."""
	st.markdown(
		"""
		<style>
		:root {
			--navy: #111831;
			--ink: #1a2238;
			--muted: #68748a;
			--indigo: #5547c8;
			--purple: #8059d8;
			--lavender: #f1efff;
			--blue-soft: #edf4ff;
			--line: #dce2ed;
			--surface: #ffffff;
			--page: #f4f5fb;
		}
		.stApp { background: var(--page); }
		.block-container { max-width: 1080px; padding: 2.2rem 2rem 4.5rem; }
		.hero { background: linear-gradient(118deg, #10162f 0%, #252466 55%, #4f3b93 100%); border: 1px solid #3b3a78; border-radius: 20px; box-shadow: 0 18px 40px rgba(36, 31, 91, 0.2); color: white; margin-bottom: 2.2rem; overflow: hidden; padding: 2.15rem 2.25rem 2rem; position: relative; }
		.hero::after { background: radial-gradient(circle, rgba(159, 126, 255, 0.32), rgba(159, 126, 255, 0) 68%); content: ""; height: 280px; position: absolute; right: -60px; top: -130px; width: 360px; }
		.eyebrow { color: #b9b5ff; font-size: 0.72rem; font-weight: 750; letter-spacing: 0.17em; position: relative; z-index: 1; }
		.hero-title { color: white; font-size: 2.45rem; font-weight: 750; letter-spacing: -0.025em; line-height: 1.08; margin: 0.55rem 0 0.75rem; position: relative; z-index: 1; }
		.hero-copy { color: #d9daf2; font-size: 1.03rem; line-height: 1.55; margin: 0; max-width: 650px; position: relative; z-index: 1; }
		.hero-badges { display: flex; flex-wrap: wrap; gap: 0.55rem; margin-top: 1.25rem; position: relative; z-index: 1; }
		.hero-badges span { background: rgba(255, 255, 255, 0.11); border: 1px solid rgba(255, 255, 255, 0.18); border-radius: 999px; color: #f0efff; font-size: 0.75rem; font-weight: 650; padding: 0.38rem 0.75rem; }
		.section-title { color: var(--ink); font-size: 1.32rem; font-weight: 750; letter-spacing: -0.01em; margin: 2rem 0 0.3rem; }
		.section-copy { color: var(--muted); font-size: 0.9rem; margin-bottom: 0.95rem; }
		div[data-testid="stVerticalBlockBorderWrapper"] { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; border-top: 3px solid var(--indigo); box-shadow: 0 12px 30px rgba(45, 44, 96, 0.07); padding: 0.8rem 1.15rem 0.7rem; }
		div[data-testid="stVerticalBlockBorderWrapper"]:has(.query-card-marker) { background: linear-gradient(135deg, #f5f2ff, #eff6ff); border-color: #d9d4f4; }
		div[data-testid="stVerticalBlockBorderWrapper"]:has(.results-card-marker) { background: #fafbff; border-top-color: var(--purple); }
		div[data-testid="stFileUploader"] { background: linear-gradient(135deg, #fbfaff, #f2f5ff); border: 1px dashed #aca4df; border-radius: 12px; padding: 0.25rem 0.75rem; }
		.connection-status { align-items: center; background: #edf9f2; border: 1px solid #c9ead6; border-radius: 9px; color: #28734d; display: flex; font-size: 0.86rem; font-weight: 750; justify-content: space-between; margin: 0.75rem 0 0.4rem; padding: 0.62rem 0.8rem; }
		.connection-status small { color: #5c8b70; font-size: 0.76rem; font-weight: 550; }
		.schema-card { background: linear-gradient(135deg, #faf9ff, #f5f8ff); border: 1px solid #e2e1f3; border-radius: 10px; margin: 0.8rem 0; overflow: hidden; }
		.schema-card-title { background: #eeecff; border-bottom: 1px solid #dfdcf7; color: #453a9c; font-size: 0.73rem; font-weight: 800; letter-spacing: 0.12em; padding: 0.6rem 0.8rem; }
		.schema-column { border-bottom: 1px solid #e9ebf4; color: #39465a; display: flex; font-size: 0.82rem; justify-content: space-between; padding: 0.5rem 0.8rem; }
		.schema-column:last-child { border-bottom: 0; }
		.schema-column span:last-child { color: #7567b9; font-family: monospace; font-size: 0.76rem; }
		.explanation-panel { background: linear-gradient(135deg, #f7f5ff, #f1f7ff); border: 1px solid #dedcf3; border-radius: 13px; margin-top: 1.25rem; padding: 1rem 1.15rem; }
		.explanation-block + .explanation-block { border-top: 1px solid #e1e2f0; margin-top: 0.9rem; padding-top: 0.9rem; }
		.explanation-heading { color: #44389d; font-size: 0.9rem; font-weight: 750; margin-bottom: 0.3rem; }
		.explanation-copy { color: #4d5870; font-size: 0.88rem; line-height: 1.6; margin: 0; }
		.question-label { color: var(--ink); font-size: 1.32rem; font-weight: 750; letter-spacing: -0.01em; margin: 0.35rem 0 0.8rem; }
		div[data-testid="stTextArea"] textarea { background: #fcfbff; border: 1px solid #c9c5ed; border-radius: 11px; color: var(--ink); font-size: 1rem; line-height: 1.5; padding: 0.9rem 1rem; }
		div[data-testid="stTextArea"] textarea:focus { border-color: var(--indigo); box-shadow: 0 0 0 1px var(--indigo), 0 0 0 4px rgba(85, 71, 200, 0.1); }
		div.stButton > button { background: #f8f8ff; border: 1px solid #d9d8ef; border-radius: 999px; color: #57527a; font-size: 0.78rem; min-height: 2.3rem; transition: border-color 120ms ease, background 120ms ease, color 120ms ease; }
		div.stButton > button:hover { background: #eeecff; border-color: #aaa2df; color: #4b3fae; }
		div.stButton > button[kind="primary"] { background: linear-gradient(100deg, var(--indigo), var(--purple)); border: 0; border-radius: 10px; box-shadow: 0 8px 18px rgba(85, 71, 200, 0.25); color: white; font-size: 0.92rem; font-weight: 750; margin-top: 1.2rem; padding: 0.25rem 1.35rem; }
		div.stButton > button[kind="primary"]:hover { background: linear-gradient(100deg, #4639ad, #7049c3); box-shadow: 0 10px 22px rgba(85, 71, 200, 0.32); color: white; }
		.results-meta { background: #edf9f2; border: 1px solid #c9ead6; border-radius: 999px; color: #28734d; display: inline-block; font-size: 0.82rem; font-weight: 700; margin-bottom: 0.95rem; padding: 0.38rem 0.75rem; }
		[data-testid="stSidebar"] { background: var(--navy); border-right: 1px solid #2d3459; }
		[data-testid="stSidebar"] * { color: #d9dcf1; }
		.sidebar-brand { color: #a99cff; font-size: 0.7rem; font-weight: 800; letter-spacing: 0.15em; }
		.sidebar-heading { color: white; font-size: 0.88rem; font-weight: 750; margin-top: 1.55rem; }
		.sidebar-copy { color: #abb2cf; font-size: 0.81rem; line-height: 1.6; }
		</style>
		</style>
		""",
		unsafe_allow_html=True,
	)


def upload_database(file_name: str, file_bytes: bytes) -> dict:
	"""Send an uploaded SQLite file to the FastAPI upload endpoint."""
	boundary = "----NaturalLanguageSQLBoundary"
	safe_file_name = Path(file_name).name.replace('"', "")
	body = (
		f"--{boundary}\r\n"
		f'Content-Disposition: form-data; name="file"; filename="{safe_file_name}"\r\n'
		"Content-Type: application/octet-stream\r\n\r\n"
	).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

	request = urllib.request.Request(
		f"{BACKEND_URL}/upload",
		data=body,
		headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
		method="POST",
	)
	with urllib.request.urlopen(request, timeout=30) as response:
		return json.loads(response.read().decode("utf-8"))


def render_schema(schema: dict) -> None:
	"""Render schema tables as readable column/type lists, not raw JSON."""
	with st.expander("View schema", expanded=False):
		if not schema:
			st.info("No tables were found in this database.")
			return

		for table_name, table_info in schema.items():
			table_title = html.escape(str(table_name).upper())
			column_rows = []
			for column in table_info.get("columns", []):
				column_name = html.escape(str(column.get("name", "")))
				column_type = html.escape(str(column.get("type", "")))
				column_rows.append(
					f'<div class="schema-column"><span>{column_name}</span><span>{column_type}</span></div>'
				)
			st.markdown(
				f'<div class="schema-card"><div class="schema-card-title">{table_title}</div>{"".join(column_rows)}</div>',
				unsafe_allow_html=True,
			)


def set_question(question: str) -> None:
	"""Populate the question field when a suggestion button is clicked."""
	st.session_state.question = question


def run_query() -> None:
	"""Send the current database ID and question to the FastAPI backend."""
	database_id = st.session_state.database_id
	question = st.session_state.question.strip()
	if not database_id:
		st.error("Please upload a SQLite database first.")
		return
	if not question:
		st.error("Please enter a question.")
		return

	request_body = json.dumps({"database_id": database_id, "question": question}).encode("utf-8")
	request = urllib.request.Request(
		f"{BACKEND_URL}/query",
		data=request_body,
		headers={"Content-Type": "application/json"},
		method="POST",
	)

	try:
		with st.spinner("Analyzing your data..."):
			with urllib.request.urlopen(request, timeout=60) as response:
				st.session_state.query_response = json.loads(response.read().decode("utf-8"))
	except urllib.error.HTTPError as error:
		if error.code in (400, 422):
			st.error("The query could not be safely executed.")
		elif error.code == 404:
			st.error("This database session has expired. Please upload the database again.")
		else:
			st.error("Something went wrong while processing your query.")
	except (urllib.error.URLError, TimeoutError):
		st.error("Unable to connect to the backend.")
	except (KeyError, json.JSONDecodeError):
		st.error("The backend returned an unexpected response.")


def render_explanation(explanation: object) -> None:
	"""Render the two labeled explanation sections without repeating labels."""
	if not isinstance(explanation, str) or not explanation.strip():
		st.info("No explanation was returned for this query.")
		return

	how_label = "How this query works:"
	results_label = "What the results tell us:"
	explanation_text = explanation.strip()
	how_start = explanation_text.find(how_label)
	results_start = explanation_text.find(results_label)
	if how_start == -1 or results_start == -1 or results_start <= how_start:
		st.info("The query completed, but no explanation was available.")
		return

	how_text = explanation_text[how_start + len(how_label) : results_start].strip()
	results_text = explanation_text[results_start + len(results_label) :].strip()
	if not how_text or not results_text:
		st.info("The query completed, but no explanation was available.")
		return

	how_html = html.escape(how_text).replace("\n", "<br>")
	results_html = html.escape(results_text).replace("\n", "<br>")
	st.markdown(
		f'<div class="explanation-panel"><div class="explanation-block"><div class="explanation-heading">🧠 How this query works</div><p class="explanation-copy">{how_html}</p></div><div class="explanation-block"><div class="explanation-heading">📊 What the results tell us</div><p class="explanation-copy">{results_html}</p></div></div>',
		unsafe_allow_html=True,
	)


def render_results(response: dict) -> None:
	"""Render query status, rows, and generated SQL after a successful query."""
	st.markdown('<span class="results-card-marker"></span>', unsafe_allow_html=True)
	st.markdown('<div class="section-title">03 Results</div>', unsafe_allow_html=True)
	st.markdown(
		f'<div class="results-meta">✓ Query completed · {response.get("row_count", 0)} rows</div>',
		unsafe_allow_html=True,
	)

	results = response.get("results", [])
	if results:
		st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
	else:
		st.info("The query returned no rows.")

	st.markdown("**Generated SQL**")
	st.code(response.get("generated_sql", ""), language="sql")
	render_explanation(response.get("explanation"))


def render_sidebar() -> None:
	"""Render the minimal product, workflow, and security sidebar."""
	with st.sidebar:
		st.markdown('<div class="sidebar-brand">AI SQL ANALYTICS</div>', unsafe_allow_html=True)
		st.markdown('<div class="sidebar-heading">About</div>', unsafe_allow_html=True)
		st.markdown('<div class="sidebar-copy">Ask questions about your SQLite data using natural language.</div>', unsafe_allow_html=True)
		st.markdown('<div class="sidebar-heading">Workflow</div>', unsafe_allow_html=True)
		st.markdown(
			'<div class="sidebar-copy">01 &nbsp; Upload database<br>02 &nbsp; Ask question<br>03 &nbsp; Generate SQL<br>04 &nbsp; Validate query<br>05 &nbsp; Execute read-only SQL<br>06 &nbsp; View results</div>',
			unsafe_allow_html=True,
		)
		st.markdown('<div class="sidebar-heading">Security</div>', unsafe_allow_html=True)
		st.markdown('<div class="sidebar-copy">Generated SQL passes through a read-only validation layer before execution.</div>', unsafe_allow_html=True)


def render_header() -> None:
	"""Render the compact product introduction."""
	st.markdown(
		'<div class="hero"><div class="eyebrow">AI • SQL • ANALYTICS</div><div class="hero-title">Ask your data anything.</div><p class="hero-copy">Upload a SQLite database and turn natural-language questions into validated SQL insights.</p><div class="hero-badges"><span>Read-only SQL</span><span>Schema-aware AI</span></div></div>',
		unsafe_allow_html=True,
	)


def render_database_section() -> None:
	"""Render the uploader and the active database status."""
	st.markdown('<div class="section-title">01 Connect your database</div>', unsafe_allow_html=True)
	st.markdown('<div class="section-copy">Upload a SQLite .db file to start exploring your data.</div>', unsafe_allow_html=True)
	with st.container(border=True):
		uploaded_file = st.file_uploader(
			"Upload SQLite database",
			type=["db"],
			help="The database is used for the current session only.",
		)

		if uploaded_file is not None:
			file_signature = f"{uploaded_file.name}:{uploaded_file.size}"
			if file_signature != st.session_state.upload_signature:
				try:
					with st.spinner("Connecting your database..."):
						upload_result = upload_database(uploaded_file.name, uploaded_file.getvalue())
					st.session_state.database_id = upload_result["database_id"]
					st.session_state.schema = upload_result["schema"]
					st.session_state.upload_signature = file_signature
					st.session_state.query_response = None
				except urllib.error.HTTPError:
					st.error("Database upload failed. Please choose a valid SQLite .db file.")
				except (urllib.error.URLError, TimeoutError):
					st.error("Unable to connect to the backend.")
				except (KeyError, json.JSONDecodeError):
					st.error("The backend returned an unexpected upload response.")

		if st.session_state.database_id and st.session_state.schema is not None:
			file_label = html.escape(Path(uploaded_file.name).name) if uploaded_file else "Current session"
			st.markdown(
				f'<div class="connection-status"><span>✓ Database connected</span><small>{file_label}</small></div>',
				unsafe_allow_html=True,
			)
			render_schema(st.session_state.schema)


def render_query_section() -> None:
	"""Render the question field, suggestion chips, and run action."""
	with st.container(border=True):
		st.markdown('<span class="query-card-marker"></span>', unsafe_allow_html=True)
		st.markdown('<div class="question-label">02 Ask your question</div>', unsafe_allow_html=True)
		st.text_area(
			"Natural-language question",
			key="question",
			height=112,
			placeholder="e.g. Show me the top 5 customers by total spending.",
			label_visibility="collapsed",
		)
		st.caption("Try asking")
		example_columns = st.columns(4)
		for index, (label, question) in enumerate(EXAMPLE_QUESTIONS):
			example_columns[index].button(
				label,
				key=f"example_question_{index}",
				on_click=set_question,
				args=(question,),
				use_container_width=True,
			)

		if st.button("✦ Run analysis", type="primary"):
			run_query()


def main() -> None:
	"""Render the Streamlit analytics workspace."""
	st.set_page_config(page_title="SQL Analytics Assistant", layout="wide")
	initialize_session_state()
	apply_custom_css()
	render_sidebar()
	render_header()
	render_database_section()

	if st.session_state.database_id and st.session_state.schema is not None:
		render_query_section()
		if st.session_state.query_response:
			with st.container(border=True):
				render_results(st.session_state.query_response)
	else:
		st.info("Upload a SQLite database to start exploring your data.")


if __name__ == "__main__":
	main()
