# This script is part of the Dynamic System project. This script manages the execution, status monitoring,
# and logging of any errors that occur during the execution of any files in the Dynamic System project. Import the
# necessary modules.
import sys
import datetime
import subprocess
import threading
import traceback
import json
import weaviate
import os
from asa import ASA
import traceback
# asa_type FORMAT: {"asa_class_type": "generation|optimization|analysis|breakdown","context":"OPTIONAL","code":"OPTIONAL",file:"OPTIONAL",repair_mode:"OPTIONAL"}
import time
import os

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
                 weaviate_server="http://192.168.1.110:8080"):
        self.script_paths = None
        self.priority = None
        self.weaviate_client = weaviate.Client(weaviate_server)
        self.python_path = sys.executable
        self.running = False
        self.processes = []
        self.error_log_path = error_log_path
        self.threads = []
        self.log_json_path = log_json_path
        self.priority_log = priority_log
        self.live_checks()

    def get_priority(self):
        # Get the priority of the script
        with open(self.priority_log, "r") as priority_log_file:
            priority_log = json.loads(priority_log_file.read())["priority_files"]
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
        while self.running:
            # Check if any threads or subprocesses have stopped running or if any traceback errors have occurred
            for thread in self.threads:
                if not thread["thread"].is_alive():
                    stdout, stderr = thread["process"].communicate()
                    error = stderr.decode("utf-8")
                    print("THREAD ERROR: ", error)
                    self.log_error(thread["script_path"], error, error)
                    if fix:
                        asa_breakdown = {"asa_class_type": "breakdown", "context": error}
                        breakdown_asa = ASA(asa_breakdown).response
                        repair_data = {"asa_class_type": "generation"}
                        repair_data.update(breakdown_asa)
                        ASA(repair_data)
                        # Restart the thread
                        thread["thread"] = threading.Thread(target=self.run_script, args=(thread["script_path"],))
                        thread["thread"].start()
                        # thread["process"] = subprocess.Popen([self.python_path, thread["script_path"]],
                        #                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    print("PROCESS ERROR: ", error)
                    # kill specific python file
                    os.system("pkill -f " + thread["script_path"])
            time.sleep(0.1)

    def initalize(self):
        # Start the multithreading process
        self.running = True
        # Create a new thread and subprocess for each script
        print("All scripts: ", self.script_paths)
        for script_path in self.script_paths:
            print("Working on script: ", script_path)
            # Create a new thread and subprocess
            thread = threading.Thread(target=self.run_script, args=(script_path,))
            # process = subprocess.Popen([self.python_path, script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Add the thread and subprocess to the threads list
            self.threads.append({"thread": thread, "process": "process", "script_path": script_path})
            # Start the thread
            thread.start()
            print("Started thread for script: ", script_path)


if __name__ == "__main__":
    # Run the LAE
    lae = LAE()
    lae.initalize()
    # monitor the threads
    lae.monitor_threads()
