import pyzed.sl as sl
import numpy as np
import cv2
import os

### This file main purpose is to manage the ZED camera ###

def ensure_data():
    """
    Ensures that the 'crop_sensing/data' folder exists.
    """
    folder_path = "crop_sensing/data"
    os.makedirs(folder_path, exist_ok=True)

class Pose:
    class Position:
        def __init__(self):
            self.x = 0
            self.y = 0
            self.z = 0

    class Orientation:
        def __init__(self):
            self.x = 0
            self.y = 0
            self.z = 0
            self.w = 0

    def __init__(self):
        self.position = self.Position()
        self.orientation = self.Orientation()

def update_pose(zed, pose):
    """
    EXPERIMENTAL
    Updates the ZED camera's transform based on the given pose.

    Args:
        zed (sl.Camera): The ZED camera object.
        pose (Pose): The new pose to set (with position and orientation).
    """
    pose.position.x += +0.01  # Offset X position
    pose.position.y += -0.02  # Offset Y position
    pose.position.z += +0.07  # Offset Z position
    translation = sl.Translation(pose.position.x, pose.position.y, pose.position.z)
    orientation = sl.Orientation()
    orientation.init_vector(
        pose.orientation.x,
        pose.orientation.y,
        pose.orientation.z,
        pose.orientation.w
    )
    zed_tf = sl.Transform()
    zed_tf.init_orientation_translation(orientation, translation)
    zed.reset_positional_tracking(zed_tf)

# === Initialize ZED ===
def zed_init(pose=None):    
    """
    Initializes a ZED camera with specific configuration parameters and sets its
    transform based on a given cobot pose

    Args:
        pose (object, optional): A pose object containing:
            - position.x, position.y, position.z (in meters)
            - orientation.x, orientation.y, orientation.z, orientation.w (quaternion)
        If None, defaults to all zeros.

    Returns:
        sl.Camera: A ZED camera object initialized and transformed according to the input pose

    Raises:
        SystemExit: If the camera fails to open
    """
    zed = sl.Camera()
    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD2K
    init_params.depth_mode = sl.DEPTH_MODE.NEURAL_PLUS
    init_params.coordinate_system = sl.COORDINATE_SYSTEM.RIGHT_HANDED_Z_UP 
    init_params.depth_maximum_distance = 2
    init_params.depth_minimum_distance = 0.2

    init_params.coordinate_units = sl.UNIT.METER
    if zed.open(init_params) != sl.ERROR_CODE.SUCCESS:
        print("Impossibile aprire la ZED")
        exit(1)

    if pose is None:
        pose = Pose()
    
    update_pose(zed, pose)
    
    return zed

# DEBUG: Save the images and depth map for testing purposes
def memorize_images(image, depth_map, normal_map):
    ensure_data()
    image_path = "crop_sensing/data/saved_image.png"
    depth_map_path = "crop_sensing/data/saved_depth_map.png"
    normal_map_path = "crop_sensing/data/saved_normal_map.png"
    # Transform the normal map to a format suitable for saving
    normal_map_data = normal_map.get_data()
    # Handle NaN and Inf values before casting
    normal_map_data = np.nan_to_num(normal_map_data, nan=0.0, posinf=1.0, neginf=-1.0)
    normal_map_image = ((normal_map_data[:, :, :3] + 1) / 2 * 255).astype(np.uint8)
    # Normalize the depth map for visualization
    depth_map_data = depth_map.get_data()
    # Handle NaN and Inf values in depth map
    depth_map_data = np.nan_to_num(depth_map_data, nan=0.0, posinf=255.0, neginf=0.0)
    depth_map_norm = cv2.normalize(depth_map_data[:, :, 2], None, 0, 255, cv2.NORM_MINMAX)
    depth_map_image = depth_map_norm.astype(np.uint8)
    # Save the images
    cv2.imwrite(image_path, image)
    cv2.imwrite(depth_map_path, depth_map_image)
    cv2.imwrite(normal_map_path, normal_map_image)

# === Acquire ZED image and depth map ===
def get_zed_image(zed, save=False):
    """
    Captures a single frame from a ZED camera, retrieving the RGB image, depth map,
    normal map, and point cloud

    Args:
        zed (sl.Camera): An initialized and opened ZED camera object
        save (bool, optional): If True, saves the RGB image, depth map, normal map,
            and point cloud to the "data/" directory. Default is False

    Returns:
        tuple: A tuple containing:
            - image (np.ndarray): The RGB image as a NumPy array
            - depth_map (sl.Mat): The depth map in XYZRGBA format
            - normal_map (sl.Mat): The normal map
            - point_cloud (sl.Mat): The 3D point cloud in XYZRGBA format
    """
    # Initialize variables
    runtime_parameters = sl.RuntimeParameters()
    image_zed = sl.Mat()
    depth_map = sl.Mat()
    point_cloud = sl.Mat()
    normal_map = sl.Mat()
    image = None

    # Retrieve the image and depth map
    print("Acquisizione misure dalla camera...")
    while zed.grab(runtime_parameters) == sl.ERROR_CODE.SUCCESS:
        # Acquisisci l'immagine e la mappa di profondità
        zed.retrieve_image(image_zed, sl.VIEW.LEFT)
        zed.retrieve_measure(depth_map, sl.MEASURE.XYZRGBA)
        zed.retrieve_measure(normal_map, sl.MEASURE.NORMALS)   
        zed.retrieve_measure(point_cloud, sl.MEASURE.XYZRGBA) 
        image = cv2.cvtColor(image_zed.get_data(), cv2.COLOR_RGBA2RGB)
        break

    if save and image is not None:
        memorize_images(image, depth_map, normal_map)
        # Salva il point cloud in un file PLY
        point_cloud.write("crop_sensing/data/point_cloud.ply")
        print(f"\"Salvato acquisizioni in \\data\"")
        print(f"\"Salvato acquisizioni in \\data\"")
    
    return image, depth_map, normal_map, point_cloud