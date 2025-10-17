"""Copyright 2024 Everlasting Systems and Solutions LLC (www.myeverlasting.net).
All Rights Reserved.

No part of this software or any of its contents may be reproduced, copied, modified or adapted, without the prior written consent of the author, unless otherwise indicated for stand-alone materials.

For permission requests, write to the publisher at the email address below:
office@myeverlasting.net

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
from espy_contact.util.db import Base
from espy_contact.model.models import Appuser
from espy_contact.util.enums import StatusEnum
from espy_contact.util.CONSTANTS import SCHEMA
from sqlalchemy import Column, Integer, String, ForeignKey,Table,Numeric,DateTime,Float,Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class Product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True, index=True)
    logo = Column(String)
    website = Column(String)
    ga_property_id = Column(String)
    cost = Column(Numeric(10,2))
    currency = Column(String)
    socials = Column(String) # comma seperated strings
    note = Column(String)
    expiry_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    customer_id = Column(Integer, ForeignKey("customer.id"))
    customer = relationship("Customer", back_populates="products")

customer_staff_association = Table(
    'customer_staff_association', Base.metadata,
    Column('customer_id', Integer, ForeignKey('customer.id')),
    Column('appuser_id', String, ForeignKey('appusers.id'))
)

class Customer(Base):
    __tablename__ = "customer"
    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String)
    business_email = Column(String) 
    contact_name = Column(String)
    contact_phone = Column(String)
    contact_email = Column(String)
    address_id = Column(String, ForeignKey("addresses.id"))
    address = relationship("Address")
    products = relationship("Product", back_populates="customer")

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    goals = Column(String)
    target_audience = Column(String)
    target_city = Column(String)
    target_age_group = Column(String)
    budget = Column(Float)
    channels = Column(String) #comma separated string
    ad_copy = Column(String)
    expiry_date = Column(DateTime)
    created_on = Column(DateTime,default=func.now())
    updated_on = Column(DateTime)
    note = Column(String)
    product_id = Column(Integer)
    status = Column(Enum(StatusEnum, schema=SCHEMA))

    assets = relationship("CampaignAsset", back_populates="campaign")

class CampaignAsset(Base):
    __tablename__ = "campaign_assets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String)
    created_on = Column(DateTime, default=func.now())
    updated_on = Column(DateTime)

    campaign = relationship("Campaign", back_populates="assets")
