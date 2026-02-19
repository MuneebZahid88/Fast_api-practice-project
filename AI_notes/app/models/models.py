from sqlalchemy import Column, Integer, String, TIMESTAMP, text, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    create_at = Column( TIMESTAMP(timezone=True),nullable=False,server_default=text("NOW()"))
    role = Column(String, nullable=False, default="User")

    # ✅ relationship with cascade delete
    notes = relationship( "Notes",back_populates="user",cascade="all, delete",passive_deletes=True)


class Notes(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    create_at = Column(TIMESTAMP(timezone=True),nullable=False,server_default=text("NOW()"))

    user_id = Column(Integer,ForeignKey("users.id", ondelete="CASCADE"),nullable=False)

    # ✅ relationship back to user
    user = relationship("User",back_populates="notes")
