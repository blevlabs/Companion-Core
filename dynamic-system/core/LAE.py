# This script is part of the Dynamic System project. This script manages the execution, status monitoring,
# and logging of any errors that occur during the execution of any files in the Dynamic System project. Import the
# necessary modules.
import datetime
import json
import os
import subprocess
import sys
import threading

# asa_type FORMAT: {"asa_class_type": "generation|optimization|analysis|breakdown","context":"OPTIONAL","code":"OPTIONAL",file:"OPTIONAL",repair_mode:"OPTIONAL"}
import time
import traceback
import requests
import weaviate

'''
Action Log Schema

"Date": [
    {
      "type": "log_type", # log_type can be "error", "warning", "info", "debug", or "action"
      "body": "log_body", # Body of log instance - can be any string. Holds information related to the log instance.
      "required_actions": [
        "action1", # List of actions that must be taken to resolve the issue. These can include script-function calls (such as calling to the ASA), or manual actions.
        "action2" 
      ]
    }
  ]
  
'''


class LAE:
    def __init__(self, script_paths=[],
                 log_json_path="/home/blabs/Companion-Core/dynamic-system/core/logs/action_log.json",
                 priority_log="/home/blabs/Companion-Core/dynamic-system/core/logs/priority_log.json",
                 error_log_path="/home/blabs/Companion-Core/dynamic-system/core/logs/error_log.json",
                 weaviate_server="http://192.168.1.110:8080",
                 asa_server="http://localhost:5090/asa"):
        self.script_paths = None
        self.priority = None
        self.weaviate_client = weaviate.Client(weaviate_server)
        self.python_path = sys.executable
        self.running = False
        self.processes = []
        self.asa_server = asa_server
        self.error_log_path = error_log_path
        self.log_json_path = log_json_path
        self.priority_log = priority_log
        self.live_checks()

    def get_priority(self):
        # Get the priority of the script
        with open(self.priority_log, "r") as priority_log_file:
            priority_log = json.loads(priority_log_file.read())["priority_files"]
        print("Priority: ", priority_log)
        return priority_log

    def live_checks(self):
        assert type(self.log_json_path) == str, "The log json path must be a string."
        assert type(self.priority_log) == str, "The priority log path must be a string."
        assert type(self.priority_log) == str, "The priority log must be a string."
        assert self.weaviate_client.is_live(), "Weaviate server is not live"
        assert os.path.isfile(self.python_path), "Python path is not valid"
        self.priority = self.get_priority()
        self.script_paths = [x["path"] for x in self.priority if os.path.isfile(x["path"])]
        for script_path in self.script_paths:
            assert os.path.isfile(script_path), f"Script path {script_path} is not valid"
        assert self.log_json_path != "", "Log JSON path is not set"
        assert os.path.isfile(self.log_json_path), "Log JSON path is not valid"
        return True

    def log_error(self, script_path, error, traceback_data):
        # Log the error
        # Create the log dictionary
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        log = {"script_path": script_path, "error": str(error), "traceback": traceback_data, "timestamp": timestamp}
        # Write the log to the log file
        with open(self.error_log_path, "a") as log_file:
            log_file.write(json.dumps(log) + "\n")
        return True

    def request_asa(self, asa_info):
        # Request the ASA
        # Send the request to the ASA
        try:
            response = requests.post(self.asa_server, json=asa_info)
            return response.json()["asa-response"]
        except Exception as error:
            return {"error": "ASA server is not live: " + str(error)}

    def run_script(self, script_path):
        # Run the script
        try:
            # Run the script
            subprocess.run([self.python_path, script_path])
        except Exception as error:
            # Log the error
            traceback_string = traceback.format_exc()
            self.log_error(script_path, error, traceback_string)

    def monitor_threads(self, fix=False):
        # Monitor the threads
        try:
            while self.running:
                # Check if any threads or subprocesses have stopped running or if any traceback errors have occurred
                for thread in self.processes:
                    if thread["process"].poll() is not None:
                        stdout, stderr = thread["process"].communicate()
                        error = stderr.decode("utf-8")
                        print("THREAD ERROR: ", error)
                        self.log_error(thread["script_path"], error, error)
                        if fix:
                            asa_breakdown = {"asa_class_type": "breakdown", "context": error}
                            breakdown_asa = self.request_asa(asa_breakdown)
                            repair_data = {"asa_class_type": "generation"}
                            repair_data.update(breakdown_asa)
                            self.request_asa(repair_data)
                            # Restart the thread
                            thread["thread"] = threading.Thread(target=self.run_script, args=(thread["script_path"],))
                            thread["thread"].start()
                            # thread["process"] = subprocess.Popen([self.python_path, thread["script_path"]],
                            #                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        print("PROCESS ERROR: ", error)
                        # kill specific python file
                        os.system("pkill -f " + thread["script_path"])
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Shutting Down LAE...")
            self.running = False
            os.system("pkill python")

    def initalize(self):
        # Start the multithreading process
        self.running = True
        # Create a new thread and subprocess for each script
        print("All scripts: ", self.script_paths)
        for script_path in self.script_paths:
            print("Working on script: ", script_path)
            # Create a new multiprocess
            process = subprocess.Popen([self.python_path, script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Add the thread and subprocess to the threads list
            self.processes.append({"process": process, "script_path": script_path})
            # Start the thread
            print("Started thread for script: ", script_path)


if __name__ == "__main__":
    # Run the LAE
    lae = LAE()
    lae.initalize()
    # monitor the threads
    lae.monitor_threads()
