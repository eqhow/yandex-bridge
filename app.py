from flask import Flask, request, jsonify
from yandex_music import Client
import traceback

app = Flask(__name__)


@app.route("/", methods=["GET"])
def health():
    return "ok", 200


@app.route("/api/now-playing/<uid>", methods=["GET"])
def now_playing(uid):
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({
            "error": "Token required"
        }), 401

    token = auth_header.replace("Bearer ", "")

    try:
        client = Client(token).init()

        queues = client.queues_list()

        if not queues:
            return jsonify({
                "title": "",
                "artist": "",
                "coverUrl": "",
                "link": "",
                "isPlaying": False
            })

        # Самая свежая очередь
        queue_item = queues[0]

        full_queue = client.queue(queue_item.id)

        current_track_id = full_queue.get_current_track()

        if not current_track_id:
            return jsonify({
                "title": "",
                "artist": "",
                "coverUrl": "",
                "link": "",
                "isPlaying": False
            })

        track = current_track_id.fetch_track()

        artists = ", ".join(
            artist.name for artist in track.artists
        ) if track.artists else ""

        cover_url = ""

        if track.cover_uri:
            cover_url = (
                "https://"
                + track.cover_uri.replace("%%", "400x400")
            )

        return jsonify({
            "title": track.title,
            "artist": artists,
            "coverUrl": cover_url,
            "link": f"https://music.yandex.ru/track/{track.id}",
            # queues_list не умеет определять play/pause
            "isPlaying": True
        })

    except Exception as e:
        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )