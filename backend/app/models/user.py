from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    bio = Column(Text, nullable=True)
    support_badges = Column(String, nullable=True)
    profile_photo_url = Column(String, nullable=True)
    strike_count = Column(Integer, default=0)
    last_strike_at = Column(DateTime(timezone=True), nullable=True)
    moderation_notes = Column(Text, nullable=True)

    scans = relationship("Scan", back_populates="owner", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan", foreign_keys="Post.user_id")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan", foreign_keys="Comment.user_id")
    appointments = relationship("Appointment", back_populates="user", cascade="all, delete-orphan")
    reactions = relationship("PostReaction", back_populates="user", cascade="all, delete-orphan")
