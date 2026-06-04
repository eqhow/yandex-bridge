from flask import Flask, request, jsonify
from yandex_music import Client
from yandex_music.ynison.client import YnisonClient
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

        # Получаем состояние Ynison через YnisonClient
        try:
            ynison_client = YnisonClient(client.user_info().account.uid, token)

            with ynison_client.session(timeout=5.0) as session:
                state = ynison_client.latest_state

                if state and state.devices:
                    # Ищем первое устройство с текущим треком в очереди
                    for device in state.devices:
                        if (device.state and
                            device.state.queue and
                            device.state.queue.current_index is not None):

                            current_idx = device.state.queue.current_index
                            tracks = device.state.queue.tracks

                            if current_idx < len(tracks):
                                track_item = tracks[current_idx]

                                # Получаем трек (может быть уже объект или нужно fetch)
                                if hasattr(track_item, 'fetch_track'):
                                    track = track_item.fetch_track()
                                else:
                                    track = track_item

                                # Получаем статус воспроизведения
                                playing_status = getattr(device.state, 'playing_status', None)
                                if playing_status:
                                    # Может быть объект с .value или строка
                                    if hasattr(playing_status, 'value'):
                                        is_playing = playing_status.value == 'playing'
                                    else:
                                        is_playing = str(playing_status).lower() == 'playing'

                                print(f"DEBUG: Трек из Ynison: {track.title if hasattr(track, 'title') else 'unknown'}, playing={is_playing}")
                                break

        except Exception as e:
            print(f"DEBUG: Ошибка Ynison: {e}")
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