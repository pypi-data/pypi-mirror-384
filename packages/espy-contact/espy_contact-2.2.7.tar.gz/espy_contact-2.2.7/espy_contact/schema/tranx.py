"""Copyright 2024 Everlasting Systems and Solutions LLC (www.myeverlasting.net).
All Rights Reserved.

No part of this software or any of its contents may be reproduced, copied, modified or adapted, without the prior written consent of the author, unless otherwise indicated for stand-alone materials.

For permission requests, write to the publisher at the email address below:
office@myeverlasting.net

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

from datetime import datetime, date, timedelta
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field, PositiveFloat, model_validator
from espy_contact.util.enums import NigerianBank


class AccountDto(BaseModel):
    id: int | None = None
    bank: NigerianBank
    account_name: str
    account_number: str
    currency: str
    is_active: bool
    account_officer: str
    account_admin: str
    created: datetime
    modified: datetime


class PayStatusEnum(Enum):
    paid = "paid"
    overdue = "overdue"
    due = "due"


class FeeCreate(BaseModel):
    classroom_id: int | None = None
    fee_name: str
    amount: PositiveFloat
    category: str
    late_fee: float | None = None
    status: PayStatusEnum | None = Field(default=PayStatusEnum.due)
    due_date: date | None = Field(
        default_factory=lambda: (datetime.today() + timedelta(days=90)).date()
    )
    start_date: date | None = Field(default_factory=date.today)
    creator_id: int

    @model_validator(mode="after")
    def validate_fee(self) -> "FeeCreate":
        if self.category != "Optional" and self.classroom_id is None:
            raise ValueError("Classroom ID must be provided for non-optional fees")
        if self.category == "Optional" and self.classroom_id is not None:
            raise ValueError("Classroom ID must not be provided for optional fees")
        return self


class FeeDto(FeeCreate):
    id: int
    created_on: datetime | None = None
    modified_on: datetime | None = None


class FeeResponse(BaseModel):
    id: int
    classroom_id: int | None = None
    fee_name: str
    amount: PositiveFloat
    category: str
    late_fee: float | None = None
    status: PayStatusEnum
    due_date: date
    start_date: date
    creator_id: int
    created_on: datetime | None = None
    modified_on: datetime | None = None


class PaymentMethodBase(BaseModel):
    logo: str | None = "https://essluploads.s3.amazonaws.com/logo/credit_card.jpg"
    name: Literal["Paystack", "Transfer", "Stripe"] | None = None
    description: str | None = None
    payurl: str | None = None
    callback_url: str | None = None
    is_active: bool = True
    currency: str | None = None
    bank: str | None = None
    account_number: str | None = None
    account_name: str | None = None

    class Config:
        from_attributes = True


class PaymentMethodUpdate(PaymentMethodBase):
    id: int
    createdOn: datetime | None = None
    modifiedOn: datetime | None = None
    sub_account_code: str | None = None
