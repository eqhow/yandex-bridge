from flask import Flask, request, jsonify
from yandex_music import Client
import traceback

app = Flask(__name__)

# Добавь этот маршрут, чтобы Render не перезагружал сервер
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
        
        # --- БЛОК ВЕРИФИКАЦИИ ---
        uid_from_token = client.me.account.uid
        print(f"DEBUG: Token belongs to UID: {uid_from_token}")
        
        # Запрашиваем лайки пользователя для 100% подтверждения аккаунта
        likes = client.users_likes_tracks()
        likes_count = len(likes) if likes else 0
        print(f"DEBUG: [VERIFY] Account has {likes_count} liked tracks.")
        
        if likes_count > 0:
            # Получаем метаданные первого лайкнутого трека для проверки
            first_liked_track = likes[0].fetch_track()
            artists = ", ".join(a.name for a in first_liked_track.artists)
            print(f"DEBUG: [VERIFY] First liked track is: '{first_liked_track.title}' by {artists}")
        else:
            print("DEBUG: [VERIFY] Account has NO liked tracks (Is this a brand new account?)")
        # ------------------------

        # ОТЛАДКА: посмотрим, что вообще возвращает сервер (очереди проигрывания)
        queues = client.queues_list()
        print(f"DEBUG: Queues found: {queues}") 
        
        if not queues:
            print("DEBUG: No active queues found. (Check if music is playing on the SAME account and device is syncing!)")
            return jsonify({"title": "", "artist": "", "coverUrl": "", "isPlaying": False, "link": ""})
            
        last_queue = client.queue(queues[0].id)
        print(f"DEBUG: Active queue ID: {queues[0].id}")
        current_index = last_queue.current_index
        
        if current_index is None or current_index >= len(last_queue.tracks):
            return jsonify({"title": "", "artist": "", "coverUrl": "", "isPlaying": False, "link": ""})
            
        track_item = last_queue.tracks[current_index]
        track = track_item.fetch_track()
        
        cover_url = ""
        if track.cover_uri:
            cover_url = "https://" + track.cover_uri.replace('%%', '400x400')
            
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
        traceback.print_exc()  # Печатает подробный лог ошибки, если что-то упадет
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)