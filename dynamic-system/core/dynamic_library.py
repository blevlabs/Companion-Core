import requests
from aci import ACI

# from asa import ASA

aci = ACI()


class dynamic:

    def __init__(self):
        self.audio_server = "http://127.0.0.1:5000"
        self.video_server = "http://127.0.0.1:5050"
        self.ris = "http://127.0.0.1:5060"

    def get_face_data(self):
        # example: {'Brayden Levangie': [x1, y1, x2, y2]}
        try:
            face_data = requests.post(self.video_server + "/live").json()
        except Exception as e:
            print(e)
            return {"error": "no frame"}
        # get closest face based on coordinates
        all_box_coordinates = list(face_data.values())
        if len(all_box_coordinates) == 0:
            return {"error": "no face"}
        closest_face = min(all_box_coordinates, key=lambda x: abs(x[0] - x[2]) * abs(x[1] - x[3]))
        closest_face_name = list(face_data.keys())[list(face_data.values()).index(closest_face)]
        # get center of closest face
        x1, y1, x2, y2 = closest_face
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        face_data["closest_face"] = {"X": center_x, "Y": center_y, "name": closest_face_name}
        return face_data

    def vit_request(self, objects):
        try:
            vit_data = requests.post(self.video_server + "/vit", json={"objects": objects}).json()["results"]
        except Exception as e:
            print(e)
            return {"error": "no frame"}
        return vit_data

    def audio_request(self):
        try:
            audio_data = requests.post(self.audio_server + "/speech").json()
        except Exception as e:
            print(e)
            return {"error": "no frame"}
        return audio_data

    def audio_history_request(self):
        try:
            audio_data = requests.post(self.audio_server + "/speech/history").json()
        except Exception as e:
            print(e)
            return {"error": "no frame"}
        return audio_data

    def classify_dialogue(self, dialogue):
        return aci.flan_classify(classifier_context=dialogue)

    def live_information_collection(self, with_audio_history=False, with_vit=False, vit_objects=[]):
        live_data = {}
        face_data = self.get_face_data()
        live_data["face_data"] = face_data
        if with_vit:
            vit_data = self.vit_request(vit_objects)
            live_data["vit_data"] = vit_data
        audio_data = self.audio_request()
        live_data["audio_data"] = audio_data
        if with_audio_history:
            audio_history_data = self.audio_history_request()
            live_data["audio_history_data"] = audio_history_data
        initial_classifier = self.classify_dialogue(audio_data["text"])
        live_data["initial_classifier"] = initial_classifier
        return live_data

    def info_search_breakdown(self, live_data):
        # Requires: User Dialogue, Face Recognition Data, Audio History Data
        # Returns: Search Data for Contextual Usage
        # Functions: Search Query Generation (FlanT5)
        dialog = live_data["audio_data"]["text"]
        # generate search query

        pass

    def info_memory_breakdown(self, live_data):
        # Requires: User Dialogue, Face Recognition Data, Audio History Data
        # Returns: Memory Data for Contextual Usage
        # Functions: Memory Query Generation (FlanT5), Memory Query Execution (Weaviate Search)
        dialog = live_data["audio_data"]["text"]
        users = live_data["face_data"]

        pass

    def chat_response_breakdown(self, live_data):
        # Requires: User Dialogue, Face Recognition Data, Audio History Data
        # Returns: Chat Response Data for ACI and Secondary Action Classifier
        # Functions: ACI Generation
        dialog = live_data["audio_data"]["text"]
        users = live_data["face_data"]
        # generate ACI
        conversation_packet = aci.prompt_generation(dialog, users)
        return conversation_packet

    def internal_fix_breakdown(self, live_data):
        # Requires: User Dialogue, Face Recognition Data, Audio History Data
        # Returns: Internal Fix Data: Traceback Review - CALL LAE
        # Functions: ASA Call on Traceback
        dialog = live_data["audio_data"]["text"]
        # parse issue and send to LAE System
        # classes: Reset, Check Scripts, Shutdown, Reboot, Add Functionality, Update Functionality

        pass

    def classifier_manager(self, class_name, ldc_details):
        related_class_functions = {"INFO-SEARCH": self.info_search_breakdown, "INFO-MEMORY": self.info_memory_breakdown,
                                   "CHAT-RESP": self.chat_response_breakdown,
                                   "INTERNAL-FIX": self.internal_fix_breakdown}
        if class_name in related_class_functions and class_name != "NONE":
            exec_content = related_class_functions[class_name](ldc_details)
        elif class_name == "NONE":
            return {"status": "NONE"}
        else:
            return {"status": "ERROR"}
        act_log = {
            "status": {"class_name": class_name, "ldc_details": ldc_details, "exec_content": exec_content}}
        return act_log

    def execution_server_manager(self, act_log):
        # Requires: Action Log
        # Returns: Execution Server Data
        # Functions: Execution Server Data
        return
