import sys
from base_asa_demo import call_asa_server
sys.path.insert(0, '/dynamic-system/core')
demo_file = "/home/blabs/Companion-Core/dynamic-system/core/demos/asa_demos/demo_files"

file_repair_data = {"file": demo_file, "asa_class_type": "repair"}


call_asa_server(file_repair_data)
