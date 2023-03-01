import requests
import weaviate


class dynamic():

    def __init__(self):
        self.servers = {"audio": {"url": "http://127.0.0.1:5000", "call": "/speech"},
                        "video": {"url": "http://127.0.0.1:5050", "call": "/live"},
                        "ris": {"url": "http://127.0.0.1:5075", "call": "/ris"},
                        "asa": {"url": "http://127.0.0.1:5090", "call": "/asa"},
                        "carp": {"url": "http://192.168.1.110:5000", "call": "/ccarp"},
                        "codet5": {"url": "http://192.168.1.110:5090", "call": "/codet5"},
                        "aci": {"url": "http://127.0.0.1:6000", "call": "/chat"}}
        self.weaviate_database = "http://192.168.1.110:8080"
        health_results = self.health()
        if "error" in health_results:
            raise Exception("Health results: ", health_results)
        # print("Health results: ", health_results)

    def construct_call(self, server_name, extension=""):
        if extension != "":
            return self.servers[server_name]["url"] + extension
        else:
            return self.servers[server_name]["url"] + self.servers[server_name]["call"]

    def get_face_data(self):
        # example: {'Brayden Levangie': [x1, y1, x2, y2]}
        try:
            face_data = requests.post(self.construct_call("video")).json()
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

    def manage_call(self, server, call_data):
        try:
            call = requests.post(server, json=call_data, timeout=10).json()
        except Exception as e:
            raise e
        return call

    def call_carp(self, query="Test", documents=["Test"]):
        try:
            carp_data = self.manage_call(server=self.construct_call("carp"),
                                         call_data={"query": query, "documents": documents})
        except Exception as e:
            raise e
        return carp_data

    def call_codet5(self, query="#make a script that adds two numbers"):
        try:
            code = \
                self.manage_call(server=self.construct_call("codet5"), call_data={"code": query})["codet5-response"][0][
                    "generated_text"].replace("\n\n", "\n").strip("\n")
        except Exception as e:
            raise e
        return code

    def health(self):
        results = {}
        for server, data in self.servers.items():
            try:
                results[server] = self.manage_call(server=data["url"] + "/health", call_data={})
            except Exception as e:
                results[server] = {"error": str(e)}
        results["weaviate_database"] = weaviate.Client(self.weaviate_database).is_live()
        return results

    def vit_request(self, objects):
        try:
            vit_data = \
                self.manage_call(server=self.construct_call("video", extension="/vit"), call_data={"objects": objects})[
                    "results"]
        except Exception as e:
            return {"error": e}
        return vit_data

    def audio_request(self):
        try:
            audio_data = self.manage_call(server=self.construct_call("audio", extension="/speech"), call_data={})
        except Exception as e:
            return {"error": e}
        return audio_data

    def audio_history_request(self):
        try:
            audio_data = self.manage_call(server=self.construct_call("audio", extension="/speech/history"),
                                          call_data={})
        except Exception as e:
            return {"error": e}
        return audio_data

    def classify_dialogue(self, dialogue):
        return self.manage_call(server=self.construct_call("aci", extension="/classify"), call_data={"text": dialogue})

    def live_information_collection(self, with_audio_history=False, with_vit=False, vit_objects=[]):
        live_data = {"face_data": {}, "audio_data": {}, "audio_history_data": {}, "initial_classifier": {},
                     "context": {}}
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

        raise NotImplementedError("Search Query Generation not implemented yet")

    def info_memory_breakdown(self, live_data):
        # Requires: User Dialogue, Face Recognition Data, Audio History Data
        # Returns: Memory Data for Contextual Usage
        # Functions: Memory Query Generation (FlanT5), Memory Query Execution (Weaviate Search)
        dialog = live_data["audio_data"]["text"]
        users = live_data["face_data"]
        # generate memory query

        # execute memory query

        # return memory query results
        raise NotImplementedError("Memory Query Generation and Execution not implemented yet")

    def chat_response_breakdown(self, live_data={}, context={}):
        # Requires: User Dialogue, Face Recognition Data, Audio History Data
        # Returns: Chat Response Data for ACI and Secondary Action Classifier
        # Functions: ACI Generation
        dialog = live_data["audio_data"]["text"]
        users = live_data["face_data"]
        # generate ACI
        conversation_packet = self.manage_call(server=self.construct_call("aci", extension="/chat"),
                                               call_data={"speaker_data": dialog, "observer_data": users,
                                                          "context": context})
        # return conversation_packet for dynamic_behavior to then call /speak for ACI server when needed
        return conversation_packet

    def internal_fix_breakdown(self, live_data):
        # Requires: User Dialogue, Face Recognition Data, Audio History Data
        # Returns: Internal Fix Data: Traceback Review - CALL LAE
        # Functions: ASA Call on Traceback
        dialog = live_data["audio_data"]["text"]
        # parse issue and send to LAE System
        # classes: Reset, Check Scripts, Shutdown, Reboot, Add Functionality, Update Functionality

        raise NotImplementedError("Internal Fix Generation not implemented yet")

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
        raise NotImplementedError("Execution Server Manager not implemented yet")