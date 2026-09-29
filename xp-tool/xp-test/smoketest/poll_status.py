import sys
import time
import xp
 
def poll(capability_id: str, interval: float = 5.0):
    last = None
    while True:
        try:
            status = xp.see_capability(capability_id)
        except Exception as e:
            print(e)
            print(xp.list_capabilities())
        if status != last:
            print(status, end="\r")
            last = status
        time.sleep(interval)
 
if __name__ == "__main__":
    poll(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 5.0)
 

