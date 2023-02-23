import serial
import time
from flask import Flask, jsonify, request


# Interface with a Raspberry Pi Pico
class RIS:
    def __init__(self, port="/dev/ttyACM0", baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        try:
            self.ser = serial.Serial(self.port, self.baudrate)
        except:
            print("Could not connect to RIS - trying a different port")
            ports = ["/dev/ttyACM0", "/dev/ttyACM1"]
            failcount = 0
            for port in ports:
                try:
                    self.ser = serial.Serial(port, self.baudrate)
                    print("Connected to RIS on port %s" % port)
                    return
                except:
                    failcount += 1
                    print("Could not connect to RIS on port %s" % port)
            if failcount == len(ports):
                raise Exception("Could not connect to RIS")


    def send(self, data):
        assert type(data) == dict, "Data must be a dictionary"
        string_repr = str(data)
        self.ser.write(b"%s\n" % string_repr.encode('utf-8'))
        time.sleep(0.1)

    def receive(self):
        return self.ser.readline().decode('utf-8')


ris = RIS()
# server will take in any commands and send it to the RIS
app = Flask(__name__)


@app.route("/health", methods=['POST'])
def health():
    return jsonify({"status": "OK"})


@app.route("/ris", methods=['POST'])
def ris_comm():
    command_data_json = request.get_json()
    ris.send(command_data_json)
    # wait for confirmation
    return jsonify({"status": "OK"})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5075)
