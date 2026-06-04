# worker.py

import time
from yandex_music import Client
from state import set_state

TOKEN = "USER_TOKEN"

def extract_track(track):
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


def run_worker():
    client = Client(TOKEN).init()

    last_track_id = None

    while True:
        try:
            state = client.ynison_state()

            if not state:
                time.sleep(2)
                continue

            # выбираем активное устройство
            for device_id, device_state in state.device_state.items():

                queue = device_state.queue
                if not queue:
                    continue

                current_index = queue.current_index
                tracks = queue.tracks

                if current_index is None or current_index >= len(tracks):
                    continue

                track_item = tracks[current_index]
                track = track_item.fetch_track()

                if not track:
                    continue

                # анти-спам (если трек не изменился)
                if last_track_id == track.id:
                    continue

                last_track_id = track.id

                data = extract_track(track)

                # play/pause
                status = getattr(device_state, "playing_status", None)
                is_playing = str(status).lower() == "playing"

                data["isPlaying"] = is_playing

                set_state("me", data)

                print("UPDATED:", data)

        except Exception as e:
            print("worker error:", e)

        time.sleep(2)


if __name__ == "__main__":
    run_worker()