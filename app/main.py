import sqlite3
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from app.database import get_db, init_db
from app.models import StudentBase, StudentCreate, StudentOut, StudentUpdate
from app.ollama_ext import OllamaUnavailable, ask_about_students

COLUMNS = (
    "student_id", "name", "date_of_birth", "email", "phone",
    "course", "address", "enrollment_date",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Student Records API", version="1.0.0", lifespan=lifespan)


def _fetch(db: sqlite3.Connection, student_id: str) -> dict:
    row = db.execute("SELECT * FROM students WHERE student_id = ?", (student_id,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Student '{student_id}' not found")
    return dict(row)


def _to_row(student: StudentBase) -> dict:
    return student.model_dump(mode="json")


# ---------- CREATE ----------
@app.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, db: sqlite3.Connection = Depends(get_db)):
    data = student.model_dump(mode="json")
    try:
        db.execute(
            "INSERT INTO students (student_id, name, date_of_birth, email, phone, "
            "course, address, enrollment_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            tuple(data[c] for c in COLUMNS),
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Student '{data['student_id']}' already exists")
    return _fetch(db, data["student_id"])


# ---------- READ ----------
@app.get("/students", response_model=list[StudentOut])
def list_students(
    name: Optional[str] = Query(None, description="Case-insensitive partial match"),
    course: Optional[str] = Query(None, description="Case-insensitive exact match"),
    email: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: sqlite3.Connection = Depends(get_db),
):
    clauses, params = [], []
    if name:
        clauses.append("name LIKE ?")
        params.append(f"%{name}%")
    if course:
        clauses.append("course = ? COLLATE NOCASE")
        params.append(course)
    if email:
        clauses.append("email = ? COLLATE NOCASE")
        params.append(email)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = db.execute(
        f"SELECT * FROM students {where} ORDER BY student_id LIMIT ? OFFSET ?",
        (*params, limit, offset),
    ).fetchall()
    return [dict(r) for r in rows]


@app.get("/students/{student_id}", response_model=StudentOut)
def get_student(student_id: str, db: sqlite3.Connection = Depends(get_db)):
    return _fetch(db, student_id)


# ---------- UPDATE ----------
@app.put("/students/{student_id}", response_model=StudentOut)
def replace_student(student_id: str, student: StudentBase, db: sqlite3.Connection = Depends(get_db)):
    _fetch(db, student_id)  # 404 if missing
    data = _to_row(student)
    db.execute(
        "UPDATE students SET name=?, date_of_birth=?, email=?, phone=?, "
        "course=?, address=?, enrollment_date=? WHERE student_id=?",
        (data["name"], data["date_of_birth"], data["email"], data["phone"],
         data["course"], data["address"], data["enrollment_date"], student_id),
    )
    db.commit()
    return _fetch(db, student_id)


@app.patch("/students/{student_id}", response_model=StudentOut)
def update_student(student_id: str, updates: StudentUpdate, db: sqlite3.Connection = Depends(get_db)):
    existing = _fetch(db, student_id)
    merged = {**existing, **updates.model_dump(exclude_unset=True, mode="json")}
    validated = StudentBase(**merged)  # re-runs contact and format validation
    data = _to_row(validated)
    db.execute(
        "UPDATE students SET name=?, date_of_birth=?, email=?, phone=?, "
        "course=?, address=?, enrollment_date=? WHERE student_id=?",
        (data["name"], data["date_of_birth"], data["email"], data["phone"],
         data["course"], data["address"], data["enrollment_date"], student_id),
    )
    db.commit()
    return _fetch(db, student_id)


# ---------- DELETE ----------
@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: str, db: sqlite3.Connection = Depends(get_db)):
    _fetch(db, student_id)
    db.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- OPTIONAL: Ollama natural-language Q&A ----------
class Question(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@app.post("/ask")
def ask(q: Question, db: sqlite3.Connection = Depends(get_db)):
    records = [dict(r) for r in db.execute("SELECT * FROM students").fetchall()]
    try:
        answer = ask_about_students(q.question, records)
    except OllamaUnavailable as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"Ollama unavailable: {exc}")
    return {"answer": answer}
