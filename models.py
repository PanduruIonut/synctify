import datetime
import json
from click import DateTime
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
    playlist_history = relationship("PlaylistCreationHistory", back_populates="user")
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    expires_in = Column(String, nullable=True)



class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    artist = Column(String, index=True)
    album = Column(String, index=True)
    preview_url= Column(String)
    images=Column(String)
    added_at= Column(String)
    lang= Column(String)

    owner = relationship("User", back_populates="songs")

    def set_images(self, images):
        self.images = json.dumps(images)

    def get_images(self):
        return json.loads(self.images) if self.images else []


class PlaylistCreationHistory(Base):
    __tablename__ = "playlist_creation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(String, default=datetime.datetime.now().isoformat()) 
    user = relationship("User", back_populates="playlist_history")