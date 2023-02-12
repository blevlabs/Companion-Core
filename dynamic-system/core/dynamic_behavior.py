from dynamic_library import dynamic
import time
import json

dynamic = dynamic()
action_log_tracker = "/home/blabs/Companion-Core/dynamic-system/core/logs/action_log.json"


def write_action_log(total_action_data):
    with open(action_log_tracker, "a") as f:
        json.dump(total_action_data, f)
        f.close()


# Main system loop. Collects live data and classifies it, executes related action steps and logs total results, then repeats. 50ms delay is for testing purposes.
while 1:
    live_data = dynamic.live_information_collection(with_audio_history=False, with_vit=False, vit_objects=[])
    print("DEBUG: live_data: ", live_data)
    action_log = dynamic.classifier_manager(live_data["initial_classifier"], live_data)
    print("DEBUG: action_log: ", action_log)
    total_action_data = {"action_log": action_log, "live_data": live_data}
    write_action_log(total_action_data)
    time.sleep(0.05)