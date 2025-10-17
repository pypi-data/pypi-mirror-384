"""Copyright 2024 Everlasting Systems and Solutions LLC (www.myeverlasting.net).
All Rights Reserved.

No part of this software or any of its contents may be reproduced, copied, modified or adapted, without the prior written consent of the author, unless otherwise indicated for stand-alone materials.

For permission requests, write to the publisher at the email address below:
office@myeverlasting.net

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
from pydantic import BaseModel,Field
from typing import List,Optional,Any
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator
from datetime import datetime
from .schema import UserResponse
from bson import ObjectId


PyObjectId = Annotated[str, BeforeValidator(str)]
# class UserModel(BaseModel):
#     """ Horace User record."""
#     id: Optional[PyObjectId] = Field(alias="_id", default=None)
#     firstname: Optional[str] = None
#     lastname: Optional[str] = None
#     email: Optional[str] = None
#     password: Optional[str] = None
#     active: bool = False
class UserCol(BaseModel):
    users: List[UserResponse]

class Course(BaseModel):
    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias='_id')
    author: UserResponse
    course_name: str = Field(..., alias='courseName')
    category: str
    target: str
    curriculum: Any
    brief: str
    price: float
    tax: float
    created_on: datetime = Field(default_factory=datetime.now, alias='createdOn')
    thumbnail: Optional[str] = None
    updated_on: Optional[datetime] = Field(None, alias='updatedOn')
    total_steps: int = Field(..., alias='totalSteps')
    draft: bool

    class Config:
        populate_by_name = True
        arbitrary_types_allowed=True
        json_schema_extra = {
            "example": {
                "author": {
                    # Assuming some example fields for Appuser
                },
                "course_name": "Introduction to Python",
                "category": "Programming",
                "target": "Beginner programmers",
                "curriculum": {
                    "introduction": "Welcome to the course",
                    "contents": [
                        {"module": "Basics", "lessons": ["Setup", "Syntax"]}
                    ]
                },
                "brief": "Learn Python from scratch!",
                "price": 19.99,
                "tax": 1.99,
                "thumbnail": "url_to_thumbnail_image",
                "total_steps": 10,
                "draft": False
            }
        }

class AssetCount(BaseModel):
    quiz_count: int
    lab_count: int
    lesson_count: int
    download_count: int
    note_count: int

class Lecture(BaseModel):
    id: int
    title: str
    video: str
    type: str
    slide: str

class Quiz(BaseModel):
    # Define the properties of Quiz here
    questions: List[str]

class Note(BaseModel):
    # Define the properties of Note here
    content: str

class Section(BaseModel):
    title: str
    description: str
    id: str
    lecture: List[Lecture]
    quiz: Optional[Quiz] = None
    note: Optional[Note] = None

class CurriculumMap(BaseModel):
    section: List[Section]
    requirement: List[str]
    objective: List[str]

class Post(BaseModel):
    id: str
    user: str
    message: str
    type: str
    course: str
    created_on: datetime = Field(default_factory=datetime.now, alias='createdOn')
    modified_on: datetime = Field(default_factory=datetime.now, alias='modifiedOn')
    like: int
    share: int
    rating: int

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        json_schema_extra = {
            "example": {
                "id": "12345",
                "user": "user123",
                "message": "This is a post message.",
                "type": "info",
                "course": "course123",
                "createdOn": "2023-01-01T12:00:00Z",
                "modifiedOn": "2023-01-02T12:00:00Z",
                "like": 10,
                "share": 5,
                "rating": 4
            }
        }
class PostResponse(BaseModel):
    id: str
    user: str
    message: str
    type: str
    course: str
    created_on: datetime = Field(default_factory=datetime.now, alias='createdOn')
    modified_on: datetime = Field(default_factory=datetime.now, alias='modifiedOn')
    like: int
    share: int
    rating: int

    class Config:
        # Use alias generation to maintain the Python convention in code and the original Java naming in JSON
        populate_by_name = True
        from_attributes = True  # Enable ORM mode if integrating with ORMs
        json_schema_extra = {
            "example": {
                "id": "post123",
                "user": "user456",
                "message": "This is a sample post message.",
                "type": "announcement",
                "course": "course789",
                "createdOn": "2023-01-01T12:00:00Z",
                "modifiedOn": "2023-01-02T12:00:00Z",
                "like": 100,
                "share": 50,
                "rating": 5
            }
        }

class CourseResponse(BaseModel):
    course_id: str
    course_name: str
    author: UserResponse
    category: str
    target: str
    curriculum: CurriculumMap
    brief: str
    price: float
    tax: float
    created_on: str
    thumbnail: str
    total_steps: int
    draft: bool
    posts: List[PostResponse]
    asset_count: AssetCount

class CourseItem(BaseModel):
    id: Optional[PyObjectId] = Field(alias="id", default=None)
    course_name: Optional[str] = None
    brief: str
    updated_on: Optional[datetime] = None
    thumbnail: Optional[str] = None
    category: Optional[str]
    total_steps: Optional[int] = 0
    draft: Optional[bool]
    author: Optional[UserResponse] = None
    students: Optional[int] = 0
    posts: Optional[List[Post]] = None
    cost: Optional[float] = 0

class Post(BaseModel):
    # Define Post model attributes as needed
    pass

class Author(BaseModel):
    first_name: str
    last_name: str

    def full_name(self):
        return f"{self.first_name} {self.last_name}"


