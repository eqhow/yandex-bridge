from flask import Flask, request, jsonify
from yandex_music import Client
import traceback

app = Flask(__name__)

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

        # 1. Попытка через Ynison (Самый приоритетный метод для "Сейчас играет")
        try:
            # Получаем список очередей через Ynison
            queues = client.queues_list()
            if queues:
                # Берем последнюю активную очередь
                last_queue = client.queue(queues[0].id)
                # Если очередь активна и там есть трек
                if last_queue.current_index is not None:
                    track = last_queue.tracks[last_queue.current_index].fetch_track()
                    is_playing = True
                    print(f"DEBUG: Трек найден через Ynison: {track.title}")
        except Exception as e:
            print(f"DEBUG: Ynison не вернул активный трек: {e}")

        # 2. Если Ynison пуст (музыка стоит на паузе или не синхронизировалась), 
        # используем твою находку - music_history()
        if not track:
            try:
                # Используем правильный метод из твоей ссылки
                history = client.music_history()
                if history:
                    # history возвращает список событий. Берем самое последнее.
                    latest_event = history[0]
                    track = latest_event.track
                    is_playing = False # Из истории мы знаем только то, что играло, а не играет сейчас
                    print(f"DEBUG: Трек найден через Music History: {track.title}")
            except Exception as e:
                print(f"DEBUG: Ошибка при чтении Music History: {e}")

        if not track:
            return jsonify({"title": "", "artist": "", "coverUrl": "", "isPlaying": False, "link": ""})

        # Формируем ответ
        cover_url = ""
        if track.cover_uri:
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
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)