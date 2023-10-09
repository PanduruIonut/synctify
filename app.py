import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi import Response
from json import JSONDecodeError
from fastapi.responses import JSONResponse

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
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    })

    auth_response_data = auth_response.json()
    access_token = auth_response_data['access_token']
    if access_token:
        response.status_code = 200
    else:
        response.status_code = 500
    return access_token

@app.get('/test')
async def test():
    return {'message': 'This is a test endpoint.'}

@app.get('/create_playlist')
async def create_playlist():
    # Simulate the authorization process
    # In your Vue.js project, you would handle the Spotify authorization flow

    # Replace this with your actual code to obtain the access token
    access_token = 'YOUR_ACCESS_TOKEN'

    if not access_token:
        raise HTTPException(status_code=400, detail='Access token not found. Please authorize the app first.')

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Get all the user's liked songs (handle pagination)
    all_liked_songs = []
    offset = 0
    limit = 50
    while True:
        endpoint_liked_songs = f'https://api.spotify.com/v1/me/tracks?limit={limit}&offset={offset}'
        response_liked_songs = requests.get(endpoint_liked_songs, headers=headers)
        liked_songs = response_liked_songs.json()['items']

        if not liked_songs:
            break

        all_liked_songs.extend(liked_songs)
        offset += limit

    # Extract track URIs from all liked songs
    track_uris = [item['track']['uri'] for item in all_liked_songs]

    # Create a new playlist with the liked songs
    endpoint_create_playlist = f'https://api.spotify.com/v1/me/playlists'
    data = {
        'name': 'Liked Songs Playlist',
        'public': False  # Change to True if you want the playlist to be public
    }
    response_create_playlist = requests.post(endpoint_create_playlist, headers=headers, json=data)
    playlist_id = response_create_playlist.json()['id']

    # Add liked songs to the playlist
    endpoint_add_tracks = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'

    # Split track_uris into chunks of 100 tracks (the maximum number of tracks that can be added per request)
    track_uris_chunks = [track_uris[x:x+100] for x in range(0, len(track_uris), 100)]
    for chunk in track_uris_chunks:
        data = {'uris': chunk}
        response_add_tracks = requests.post(endpoint_add_tracks, headers=headers, json=data)

    return {'message': 'Playlist created with liked songs!'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
