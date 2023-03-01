import requests

asa_server = "http://127.0.0.1:5090"


def call_asa_server(data):
    try:
        asaresp = requests.post(asa_server + "/asa", json=data)
        print(asaresp.status_code, asaresp.text)
        print(asaresp.json())
    except Exception as e:
        print(e)
        return {"error": "failed to send data"}
