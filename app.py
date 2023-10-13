from datetime import datetime
import json
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi import Response
from json import JSONDecodeError
from fastapi.responses import JSONResponse

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from  crud import get_user_by_spotify_id, create_user, get_liked_songs_for_user, create_song, get_song_by_details, get_songs, get_users, get_user, latest_playlist_entry
from models import Base, PlaylistCreationHistory
from schemas import User, UserCreate, Song, SongCreate
from database import SessionLocal, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/user/liked_songs/{user_id}")
async def get_liked_songs(user_id: str, db: Session = Depends(get_db)):
    liked_songs = get_liked_songs_for_user(db, user_id)
    
    if liked_songs:
        liked_songs_data = [
            {
                "id": song.id,
                "title": song.title,
                "artist": song.artist,
                "album": song.album,
                "preview_url": song.preview_url,
                "images": json.loads(song.images),
                "added_at": datetime.strptime(song.added_at, "%Y-%m-%dT%H:%M:%SZ").strftime("%-d %b %Y"),
            }
            for song in liked_songs
        ]
        
        latest_entry = latest_playlist_entry(db, user_id)
        if latest_entry:
            last_synced =             last_synced = datetime.strptime(latest_entry.created_at, "%Y-%m-%dT%H:%M:%S.%f").strftime("%-d %b %Y %H:%M:%S")
        else:
            last_synced = "N/A"
        return JSONResponse(content={"liked_songs": liked_songs_data, "last_synced": last_synced})
    else:
        return JSONResponse(content={"message": "User not found or has no liked songs"}, status_code=404)

@app.post('/callback')
async def callback(request: Request, response: Response):
    try:
        data = await request.json()
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    code = data.get('code')
    CLIENT_ID = data.get('client_id')
    CLIENT_SECRET = data.get('client_secret')
    REDIRECT_URI = data.get('redirect_uri')

    auth_url = 'https://accounts.spotify.com/api/token'
    auth_response = requests.post(auth_url, {
        'grant_type': 'authorization_code',
        'scope': 'user-top-read',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    })

    auth_response_data = auth_response.json()
    print(auth_response_data)
    access_token = auth_response_data['access_token']
    if access_token:
        response.status_code = 200
    else:
        response.status_code = 500
    return access_token


@app.post('/me')
async def getCurrentUser(request: Request, response: Response):
    try:
        data = await request.json()
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    access_token = data.get('access_token')

    if not access_token:
        raise HTTPException(status_code=400, detail='Access token not found. Please authorize the app first.')

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    spotify_response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    if spotify_response.status_code == 200:
        response_data = spotify_response.json()
        return response_data
    else:
        raise HTTPException(status_code=spotify_response.status_code, detail='Failed to fetch Spotify data')


@app.post('/create_playlist')
async def create_playlist(request: Request, response: Response):
    try:
        data = await request.json()
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    access_token = data.get('access_token')

    if not access_token:
        raise HTTPException(status_code=400, detail='Access token not found. Please authorize the app first.')

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    me_response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    user_email = me_response.json().get('email')
    spotify_id = me_response.json().get('id')
    name = me_response.json().get('display_name')

    db = next(get_db())
    try:
        user = get_user_by_spotify_id(db, spotify_id)
        if not user:
            user_data = UserCreate(email=user_email, spotify_id=spotify_id, name=name)
            user = create_user(db, user_data)
            db.commit()
        all_liked_songs = []
        offset = 0
        limit = 50
        while True:
            endpoint_liked_songs = f'https://api.spotify.com/v1/me/tracks?limit={limit}&offset={offset}'
            response_liked_songs = requests.get(endpoint_liked_songs, headers=headers)
            liked_songs = response_liked_songs.json().get('items', [])

            if not liked_songs:
                break

            all_liked_songs.extend(liked_songs)
            offset += limit

        for song in all_liked_songs:
            title = song['track']['name']
            artist = song['track']['artists'][0]['name']
            album = song['track']['album']['name']
            preview_url = song['track']['preview_url']
            images = song['track']['album']['images']
            added_at = song['added_at']

            image_urls = [entry["url"] for entry in images]

            image_urls_json = json.dumps(image_urls)
            existing_song = get_song_by_details(db, title, artist)

            if not existing_song:
                db_song = create_song(db=db, title=title, artist=artist, album_name=album, preview_url=preview_url, images=image_urls_json, added_at=added_at)
                user.songs.append(db_song)

        db.commit()

        track_uris = [item['track']['uri'] for item in all_liked_songs]

        endpoint_create_playlist = f'https://api.spotify.com/v1/me/playlists'
        data = {
            'name': 'Liked Songs Playlist',
            'public': False
        }
        response_create_playlist = requests.post(endpoint_create_playlist, headers=headers, json=data)
        playlist_id = response_create_playlist.json()['id']

        endpoint_add_tracks = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'

        # Split track_uris into chunks of 100 tracks (the maximum number of tracks that can be added per request)
        track_uris_chunks = [track_uris[x:x + 100] for x in range(0, len(track_uris), 100)]
        for chunk in track_uris_chunks:
            data = {'uris': chunk}
            response_add_tracks = requests.post(endpoint_add_tracks, headers=headers, json=data)

        playlist_history_entry = PlaylistCreationHistory(user_id=user.spotify_id)
        db.add(playlist_history_entry)
        db.commit()
        return {'message': 'Playlist created with liked songs!'}
    finally:
        db.close()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
