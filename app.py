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
        
        # Используем твою находку: ynison_state()
        # Этот метод возвращает актуальное состояние синхронизации всех устройств
        ynison_data = client.ynison_state()
        
        track = None
        is_playing = False
        
        # Ynison содержит список активных сессий/очередей
        # Мы ищем устройство, которое сейчас активно проигрывает музыку
        if ynison_data and ynison_data.device_state:
            # Перебираем устройства (обычно активное устройство одно)
            for device_id, state in ynison_data.device_state.items():
                # Проверяем, есть ли в состоянии очередь
                if state.queue and state.queue.current_index is not None:
                    # Получаем текущий трек из очереди
                    # state.queue.tracks — это список, берем по индексу
                    current_idx = state.queue.current_index
                    if current_idx < len(state.queue.tracks):
                        track_item = state.queue.tracks[current_idx]
                        
                        # fetch_track() обычно нужен, если это ссылка/ID
                        # Если объект уже содержит данные (как в Ynison), пробуем напрямую
                        track = track_item.fetch_track()
                        
                        # Проверяем статус воспроизведения через PlayingStatus
                        # (Обычно 1 — это Playing, 2 — Paused, зависит от реализации)
                        if state.playing_status == 'playing':
                            is_playing = True
                        
                        print(f"DEBUG: Трек найден через Ynison State: {track.title}")
                        break # Нашли активное устройство, выходим из цикла

        # Если через Ynison ничего не нашли (например, музыка стоит на паузе давно)
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