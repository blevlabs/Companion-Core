from dynamic_library import dynamic
import time
dynamic = dynamic()
print("Starting LDC Test")
while 1:
    t0 = time.time()
    data = dynamic.live_information_collection()
    t1 = time.time()
    print("\n\n", data)
    print(t1-t0)
    time.sleep(2)
