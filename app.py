import os
import requests
from flask_cors import CORS, cross_origin, jsonify
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Replace 'YOUR_CLIENT_ID' and 'YOUR_CLIENT_SECRET' with your own values.
CLIENT_ID = ''
CLIENT_SECRET = ''
REDIRECT_URI = 'http://127.0.0.1:8000/callback'  # Replace with your desired Redirect URI

@app.route('/test')
@cross_origin()
def test():
    return "test"

@app.route('/')
def home():
    # Redirect the user to Spotify authorization page
    auth_url = f'https://accounts.spotify.com/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=user-library-read playlist-modify-public playlist-modify-private'
    return redirect(auth_url)

@app.route('/callback')
def callback():
    # Get the authorization code from the query parameters
    code = request.args.get('code')

    # Exchange the authorization code for an access token
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

    # Save the access token in the session for later use
    session['access_token'] = access_token

    return redirect('/create_playlist')

@app.route('/create_playlist')
def create_playlist():
    access_token = session.get('access_token')
    if not access_token:
        return 'Access token not found. Please authorize the app first.'

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

    # split track_uris into chunks of 100 tracks (the maximum number of tracks that can be added per request)
    track_uris_chunks = [track_uris[x:x+100] for x in range(0, len(track_uris), 100)]
    for chunk in track_uris_chunks:
        data = {'uris': chunk}
        response_add_tracks = requests.post(endpoint_add_tracks, headers=headers, json=data)

    return 'Playlist created with liked songs!'

if __name__ == '__main__':
    app.run(port=8000, debug=True)
