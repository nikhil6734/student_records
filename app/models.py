from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator

PHONE_PATTERN = r"^\+?[0-9][0-9 \-()]{6,19}$"


class StudentBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, pattern=PHONE_PATTERN)
    course: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=255)
    enrollment_date: Optional[date] = None

    @model_validator(mode="after")
    def require_contact(self):
        if not self.email and not self.phone:
            raise ValueError("Provide at least one contact method: email or phone")
        return self


class StudentCreate(StudentBase):
    student_id: str = Field(min_length=1, max_length=20)


class StudentUpdate(BaseModel):
    """Partial update: only fields present in the request body are changed."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, pattern=PHONE_PATTERN)
    course: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=255)
    enrollment_date: Optional[date] = None


class StudentOut(StudentBase):
    student_id: str
