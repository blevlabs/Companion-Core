import depthai as dai
import threading
import contextlib
import cv2
import time
from PIL import Image

from face_profiler import recognize
from flask import Flask, render_template, Response, jsonify, request
from transformers import OwlViTProcessor, OwlViTForObjectDetection
import torch

app = Flask(__name__)
face_data = {}
frames = {}
cuda_device = "cuda"
processor = OwlViTProcessor.from_pretrained("google/owlvit-base-patch32")
model = OwlViTForObjectDetection.from_pretrained("google/owlvit-base-patch32")
model.to(cuda_device)


# This can be customized to pass multiple parameters
def getPipeline(stereo):
    # Start defining a pipeline
    pipeline = dai.Pipeline()

    # Define a source - color camera
    cam_rgb = pipeline.create(dai.node.ColorCamera)
    # For the demo, just set a larger RGB preview size for OAK-D
    cam_rgb.setPreviewSize(1920, 1080)
    cam_rgb.setBoardSocket(dai.CameraBoardSocket.RGB)
    cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    cam_rgb.setInterleaved(False)

    # Create output
    xout_rgb = pipeline.create(dai.node.XLinkOut)
    xout_rgb.setStreamName("rgb")
    cam_rgb.preview.link(xout_rgb.input)
    return pipeline


def depth_init(dev_info, stack, dic):
    openvino_version = dai.OpenVINO.Version.VERSION_2021_4
    # Closer-in minimum depth, disparity range is doubled (from 95 to 190):
    extended_disparity = False
    # Better accuracy for longer distance, fractional disparity 32-levels:
    subpixel = False
    # Better handling for occlusions:
    lr_check = True
    DEPTHdevice_info = dai.DeviceInfo("1944301051694D1300")

    # Create pipeline
    DEPTHpipeline = dai.Pipeline()

    # Define sources and outputs
    monoLeft = DEPTHpipeline.create(dai.node.MonoCamera)
    monoRight = DEPTHpipeline.create(dai.node.MonoCamera)
    depth = DEPTHpipeline.create(dai.node.StereoDepth)
    xout = DEPTHpipeline.create(dai.node.XLinkOut)

    xout.setStreamName("disparity")
    # Properties
    monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
    monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    monoRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)

    # Create a node that will produce the depth map (using disparity output as it's easier to visualize depth this way)
    depth.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_ACCURACY)
    # Options: MEDIAN_OFF, KERNEL_3x3, KERNEL_5x5, KERNEL_7x7 (default)
    depth.initialConfig.setMedianFilter(dai.MedianFilter.KERNEL_7x7)
    depth.setLeftRightCheck(lr_check)
    depth.setExtendedDisparity(extended_disparity)
    depth.setSubpixel(subpixel)

    # Linking
    monoLeft.out.link(depth.left)
    monoRight.out.link(depth.right)
    depth.disparity.link(xout.input)
    device: dai.Device = stack.enter_context(dai.Device(DEPTHpipeline, DEPTHdevice_info))
    dic["depth"] = device.getOutputQueue(name="disparity", maxSize=4, blocking=False)


def worker(dev_info, stack, dic):
    openvino_version = dai.OpenVINO.Version.VERSION_2021_4
    device: dai.Device = stack.enter_context(dai.Device(openvino_version, dev_info, False))

    # Note: currently on POE, DeviceInfo.getMxId() and Device.getMxId() are different!
    print("=== Connected to " + dev_info.getMxId())
    mxid = device.getMxId()
    cameras = device.getConnectedCameras()
    usb_speed = device.getUsbSpeed()
    print("   >>> MXID:", mxid)
    print("   >>> Cameras:", *[c.name for c in cameras])
    print("   >>> USB speed:", usb_speed.name)

    device.startPipeline(getPipeline(len(cameras) == 3))
    dic["rgb"] = device.getOutputQueue(name="rgb")


device_infos = dai.Device.getAllAvailableDevices()
print(f'Found {len(device_infos)} devices')
global ticker
ticker = 0

with contextlib.ExitStack() as stack:
    queues = {}
    threads = []
    for dev in device_infos:
        try:
            time.sleep(1)  # Currently required due to XLink race issues
            if dev.getMxId() == "1944301051694D1300":
                thread = threading.Thread(target=depth_init, args=(dev, stack, queues))
            else:
                thread = threading.Thread(target=worker, args=(dev, stack, queues))
            thread.start()
            threads.append(thread)
        except Exception as e:
            print("Error", e)

    for t in threads:
        t.join()  # Wait for all threads to finish


    def get_depth_frame():
        for i in range(30):
            inDisparity = queues["depth"].get()
        inDisparity = queues["depth"].get()  # blocking call, will wait until a new data has arrived
        frame = inDisparity.getFrame()
        frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)
        return frame


    def get_rgb_frame():
        for i in range(7):
            in_rgb = queues["rgb"].get()
            frame = in_rgb.getCvFrame()
        in_rgb = queues["rgb"].get()  # blocking call, will wait until a new data has arrived
        frame = in_rgb.getCvFrame()
        frame = cv2.flip(frame, 0)
        print(frame.shape)
        return frame


    @app.route("/health", methods=['POST'])
    def health():
        return jsonify({"status": "OK"})


    @app.route('/live', methods=['POST'])
    def return_face_data():
        try:
            rgb_frame = get_rgb_frame()
            # print resoloution
            face_data = recognize(rgb_frame, array=True)
        except Exception as e:
            print(e)
            return jsonify({"error": "no frame"})
        return jsonify(face_data)


    @app.route("/vit", methods=['POST'])
    def vit():
        try:
            rgb_frame = get_rgb_frame()
        except Exception as e:
            print(e)
            return jsonify({"error": "no frame"})
        # get requested object
        objects = request.get_json()
        objects_recognize = objects["objects"]
        # get image
        original_image = rgb_frame
        rgb_frame = Image.fromarray(rgb_frame)
        inputs = processor(text=objects_recognize, images=rgb_frame, return_tensors="pt").to(cuda_device)
        outputs = model(**inputs)
        target_sizes = torch.Tensor([rgb_frame.size[::-1]]).to(cuda_device)
        results = processor.post_process(outputs=outputs, target_sizes=target_sizes)
        i = 0  # Retrieve predictions for the first image for the corresponding text queries
        text = objects_recognize[i]
        boxes, scores, labels = results[i]["boxes"], results[i]["scores"], results[i]["labels"]
        results = []
        score_threshold = 0.1
        for box, score, label in zip(boxes, scores, labels):
            box = [round(i, 2) for i in box.tolist()]
            if score >= score_threshold:
                results.append({"box": list(box), "score": float(score), "label": objects_recognize[label]})
        del inputs
        del outputs
        del target_sizes
        return jsonify({"results": results})


    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5050)
