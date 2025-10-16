## About The Project

`unimi_crop_sensing` was created with the aim of offering a set of **simple and intuitive operations** to interact with the **ZED camera**. It consists of a toolkit for processing and segmenting images and point clouds acquired via the **ZED stereo camera**. The project is designed for precision agriculture applications, allowing you to identify plants in 2D and 3D, generate bounding boxes and communicate with a cobot through WebSocket in a ROS environment.

### Main features
* Green segmentation with Excess Green Index
* Plant clustering via KMeans
* 2D and 3D bounding box calculation on point cloud
* Save `.ply`, images, normal map
* WebSocket ROS (`rosbridge`) integration for communication on separate systems

### Built With

* [Stereolabs ZED SDK](https://www.stereolabs.com/zed-sdk/) 
* [OpenCV](https://opencv.org/)
* [NumPy](https://numpy.org/)
* [scikit-image](https://scikit-image.org/)
* [scikit-learn](https://scikit-learn.org/)
* [websocket-client](https://github.com/websocket-client/websocket-client)

## Getting Started

### Prerequisites

Make sure you have:
- Python 3.9
- ZED SDK properly installed and working and a connected **ZED camera**
- ROS + rosbridge running if you use WebSocket
- The libraries listed in `requirements.txt`

### Installation

You can use `unimi_crop_sensing` as a **Python package installable via PyPI**. Install everything with:
```bash
pip install unimi_crop_sensing
```

⚠️ Pyzed 5.0 requires numpy 2.x, this conflicts with other project features, so if you encounter errors related to `numpy`, make sure you install a compatible version:
```bash
pip install "numpy<2"
```

## Usage

This is an example of a script that uses every function to obtain spatial coordinates and point clouds of each plant within its range

```python
# This function is used to test the functionalities of the crop sensing module
def main():
    
    # Get the current pose of the cobot
    pose = cobot_manager.get_cobot_pose(linux_ip)

    # Initialize the ZED camera
    zed = zed_manager.zed_init(pose)
    
    # Capture the environment with the ZED camera
    image, depth_map, normal_map, point_cloud = zed_manager.get_zed_image(zed, save=True)

    # Filter the plants from the background
    mask = find_plant.filter_plants(image, save_mask=True)
    
    # Divide the plants into clusters
    masks, bounding_boxes = find_plant.segment_plants(mask, plants_number)
    find_plant.save_clustered_image(image, bounding_boxes)

    # Extract the 3D points from the clusters
    for m in masks:
        bbxpts = find_plant.get_3d_bbox(m, point_cloud)
        
    # Communicate the bounding boxes to the cobot (only if the cobot is operated in another machine)
    cobot_manager.send_cobot_map(linux_ip, bbxpts)

    # Create point cloud (this will create a .ply file by taking a video of the environment)
    zed.close()
    create_plc.record_and_save(plant_name='piantina1', frames=300)

``` 

**Note:** The `pipeline.py` file contains a ready-to-run example with all the necessary components to extract bounding boxes and send them to the Dobot cobot.

<!-- CONTACT -->
## Contact

francescobassam.morgigno@studenti.unimi.it

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [Stereolabs](https://www.stereolabs.com/en-it)

