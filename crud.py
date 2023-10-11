from sqlalchemy.orm import Session

from models import User, Song
from schemas import UserCreate, SongCreate


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_spotify_id(db: Session, id: str):
    return db.query(User).filter(User.spotify_id == id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate):
    db_user = User(email=user.email, spotify_id=user.spotify_id, name = user.name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


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

def create_song(db: Session, title: str, artist: str, album_name: str):
    db_song = Song(title=title, artist=artist, album=album_name)
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