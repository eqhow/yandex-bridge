from flask import Flask, request, jsonify
from yandex_music import Client
import traceback

app = Flask(__name__)

@app.route('/', methods=['GET'])
def health_check():
    return "Service is online", 200

@app.route('/api/now-playing/<uid>', methods=['GET'])
def get_now_playing(uid):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "No valid token provided"}), 401

    token = auth_header.split(" ")[1]

    try:
        client = Client(token).init()
        track = None
        is_playing = False

        # Получаем последний прослушанный трек из истории
        try:
            history = client.music_history()
            if history and history.events:
                # MusicHistory.events - это список событий
                latest_event = history.events[0]
                track = latest_event.track
                is_playing = False  # Из истории мы не можем узнать, играет ли сейчас
                print(f"DEBUG: Трек из истории: {track.title}")
        except Exception as e:
            print(f"DEBUG: Ошибка получения истории: {e}")
            traceback.print_exc()

        # Если трека нет вообще
        if not track:
            return jsonify({
                "title": "",
                "artist": "",
                "coverUrl": "",
                "isPlaying": False,
                "link": ""
            })

        # Извлекаем все необходимые данные
        cover_url = ""
        if hasattr(track, 'cover_uri') and track.cover_uri:
            cover_url = "https://" + track.cover_uri.replace('%%', '400x400')

        artist_name = ""
        if hasattr(track, 'artists') and track.artists:
            artist_name = ", ".join(artist.name for artist in track.artists)

        title = track.title if hasattr(track, 'title') else ""
        track_id = track.id if hasattr(track, 'id') else None

        return jsonify({
            "title": title,
            "artist": artist_name or "Unknown Artist",
            "coverUrl": cover_url,
            "isPlaying": is_playing,
            "link": f"https://music.yandex.ru/track/{track_id}" if track_id else ""
        })

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)