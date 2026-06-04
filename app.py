from flask import Flask, request, jsonify
from yandex_music import Client
from datetime import datetime, timezone
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
        
        # МЕТОД 1: Пытаемся поймать живую очередь (Ynison)
        try:
            queues = client.queues_list()
            if queues:
                last_queue = client.queue(queues[0].id)
                current_index = last_queue.current_index
                if current_index is not None and current_index < len(last_queue.tracks):
                    track_item = last_queue.tracks[current_index]
                    track = track_item.fetch_track()
                    is_playing = True
                    print(f"DEBUG: Трек найден через активную QUEUE: {track.title}")
        except Exception as q_err:
            print(f"DEBUG: Ошибка при чтении очереди: {q_err}")

        # МЕТОД 2: Твоя идея с 10-минутным таймером истории (ИСПРАВЛЕНО НА users_play_history)
        if not track:
            try:
                history = client.users_play_history()
                if history:
                    latest_history_item = history[0]
                    
                    # Получаем время, когда трек был включен
                    track_time = latest_history_item.timestamp
                    
                    # Приводим к правильному формату datetime, если библиотека вернула строку
                    if not isinstance(track_time, datetime):
                        track_time = datetime.fromisoformat(str(track_time).replace('Z', '+00:00'))
                    
                    # Считаем разницу с текущим временем сервера
                    now = datetime.now(timezone.utc)
                    time_diff_minutes = (now - track_time).total_seconds() / 60
                    
                    print(f"DEBUG: Последний трек из истории включен {time_diff_minutes:.1f} мин. назад")
                    
                    # Если трек включили менее 10 минут назад — считаем, что музыка ИГРАЕТ
                    if time_diff_minutes <= 10:
                        track = latest_history_item.track
                        is_playing = True
                        print(f"DEBUG: Трек признан активным через HISTORY: {track.title}")
                    else:
                        print(f"DEBUG: Трек из истории слишком старый ({time_diff_minutes:.1f} мин). Плеер считается выключенным.")
            except Exception as h_err:
                print(f"DEBUG: Ошибка при расчете времени истории: {h_err}")

        # Если трек не найден или время вышло — отдаем пустой ответ (дизайн не ломается)
        if not track:
            return jsonify({"title": "", "artist": "", "coverUrl": "", "isPlaying": False, "link": ""})
            
        # Собираем данные для Swift
        cover_url = ""
        if track.cover_uri:
            cover_url = "https://" + track.cover_uri.replace('%%', '400x400')
            
        response = {
            "title": track.title,
            "artist": ", ".join(artist.name for artist in track.artists) if track.artists else "Unknown Artist",
            "coverUrl": cover_url,
            "isPlaying": is_playing,
            "link": f"https://music.yandex.ru/track/{track.id}" if track.id else ""
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)