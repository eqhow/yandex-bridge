from flask import Flask, request, jsonify
from yandex_music import Client
from yandex_music.ynison import simple
import traceback

app = Flask(__name__)

# ИСПРАВЛЕНИЕ: Добавляем корневой маршрут для health check
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

        # 1. Пытаемся получить текущий трек через простой интерфейс
        try:
            state = simple.get_state(token)
            if state and state.devices:
                # Ищем активное устройство с текущим треком
                for device in state.devices:
                    if device.state and device.state.queue and device.state.queue.current_index is not None:
                        current_idx = device.state.queue.current_index
                        if current_idx < len(device.state.queue.tracks):
                            track_item = device.state.queue.tracks[current_idx]
                            track = track_item.fetch_track() if hasattr(track_item, 'fetch_track') else track_item

                            # Проверяем статус воспроизведения
                            status = getattr(device.state, 'playing_status', None)
                            if status and hasattr(status, 'value'):
                                is_playing = status.value == 'playing'
                            elif status:
                                is_playing = status == 'playing'

                            print(f"DEBUG: Трек из get_state: {track.title if hasattr(track, 'title') else 'unknown'}, playing={is_playing}")
                            break
        except Exception as e:
            print(f"DEBUG: Ошибка get_state: {e}")

        # 2. Если нет текущего трека, берём последний из истории
        if not track:
            try:
                history = client.music_history()
                if history and len(history) > 0:
                    latest_event = history[0]
                    track = latest_event.track
                    is_playing = False
                    print(f"DEBUG: Трек из истории: {track.title if hasattr(track, 'title') else 'unknown'}")
            except Exception as e:
                print(f"DEBUG: Ошибка истории: {e}")

        # 3. Если трека нет вообще
        if not track:
            return jsonify({"title": "", "artist": "", "coverUrl": "", "isPlaying": False, "link": ""})

        # 4. Извлекаем все необходимые данные
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