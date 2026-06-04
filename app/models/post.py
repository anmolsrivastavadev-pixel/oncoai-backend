from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    category = Column(String, index=True)
    image_url = Column(String, nullable=True)
    is_flagged = Column(Boolean, default=False, index=True)
    flag_reason = Column(Text, nullable=True)
    flagged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_hidden = Column(Boolean, default=False)
    pinned = Column(Boolean, default=False)
    group_id = Column(Integer, ForeignKey("community_groups.id"), nullable=True)
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="posts", foreign_keys=[user_id])
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    reactions = relationship("PostReaction", back_populates="post", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    is_flagged = Column(Boolean, default=False)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))

    author = relationship("User", back_populates="comments", foreign_keys=[user_id])
    post = relationship("Post", back_populates="comments")
