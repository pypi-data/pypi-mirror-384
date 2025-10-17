"""Copyright 2024 Everlasting Systems and Solutions LLC (www.myeverlasting.net).
All Rights Reserved.

No part of this software or any of its contents may be reproduced, copied, modified or adapted, without the prior written consent of the author, unless otherwise indicated for stand-alone materials.

For permission requests, write to the publisher at the email address below:
office@myeverlasting.net

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
from espy_contact.util.db import Base
from sqlalchemy import Column, DateTime,ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Integer, String
from espy_contact.util.db import Base
from sqlalchemy import Column, DateTime,JSON
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import Integer, String
class Message(Base):
    """Model for in-app messaging."""
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey('appusers.id'), nullable=False)
    recipient_id = Column(Integer, nullable=False)
    recipient_type = Column(String, nullable=False)
    content = Column(JSON)
    event_type = Column(String)
    created_at = Column(DateTime(), server_default=func.now())
    updated_at = Column(DateTime(), server_default=func.now(), onupdate=func.now())

    sender = relationship("Appuser", foreign_keys=[sender_id])
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}