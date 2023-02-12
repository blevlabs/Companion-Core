"""
This script is the reciever for the RIS system. It is responsible for receiving data from the RIS server and controlling the robotic body for the Companion Core
"""

import time
import array
import math
import board
import audiobusio
import pwmio
import select
import sys
from adafruit_motor import servo


# Remove DC bias before computing RMS.
def mean(values):
    return sum(values) / len(values)


def normalized_rms(values):
    minbuf = int(mean(values))
    samples_sum = sum(
        float(sample - minbuf) * (sample - minbuf)
        for sample in values
    )

    return math.sqrt(samples_sum / len(values))


# Initalize the microphones (5pt Array)
mic = audiobusio.PDMIn(board.GP7, board.GP6, bit_depth=16)  # front center mic
mic2 = audiobusio.PDMIn(board.GP15, board.GP16, bit_depth=16)  # front left
mic3 = audiobusio.PDMIn(board.GP19, board.GP18, bit_depth=16)  # front right
mic4 = audiobusio.PDMIn(board.GP11, board.GP10, bit_depth=16)  # back left
mic5 = audiobusio.PDMIn(board.GP3, board.GP2, bit_depth=16)  # back right

samples = array.array('H', [0] * 160)  # initalize samples array for each mic
prevSerial = ""


def serial_read():
    if not select.select([sys.stdin, ], [], [], 0.0)[0]:
        return None
    serialData = sys.stdin.readline().strip()
    if serialData != None:
        return eval(serialData)


def serial_write(data):
    print(data)
    sys.stdout.flush()
    return


def setServoCycle(position, pwm):
    pwm.duty_u16(position)
    time.sleep(0.01)


# 0deg = 1000
# 180deg = 9000
def degrees_to_angle(degrees):
    return int((degrees / 180) * 8000 + 1000)


pwm1 = pwmio.PWMOut(board.GP22, duty_cycle=2 ** 15, frequency=50)  # head
servo1 = servo.Servo(pwm1)
pwm2 = pwmio.PWMOut(board.GP21, duty_cycle=2 ** 15, frequency=50)  # mid-arm
servo2 = servo.Servo(pwm2)
pwm3 = pwmio.PWMOut(board.GP26, duty_cycle=2 ** 15, frequency=50)  # mid
servo3 = servo.Servo(pwm3)
pwm4 = pwmio.PWMOut(board.GP27, duty_cycle=2 ** 15, frequency=50)  # base
servo4 = servo.Servo(pwm4)

s1_base_angle = 70  # head
s2_base_angle = 10
s3_base_angle = 180
s4_base_angle = 0  # base


def record_mics():
    mic.record(samples, len(samples))
    magnitude = normalized_rms(samples)
    mic2.record(samples, len(samples))
    magnitude2 = normalized_rms(samples)
    mic3.record(samples, len(samples))
    magnitude3 = normalized_rms(samples)
    mic4.record(samples, len(samples))
    magnitude4 = normalized_rms(samples)
    mic5.record(samples, len(samples))
    magnitude5 = normalized_rms(samples)
    location = {"Front_Center": magnitude, "Front_Left": magnitude2, "Front_Right": magnitude3, "Back_Left": magnitude4,
                "Back_Right": magnitude5}
    # find max magnitude
    max_mag = max(magnitude, magnitude2, magnitude3, magnitude4, magnitude5)
    # find location of max magnitude
    for key, value in location.items():
        if value == max_mag:
            location = key
    return f"{location}: {max_mag}"


def set_servos(s1_base_angle, s2_base_angle, s3_base_angle, s4_base_angle, **kwargs):
    servo1.angle = s1_base_angle
    servo2.angle = s2_base_angle
    servo3.angle = s3_base_angle
    servo4.angle = s4_base_angle


angle = 2


def tracker_calc(x_mid, y_mid, resolution, **kwargs):
    width, height = resolution[0], resolution[1]
    xpos, ypos = servo4.angle, servo1.angle
    while not x_mid - 10 < xpos < x_mid + 10:
        if x_mid > width / 2 + 30:
            xpos += angle
        if x_mid < width / 2 - 30:
            xpos -= angle
        if y_mid < height / 2 + 30:
            ypos -= angle
        if y_mid > height / 2 - 30:
            ypos += angle
        if xpos >= 180:
            xpos = 180
        elif xpos <= 0:
            xpos = 0
        if ypos >= 180:
            ypos = 180
        elif ypos <= 0:
            ypos = 0
        set_servos(s1_base_angle=xpos, s2_base_angle=32, s3_base_angle=180, s4_base_angle=ypos)


while True:
    data = serial_read()
    location_key = record_mics()
    if data is not None:
        if data["format"] == "servos":
            set_servos(**data)
            s1_base_angle = data["s1_base_angle"]
            s2_base_angle = data["s2_base_angle"]
            s3_base_angle = data["s3_base_angle"]
            s4_base_angle = data["s4_base_angle"]  # base
        elif data["format"] == "axis":
            tracker_calc(data["X"], data["Y"], data["resolution"])
    set_servos(s1_base_angle, s2_base_angle, s3_base_angle, s4_base_angle)
