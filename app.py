from flask import Flask, request, jsonify
from yandex_music import Client
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
        
        # 1. Попытка через Ynison State
        track = None
        is_playing = False
        
        try:
            ynison_data = client.ynison_state()
            # Проверяем, есть ли данные о состоянии устройств
            if ynison_data and hasattr(ynison_data, 'device_state') and ynison_data.device_state:
                for device_id, state in ynison_data.device_state.items():
                    # Проверяем наличие очереди
                    if state.queue and state.queue.current_index is not None:
                        current_idx = state.queue.current_index
                        if current_idx < len(state.queue.tracks):
                            track_item = state.queue.tracks[current_idx]
                            track = track_item.fetch_track()
                            
                            # Проверяем статус (playing или paused)
                            # У ynison playing_status часто возвращает объект, проверяем его значение
                            status = getattr(state, 'playing_status', None)
                            if status and hasattr(status, 'value') and status.value == 'playing':
                                is_playing = True
                            
                            print(f"DEBUG: Успешно через Ynison: {track.title}")
                            break
        except Exception as e:
            print(f"DEBUG: Ошибка в логике Ynison: {e}")

        # 2. Если Ynison пуст, пробуем Fallback: Последний прослушанный трек через history
        if not track:
            try:
                # Используем твою находку - music_history()
                history = client.music_history()
                if history and len(history) > 0:
                    latest_event = history[0]
                    track = latest_event.track
                    is_playing = False # Из истории мы знаем только факт прослушивания
                    print(f"DEBUG: Трек подхвачен из History: {track.title}")
            except Exception as e:
                print(f"DEBUG: Ошибка в логике History: {e}")

        # Финальная проверка
        if not track:
            return jsonify({"title": "", "artist": "", "coverUrl": "", "isPlaying": False, "link": ""})

        # Формируем ответ
        cover_url = ""
        if track.cover_uri:
            # Заменяем плейсхолдер %% на нужный размер
            cover_url = "https://" + track.cover_uri.replace('%%', '400x400')

        return jsonify({
            "title": track.title,
            "artist": ", ".join(artist.name for artist in track.artists) if track.artists else "Unknown Artist",
            "coverUrl": cover_url,
            "isPlaying": is_playing,
            "link": f"https://music.yandex.ru/track/{track.id}" if track.id else ""
        })

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        # traceback.print_exc() # Можно закомментировать в проде, чтобы не засорять логи
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)