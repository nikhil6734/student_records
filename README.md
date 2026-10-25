# Student Records API

FastAPI + SQLite CRUD service for student records. Optional Ollama endpoint for natural-language questions.

## Setup

```bash
cd student_records
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Interactive docs: http://127.0.0.1:8000/docs

Optional environment variables:
- `STUDENTS_DB` (default `students.db`)
- `OLLAMA_URL` (default `http://localhost:11434`)
- `OLLAMA_MODEL` (default `llama3`)

## Record fields

| Field | Required | Notes |
|---|---|---|
| student_id | yes (create) | unique, max 20 chars |
| name | yes | |
| date_of_birth | yes | `YYYY-MM-DD` |
| email / phone | at least one | email validated; phone digits, optional leading `+` |
| course | no | |
| address | no | |
| enrollment_date | no | `YYYY-MM-DD` |

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | /students | Create (201, 409 if ID exists) |
| GET | /students | List / filter: `name`, `course`, `email`, `limit`, `offset` |
| GET | /students/{student_id} | View one (404 if missing) |
| PUT | /students/{student_id} | Full replace |
| PATCH | /students/{student_id} | Partial update |
| DELETE | /students/{student_id} | Delete (204) |
| POST | /ask | Ask a question about the records (needs Ollama running) |

## Examples

```bash
curl -X POST http://127.0.0.1:8000/students -H "Content-Type: application/json" -d '{
  "student_id": "S001", "name": "Asha Rao", "date_of_birth": "2004-05-12",
  "email": "asha@example.com", "course": "B.Tech CSE", "enrollment_date": "2024-07-01"
}'

curl "http://127.0.0.1:8000/students?course=b.tech%20cse"
curl -X PATCH http://127.0.0.1:8000/students/S001 -H "Content-Type: application/json" -d '{"phone": "+91 98765 43210"}'
curl -X DELETE http://127.0.0.1:8000/students/S001
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d '{"question": "Which students are in B.Tech CSE?"}'
```

## Layout

```
student_records/
├── app/
│   ├── __init__.py
│   ├── main.py          # routes
│   ├── models.py        # Pydantic schemas
│   ├── database.py      # SQLite connection and schema
│   └── ollama_ext.py    # optional Ollama extension
├── requirements.txt
└── README.md
```
