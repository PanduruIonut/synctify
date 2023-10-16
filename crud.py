from sqlalchemy.orm import Session

from models import User, Song
from schemas import UserCreate, SongCreate
from typing import List
from models import PlaylistCreationHistory



def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_spotify_id(db: Session, id: str):
    return db.query(User).filter(User.spotify_id == id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user_data: UserCreate, access_token: str, refresh_token: str, expires_in:str):
   user_dict = user_data.model_dump()
   user = User(**user_dict, access_token=access_token, refresh_token=refresh_token, expires_in=expires_in)
   db.add(user)
   db.commit()
   db.refresh(user)
   return user

def get_songs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Song).offset(skip).limit(limit).all()


def create_user_song(db: Session, song: SongCreate, user_id: int):
    db_song = Song(**song.dict(), owner_id=user_id)
    db.add(db_song)
    db.commit()
    db.refresh(db_song)
    return db_song

def get_song_by_details(db: Session, title: str, artist: str):
    return db.query(Song).filter(Song.title == title, Song.artist == artist).first()

def create_song(db: Session, title: str, artist: str, album_name: str, preview_url: str, images: List[str], added_at: str, lang: str):
    db_song = Song(title=title, artist=artist, album=album_name, preview_url= preview_url, images=images, added_at=added_at, lang=lang)
    db.add(db_song)
    db.commit()
    db.refresh(db_song)
    return db_song

def get_liked_songs_for_user(db: Session, user_id: int):
    user = db.query(User).filter(User.spotify_id == user_id).first()

    if user:
        liked_songs = user.songs
        return liked_songs
    else:
        return None

def create_playlist_creation_history(db: Session, user_id: int):
    playlist_history = PlaylistCreationHistory(user_id=user_id)
    db.add(playlist_history)
    db.commit()
    db.refresh(playlist_history)
    return playlist_history

def get_playlist_creation_history(db: Session, user_id: int):
    return db.query(PlaylistCreationHistory).filter(PlaylistCreationHistory.user_id == user_id).all()

def latest_playlist_entry(db: Session, user_id: str):
    return db.query(PlaylistCreationHistory).filter(PlaylistCreationHistory.user_id == user_id).order_by(PlaylistCreationHistory.created_at.desc()).first()

def get_tokens_by_spotify_id(db: Session, spotify_id: str):
    user = db.query(User).filter(User.spotify_id == spotify_id).first()
    if user:
        return user.access_token, user.refresh_token
    return None, None
