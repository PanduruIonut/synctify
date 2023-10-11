from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    songs = relationship("Song", back_populates="owner")
    spotify_id = Column(String)
    name = Column(String)


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    artist = Column(String, index=True)
    album = Column(String, index=True)

    owner = relationship("User", back_populates="songs")
