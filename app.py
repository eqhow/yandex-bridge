from flask import Flask, jsonify
from yandex_music import Client
import threading
import time

app = Flask(__name__)

STATE = {}

TOKEN = "YOUR_TOKEN"


def extract(track):
    artists = ", ".join(a.name for a in track.artists or [])

    cover = ""
    if track.cover_uri:
        cover = "https://" + track.cover_uri.replace("%%", "400x400")

    return {
        "title": track.title,
        "artist": artists,
        "coverUrl": cover,
        "link": f"https://music.yandex.ru/track/{track.id}",
    }


def ynison_worker():
    print("worker started")

    client = Client(TOKEN).init()
    last_id = None

    while True:
        try:
            state = client.ynison_state()

            if not state:
                time.sleep(2)
                continue

            for device_id, device_state in state.device_state.items():

                queue = device_state.queue
                if not queue:
                    continue

                idx = queue.current_index
                if idx is None:
                    continue

                track_item = queue.tracks[idx]
                track = track_item.fetch_track()

                if not track:
                    continue

                if track.id == last_id:
                    continue

                last_id = track.id

                STATE["me"] = {
                    **extract(track),
                    "isPlaying": str(device_state.playing_status).lower() == "playing"
                }

                print("UPDATED:", STATE["me"])

        except Exception as e:
            print("worker error:", e)

        time.sleep(2)


@app.route("/api/now-playing/<uid>")
def now_playing(uid):
    return jsonify(STATE.get(uid, {
        "title": "",
        "artist": "",
        "coverUrl": "",
        "link": "",
        "isPlaying": False
    }))


@app.route("/")
def health():
    return "ok"


if __name__ == "__main__":
    t = threading.Thread(target=ynison_worker, daemon=True)
    t.start()

    app.run(host="0.0.0.0", port=5000)