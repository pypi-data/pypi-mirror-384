"""Copyright 2024 Everlasting Systems and Solutions LLC (www.myeverlasting.net).
All Rights Reserved.

No part of this software or any of its contents may be reproduced, copied, modified or adapted, without the prior written consent of the author, unless otherwise indicated for stand-alone materials.

For permission requests, write to the publisher at the email address below:
office@myeverlasting.net

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field, field_validator, AnyHttpUrl
from espy_contact.util.enums import (
    AccessRoleEnum,
    StatusEnum,
    GenderEnum,
    MonthEnum,
    GradeLevel,
    Term,
)
from typing import List, Optional, Literal
import re


class ReachBase(BaseModel):
    id: str
    timestamp: datetime


class SeoRequest(BaseModel):
    url: AnyHttpUrl = Field(description="Your website url")


class WebbuilderRequest(BaseModel):
    id: str
    content: str
    product_id: int


class AddressBase(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str | None = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    country: str


class AddressUpdateDto(AddressBase):
    id: int


class AddressDto(AddressBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True


class UserEmail(BaseModel):
    email: EmailStr


class UserReset(UserEmail):
    token: str
    password: str
    new_password: str | None = None


class UserBase(BaseModel):
    first_name: str
    last_name: str
    is_active: bool = False
    roles: List[AccessRoleEnum]
    socialmedia: Optional[str] = None  # comma separated string
    gender: GenderEnum
    token: str | None = None
    username: str | None = None
    attendance_token: str | None = None
    subclass: Optional[str] = None


def strip_prefix(email: str) -> str:
    """
    Strips the prefix from an email address.

    Args:
        email (str): The email address to strip.

    Returns:
        str: The email address without the prefix.
    """
    match = re.match(r"secondary-\d+\+(.+)", email)
    if match:
        return match.group(1)
    return email


class UserResponse(UserBase):
    id: Optional[int] = None
    timestamp: Optional[datetime] = datetime.now()
    email: EmailStr
    phone_number: str | None = None
    status: StatusEnum = StatusEnum.NEW
    address: AddressDto | None = None
    dp: str | None = None

    @field_validator("roles")
    def validate_roles(cls, roles):
        if AccessRoleEnum.STUDENT in roles and AccessRoleEnum.ADMIN in roles:
            raise ValueError(
                "User cannot have roles of Student and Admin at the same time"
            )
        return roles

    @field_validator("email", mode="before")
    def extract_email(cls, email) -> str:
        return strip_prefix(email)

    class Config:
        from_attributes = True


class AppuserDto(UserResponse):
    password: str
    address: Optional[AddressDto] = None


class AppuserUpdate(UserBase):
    id: int
    status: StatusEnum
    address: Optional[AddressUpdateDto] = None

    @field_validator("roles")
    def validate_roles(cls, roles):
        if AccessRoleEnum.STUDENT in roles and AccessRoleEnum.ADMIN in roles:
            raise ValueError(
                "User cannot have roles of Student and Admin at the same time"
            )
        return roles

    class Config:
        extra = "ignore"


class EnrollmentBase(UserBase):
    dob: date
    gender: GenderEnum
    nationality: str
    address: AddressBase
    parent_email: EmailStr
    current_school: str
    current_class: str
    achievements: str
    extracurricular: str
    parent_phone: str
    parent_name: str
    parent_occupation: str
    religion: str
    grade_level: GradeLevel
    term: Term
    academic_year: int
    remarks: str
    password: str | None = None
    photo: str | None = None
    birth_certificate: str | None = None
    signature: Optional[str] = None
    is_paid: Optional[bool] = False
    email: EmailStr
    status: StatusEnum = StatusEnum.NEW


class EnrollmentDto(EnrollmentBase):
    roles: Literal[AccessRoleEnum.GUEST.value] = AccessRoleEnum.GUEST.value


class EnrollmentUpdate(EnrollmentBase):
    id: int


class SchoolDto(BaseModel):
    id: Optional[int] = None
    name: str
    address: AddressDto
    owner_id: int
    email: Optional[EmailStr] = None
    status: Optional[StatusEnum] = StatusEnum.NEW
    is_subscribed: bool = False
    logo: str | None = None
    subscribed_on: datetime | None = None
    expiry: datetime | None = None


class SchoolResponse(BaseModel):
    id: str
    name: str
    create_at: datetime
    address_id: str
    owner_id: str


class AcademicHistory(ReachBase):
    """Student or teacher can have multiple AcademicHistory."""

    school_name: str
    start_date: str
    end_date: str
    grade_level: str
    reason_for_leaving: str
    classroom: str  # ForeignKey to Classroom or String
    owner: AppuserDto  # ForeignKey to StudentProfile or None

    # teacher: Teacher  # Optional ForeignKey to Teacher (null allowed) or None


class GenDto(BaseModel):
    start_date: date
    end_date: date


class HomeAnalytics(BaseModel):
    student_count: int
    teacher_count: int
    tranx_total: Optional[int] = None
    expected_tranx: int


class Revenue(BaseModel):
    month: MonthEnum
    income: int
    expense: int
    refunds: int
    net: int


class LeadBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str | None = None
    subject: str | None = None
    message: str | None = None
    created_at: datetime = datetime.now()


class LeadDto(LeadBase):
    id: int


class UserPhoto(BaseModel):
    photo: str
    id: int
