STATE = {}

def set_state(user_id, data):
    STATE[user_id] = data

def get_state(user_id):
    return STATE.get(user_id, {
        "title": "",
        "artist": "",
        "coverUrl": "",
        "link": "",
        "isPlaying": False
    })