from flask import Flask, request, jsonify
from yandex_music import Client

app = Flask(__name__)

# Маршрут должен быть /api/now-playing/<uid>, как в твоем Swift-коде
@app.route('/api/now-playing/<uid>', methods=['GET'])
def get_now_playing(uid):
    # Получаем токен из заголовка Authorization: Bearer <token>
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "No valid token provided"}), 401
    
    token = auth_header.split(" ")[1]

    try:
        # Инициализируем клиент
        client = Client(token).init()
        
        # Получаем список очередей (сессий)
        queues = client.queues_list()
        
        if not queues:
            return jsonify({"title": "", "artist": "", "coverUrl": "", "isPlaying": False, "link": ""})
            
        # Берем самую актуальную очередь
        last_queue = client.queue(queues[0].id)
        
        current_index = last_queue.current_index
        # Проверка на существование трека
        if current_index is None or current_index >= len(last_queue.tracks):
            return jsonify({"title": "", "artist": "", "coverUrl": "", "isPlaying": False, "link": ""})
            
        track_item = last_queue.tracks[current_index]
        track = track_item.fetch_track()
        
        cover_url = ""
        if track.cover_uri:
            cover_url = "https://" + track.cover_uri.replace('%%', '400x400')
            
        # Эти ключи теперь полностью соответствуют твоему Swift-декодеру
        response = {
            "title": track.title,
            "artist": ", ".join(artist.name for artist in track.artists),
            "coverUrl": cover_url,
            "isPlaying": True,
            "link": f"https://music.yandex.ru/track/{track.id}"
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)