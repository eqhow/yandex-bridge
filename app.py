from flask import Flask, request, jsonify
from yandex_music import Client

app = Flask(__name__)

@app.route('/now-playing', methods=['GET'])
def get_now_playing():
    token = request.args.get('token')
    
    if not token:
        return jsonify({"error": "No token provided"}), 400

    try:
        client = Client(token).init()
        
        queues = client.queues_list()
        
        if not queues:
            return jsonify({"isPlaying": False})
            
        last_queue = client.queue(queues[0].id)
        
        current_index = last_queue.current_index
        if current_index is None or not last_queue.tracks:
            return jsonify({"isPlaying": False})
            
        track_item = last_queue.tracks[current_index]
        track = track_item.fetch_track()
        
        cover_url = ""
        if track.cover_uri:
            cover_url = "https://" + track.cover_uri.replace('%%', '400x400')
            
        response = {
            "track": track.title,
            "artist": ", ".join(artist.name for artist in track.artists),
            "image": cover_url,
            "isPlaying": True,
            "externalURL": f"https://music.yandex.ru/track/{track.id}"
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)