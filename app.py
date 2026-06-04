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
        
        # Переменные для финального ответа
        track = None
        is_playing = False
        
        # МЕТОД 1: Пробуем получить через активную очередь (Ynison)
        try:
            queues = client.queues_list()
            if queues:
                last_queue = client.queue(queues[0].id)
                current_index = last_queue.current_index
                if current_index is not None and current_index < len(last_queue.tracks):
                    track_item = last_queue.tracks[current_index]
                    track = track_item.fetch_track()
                    is_playing = True
                    print(f"DEBUG: Трек найден через QUEUE (Ynison): {track.title}")
        except Exception as q_err:
            print(f"DEBUG: Ошибка при чтении очереди: {q_err}")

        # МЕТОД 2: Если очередь пуста, лезем в Историю Прослушиваний (Работает ВСЕГДА)
        if not track:
            try:
                history = client.users_play_histories()
                if history:
                    # Берем самый первый (последний запущенный) трек из истории
                    latest_history_item = history[0]
                    track = latest_history_item.track
                    is_playing = True # В истории всегда true для отображения, либо можно симулировать
                    print(f"DEBUG: Трек найден через HISTORY: {track.title}")
            except Exception as h_err:
                print(f"DEBUG: Ошибка при чтении истории: {h_err}")

        # Если трек так и не нашли (аккаунт вообще пустой)
        if not track:
            return jsonify({"title": "", "artist": "", "coverUrl": "", "isPlaying": False, "link": ""})
            
        # Формируем красивый ответ
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