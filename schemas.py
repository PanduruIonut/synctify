from pydantic import BaseModel
from typing import List


class SongBase(BaseModel):
    title: str
    description: str | None = None
    artists: List[str] | None = None
    album: str | None = None
    preview_url: str | None = None
    images: List[str] | None = None


class SongCreate(SongBase):
    pass


class Song(SongBase):
    id: int
    owner_id: int
    preview_url: str | None = None
    images: List[str] | None = None
    added_at: str | None = None

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: str | None = None
    songs: list[Song] = []
    name: str
    spotify_id: str



class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    email: str | None = None

    class Config:
        from_attributes = True
