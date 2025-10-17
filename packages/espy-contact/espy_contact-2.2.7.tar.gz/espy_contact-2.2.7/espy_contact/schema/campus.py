"""Copyright 2024 Everlasting Systems and Solutions LLC (www.myeverlasting.net).
All Rights Reserved.

No part of this software or any of its contents may be reproduced, copied, modified or adapted, without the prior written consent of the author, unless otherwise indicated for stand-alone materials.

For permission requests, write to the publisher at the email address below:
office@myeverlasting.net

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

from pydantic import BaseModel, Field, AnyHttpUrl, EmailStr, field_validator
from typing import List, Literal, Optional
from datetime import datetime, date, timedelta
from espy_contact.util.enums import (
    AccessRoleEnum,
    ResourceEnum,
    StatusEnum,
    SchoolTypeEnum,
)
from espy_contact.schema.schema import SchoolDto, UserResponse, AddressDto


class Resource(BaseModel):
    """Type of resource can be Poll, Form Builder, Questionnaire, RichText, Video, Audio, File, Hyperlink."""

    id: Optional[int] = None
    title: str
    type: ResourceEnum
    lesson_id: int


class Lesson_note(BaseModel):
    id: Optional[int] = None
    title: str
    content: str
    lesson_id: Optional[int] = None


class Quiz(BaseModel):
    id: Optional[int] = None
    title: str
    question: str
    options: List[str]
    answer: str
    lesson_id: Optional[int] = None


class Lessonbase(BaseModel):
    title: str
    term: str
    academic_year: str = Field(
        description="The academic year of the lesson",
        default=f"{datetime.now().year}/{datetime.now().year + 1}",
    )
    lesson_note: str | None = Field(None, description="Optional lesson note")
    due_date: date | None = Field(
        default_factory=lambda: date.today() + timedelta(days=90)
    )

    @field_validator("academic_year")
    def validate_academic_year(cls, v):
        # Extract the starting year from the format "2024/2025"
        try:
            start_year = int(v.split("/")[0])
            if start_year < date.today().year:
                raise ValueError("academic year cannot be in the past")
        except (ValueError, IndexError):
            raise ValueError("academic year must be in format 'YYYY/YYYY'")
        return v

    @field_validator("due_date")
    def validate_due_date(cls, v):
        if v < date.today():
            raise ValueError("due date cannot be in the past")
        return v


class LessonCreate(Lessonbase):
    topic_id: int | None = None
    instructor_id: int | None = None


class LessonUpdate(LessonCreate):
    id: int


class LessonResponse(BaseModel):
    id: int
    class_id: int | None = None
    title: str  # Intro to Biology
    term: str
    academic_year: str = Field(
        description="The academic year of the lesson",
        default=f"{datetime.now().year}/{datetime.now().year + 1}",
    )
    topic_id: int | None = None
    instructor_id: int | None = None
    due_date: datetime | None = None
    lesson_note: str | None = None


class TopicCreate(BaseModel):
    title: str
    week: str | None = None


class TopicDto(TopicCreate):
    subject_id: int | None = None


class TopicBase(TopicDto):  # Introduction to Biology
    id: Optional[int] = None


class SubjectCreate(BaseModel):
    title: str  # Biology
    class_id: int
    overview: str | None = None


class SubjectDto(SubjectCreate):
    topics: list[TopicDto] | None = None
    lesson_count: int | None = 0
    topic_count: int | None = 0

    @field_validator("title", mode="before")
    def uppercase_title(cls, v: str) -> str:
        return v.upper() if isinstance(v, str) else v


class TopicComplete(BaseModel):
    topic: TopicCreate
    lessons: list[Lessonbase]


class SubjectComplete(BaseModel):
    subject: SubjectCreate
    topics: list[TopicComplete]
    term: str

    class Config:
        from_attributes = True


class SubjectResponse(SubjectDto):
    id: int
    teacher: str | None = None
    teacher_id: int | None = None


class SubjectUpdate(SubjectCreate):
    id: int


class ClassroomCreate(BaseModel):
    title: str
    subclasses: Optional[str] = None
    class_category: SchoolTypeEnum | None = None
    level: int | None = None


class ClassroomDto(ClassroomCreate):
    id: int | None = None
    subjects: list[SubjectDto] | None = None
    teacher: UserResponse | None = None  # ManyToMany relationship with Teacher
    level: int | None = None

    class Config:
        from_attributes = True


class Makeschool(BaseModel):
    school_type: SchoolTypeEnum
    classes: List[ClassroomDto]
    created_by: str


class ReviewDto(BaseModel):
    # to-do separate teacher review from subject review
    id: Optional[int] = None
    title: str
    review: str
    rating: float
    reviewer: str
    created_at: Optional[datetime] = None
    subject_id: int
    teacher_id: int


class ReviewResultDto(BaseModel):
    id: int
    name: str
    review_count: int
    average_rating: float


class Holiday(BaseModel):
    id: Optional[int] = None
    name: str
    remarks: Optional[str] = None
    start_date: datetime
    end_date: datetime
    created_at: Optional[datetime] = None
    created_by: str


class SchoolTerm(BaseModel):
    id: Optional[int] = None
    term: str
    academic_year: int
    start_date: datetime
    end_date: datetime
    remarks: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: str


class SchoolProfileField(BaseModel):
    school_id: int
    logo: str = Field(
        description="url to the school logo",
        default="https://essluploads.s3.amazonaws.com/logo/horace-logo.png",
    )
    slug: str | None = None
    mission: str | None = None
    vision: str | None = None
    motto: str | None = None
    banner: str | None = None
    contact: str | None = None
    website: AnyHttpUrl | None = None
    portal: AnyHttpUrl
    social_media: str | None = Field(None, description="comma separated strings")
    established: int | None = None
    school_type: SchoolTypeEnum = Field(
        description="Type of school e.g Private, Public, International",
        default=SchoolTypeEnum.HIGHSCHOOL,
    )
    affiliation: str | None = None
    board: str | None = None
    facilities: str | None = Field(None, description="comma separated strings")
    created_at: datetime | None = None


class SchoolProfile(SchoolProfileField):
    id: int

    class Config:
        from_attributes = True


class SchoolProfileLite(BaseModel):
    id: int
    name: str
    logo: str = Field(
        description="url to the school logo",
        default="https://essluploads.s3.amazonaws.com/logo/horace-logo.png",
    )
    email: EmailStr
    website: AnyHttpUrl
    portal: AnyHttpUrl
    address: AddressDto
    social_media: str | None = None

    class Config:
        from_attributes = True


class SchoolComplete(SchoolProfile):
    school: SchoolDto


class Extracurricular(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    start_date: datetime
    end_date: datetime
    venue: Optional[str] = None
    created_by: str
    status: StatusEnum = StatusEnum.NEW
    coordinator: Optional[str] = None
    images: Optional[str] = Field(None, description="comma separated strings")
    created_at: Optional[datetime] = None


class Asset(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    worth: Optional[str] = None
    type: Optional[str] = None
    url: Optional[AnyHttpUrl] = None
    tags: Optional[str] = Field(None, description="comma separated strings")
    images: Optional[str] = Field(None, description="comma separated strings")
    created_by: str
    status: StatusEnum = StatusEnum.NEW
    created_at: Optional[datetime] = None


class Vacancy(BaseModel):
    id: Optional[int] = None
    title: str
    description: str = Field(description="detailed job description")
    requirements: Optional[str] = Field(None, description="comma separated strings")
    salary: Optional[str] = Field(
        None, description="amount with currency and duration e.g $48,000 per annum"
    )
    location: Optional[str] = None
    deadline: datetime = Field(description="date you will stop accepting applications")
    created_by: str
    status: StatusEnum = StatusEnum.NEW
    created_at: Optional[datetime] = None


class AttendanceBase(BaseModel):
    user_id: int
    subject_id: int | None = None
    classroom_id: int | None = None
    is_present: bool
    created_by: EmailStr
    latitude: float
    longitude: float
    remarks: str | None = None
    token: str


class AttendanceDto(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    classroom_id: int | None = None
    subject_id: int | None = None
    student_id: int | None = None
    role: AccessRoleEnum | None = None


class Attendance(BaseModel):
    id: Optional[int] = None
    user_id: int
    subject_id: Optional[int] = None
    classroom_id: Optional[int] = None
    is_present: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: EmailStr
    remarks: Optional[str] = None
    user: UserResponse | None = None


class AttendanceLte(BaseModel):
    date: date
    status: Literal["present", "absent", "late"]


class AttendanceResponse(BaseModel):
    user_id: int
    name: str
    image: str | None = None
    role: AccessRoleEnum
    subject: str | None = None
    classroom: str | None = None
    attendance: list[AttendanceLte] | None = None


class AbsenteeDto(BaseModel):
    start: date | None = None
    end: date | None = None
    role: AccessRoleEnum | None = None


class Absentee(BaseModel):
    id: Optional[int] = None
    first_name: str
    last_name: str
    email: EmailStr
    roles: list[AccessRoleEnum]
    date: datetime
    reason: str
    note: str | None = None


class Student_class(BaseModel):
    student_ids: list[int]
    class_id: int
    subclass: Optional[str] = None
    term: str
    year: str


class Teacher_class(BaseModel):
    teacher_id: int
    class_id: int
    term: str | None = None
    year: int | None = None
