import websocket
import json
import time
import threading

pose_data = None  # shared global

# === SEND MAP STRUCTURE ===
def on_open(ws, bbxpts):
    print("Connected to rosbridge")

    advertise_msg = {
        "op": "advertise",
        "topic": "/Boing",
        "type": "custom_messages/Map"
    }
    ws.send(json.dumps(advertise_msg))

    # Convert numpy types to native Python types for JSON serialization
    map_msg = {
        "op": "publish",
        "topic": "/Boing",
        "msg": {
            "work_space": {
                "low_left": {"x": -10.0, "y": -10.0, "z": -10.0},
                "top_right": {"x": 10.0, "y": 10.0, "z": 10.0}
            },
            "objects": [
                {
                    "target": True,
                    "shape": {
                        "low_left": {
                            "x": bbx['min']['x'],
                            "y": bbx['min']['y'],
                            "z": bbx['min']['z']
                        },
                        "top_right": {
                            "x": bbx['max']['x'],
                            "y": bbx['max']['y'],
                            "z": bbx['max']['z']
                        }
                    },
                    "possible_trajectories": []
                } for bbx in bbxpts
            ]
        }
    }

    try:
        ws.send(json.dumps(map_msg))
        print("Map message sent:", json.dumps(map_msg, indent=2))
    except Exception as e:
        print(f"Error sending map message: {e}")
        raise
    
def on_error(ws, error):
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("Closed connection")

# === RECEIVE POSE ===
def on_message_pose(ws, message):
    global pose_data
    data = json.loads(message)
    pose_data = data.get('msg', {})
    print("Received pose:", json.dumps(pose_data, indent=2))

def subscribe_to_pose(ws):
    print("Subscribing to /cobot_pose")
    subscribe_msg = {
        "op": "subscribe",
        "topic": "/cobot_pose",
        "type": "geometry_msgs/PoseStamped"
    }
    ws.send(json.dumps(subscribe_msg))

def listen_for_pose(linux_ip):
    ws_url = f"ws://{linux_ip}:9090"
    ws = websocket.WebSocketApp(ws_url,
                                 on_open=subscribe_to_pose,
                                 on_message=on_message_pose,
                                 on_error=on_error,
                                 on_close=on_close)
    thread = threading.Thread(target=ws.run_forever, daemon=True)
    thread.start()

def send_cobot_map(linux_ip, bbxpts):
    """
    This function establishes a WebSocket connection to the specified ROS bridge server
    running on the given Linux IP address and sends the bounding box coordinates.

    Args:
        linux_ip (str): IP address of the ROS-enabled Linux machine running rosbridge server.
        bbxpts (dict): Bounding box data dictionary containing min and max coordinates,
            e.g., {"min": {"x": ..., "y": ..., "z": ...}, "max": {"x": ..., "y": ..., "z": ...}}.
    """
    ws_url = f"ws://{linux_ip}:9090"
    ws = websocket.WebSocketApp(ws_url,
                                 on_open=lambda ws: on_open(ws, bbxpts),
                                 on_error=on_error,
                                 on_close=on_close)
    print("Connecting to rosbridge...")
    ws.run_forever()

def get_cobot_pose(linux_ip, timeout=1):
    """
    Retrieves the current pose (position and orientation) of a collaborative robot (cobot)
    from a remote Linux PC running ROS over WebSocket

    The function starts listening for incoming pose data from the specified IP address, which
    must belong to a ROS-enabled Linux system using WebSocket communication. It waits for up to
    `timeout` seconds for the data to arrive. If no data is received within that time, it returns
    a default Pose object with all fields (x, y, z, w) set to zero

    Args:
        linux_ip (str): IP address of the ROS-enabled Linux machine (WebSocket server)
        timeout (int, optional): Maximum number of seconds to wait for pose data (default is 1)

    Returns:
        Pose: An object containing `position` (x, y, z) and `orientation` (x, y, z, w) fields
    """
    global pose_data
    pose_data = None
    listen_for_pose(linux_ip)

    start_time = time.time()
    while pose_data is None and (time.time() - start_time) < timeout:
        print("Waiting for pose...")
        time.sleep(0.5)

    if pose_data is not None:
        print("Pose data received:", pose_data)
        return pose_data
    
    class Pose:
        class Position:
            def __init__(self, x=0, y=0, z=0):
                self.x = x
                self.y = y
                self.z = z

        class Orientation:
            def __init__(self, x=0, y=0, z=0, w=0):
                self.x = x
                self.y = y
                self.z = z
                self.w = w

        def __init__(self):
            self.position = self.Position()
            self.orientation = self.Orientation()

    return Pose()