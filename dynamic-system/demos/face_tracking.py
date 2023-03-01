import sys
import requests
import time


# sys.path.insert(0, '/home/blabs/Companion-Core/dynamic-system/core')
# from dynamic_library import dynamic
# dynamic = dynamic()
def get_face_data():
    # example: {'Brayden Levangie': [x1, y1, x2, y2]}
    video_server = "http://127.0.0.1:5050"
    try:
        face_data = requests.post(video_server + "/live").json()
        if face_data is None:
            return {"error": "no face"}
    except Exception as e:
        print(e)
        return {"error": "no frame"}
    # get closest face based on coordinates
    all_box_coordinates = list(face_data.values())
    if len(all_box_coordinates) == 0 or all_box_coordinates[0] == "no frame":
        return {"error": "no face"}
    closest_face = min(all_box_coordinates, key=lambda x: abs(x[0] - x[2]) * abs(x[1] - x[3]))
    closest_face_name = list(face_data.keys())[list(face_data.values()).index(closest_face)]
    # get center of closest face
    x1, y1, x2, y2 = closest_face
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    face_data["closest_face"] = {"X": int(center_x), "Y": int(center_y), "name": closest_face_name}
    return face_data


def send_tracking_data(data):
    X, Y = data["closest_face"]["X"], data["closest_face"]["Y"]
    ris_config = {"X": X, "Y": Y, "format": "axis", "resolution": [1920, 1080]}
    ris_server = "http://127.0.0.1:5075"
    try:
        requests.post(ris_server + "/ris", json=ris_config)
    except Exception as e:
        print(e)
        return {"error": "failed to send data"}


while 1:
    live_data = get_face_data()
    print(live_data)
    if "error" in live_data:
        continue
    send_tracking_data(live_data)
    # time.sleep(0.05)
