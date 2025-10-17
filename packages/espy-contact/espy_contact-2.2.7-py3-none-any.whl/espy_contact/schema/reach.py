"""Copyright 2024 Everlasting Systems and Solutions LLC (www.myeverlasting.net).
All Rights Reserved.

No part of this software or any of its contents may be reproduced, copied, modified or adapted, without the prior written consent of the author, unless otherwise indicated for stand-alone materials.

For permission requests, write to the publisher at the email address below:
office@myeverlasting.net

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
from typing import List,Optional
from datetime import datetime,date,timedelta
from decimal import Decimal
from pydantic import BaseModel,Field, EmailStr, ConfigDict
from espy_contact.schema.schema import AppuserDto,AddressDto
from espy_contact.util.enums import StatusEnum
class ProductBase(BaseModel):
    logo: str
    website: str
    ga_property_id: str
    socials: str
    cost: Decimal = Field(max_digits=10, decimal_places=2)
    expiry_date: Optional[datetime] = None
    note: str

class ProductCreate(ProductBase):
    pass
class Product(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int

class CustomerBase(BaseModel):
    pass

class CustomerCreate(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    business_name: str
    business_email: EmailStr
    contact_name: str
    contact_phone: str
    contact_email: EmailStr
    address: AddressDto

class Customer(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    staff: List[AppuserDto] = []
    products: List[Product] = []

class Campaign(BaseModel):
    id: Optional[int] = None
    title: str
    goals: Optional[str] = None
    target_audience: Optional[str] = None
    target_city: Optional[str] = None
    target_age_group: Optional[str] = None
    budget: float
    channels: Optional[str] = None
    ad_copy: Optional[str] = None
    expiry_date: datetime
    created_on: Optional[datetime]
    updated_on: Optional[datetime]
    note: Optional[str] = None
    product_id: int
    status: StatusEnum

class GaProperty(BaseModel):
    id: Optional[int] = None
    product_id: str
    start_date: Optional[date] = (datetime.now() - timedelta(weeks=30)).date()
    end_date: Optional[date] = datetime.now().date()