import find_plant
import zed_manager
import cobot_manager
import create_plc

# testing parameters
linux_ip = "192.168.5.100"
plants_number = 2

# This function is used to test the functionalities of the crop sensing module
def main():

    # Initialize the ZED camera
    zed = zed_manager.zed_init()
    pose=cobot_manager.get_cobot_pose(linux_ip)
    zed_manager.update_pose(zed,pose)
    
    frame = 1
    
    # Start loop
    for frame in range(1):
        # Capture the environment with the ZED camera
        image, depth_map, normal_map, point_cloud = zed_manager.get_zed_image(zed, save=True)

        # Filter the plants from the background
        mask = find_plant.filter_plants(image, default_T=50, save_mask=True)
        
        # Divide the plants into clusters
        masks, bounding_boxes = find_plant.segment_plants(mask, plants_number)
        find_plant.save_clustered_image(image, bounding_boxes)
        
        # Save bounding boxes to a txt file in crop_sensing/data/log.txt
        log_file = "crop_sensing/data/log.txt"
        with open(log_file, "w") as f:
            f.write("=== Bounding Box individuati ===")
        with open(log_file, "a") as f:
            for i, bbox in enumerate(bounding_boxes):
                f.write(f"Frame {frame}: {bbox}\n")
        
        # Extract the 3D points from the clusters
        bbxpts = []
        for m in masks:
            bbxpts.append(find_plant.get_3d_bbox(m, point_cloud))
        frame += 1
        
        # Communicate the bounding boxes to the cobot (only if the cobot is operated in another machine)
        if bbxpts is not None:
            cobot_manager.send_cobot_map(linux_ip, bbxpts)

    zed.close()
    
    # Create point cloud (this will create a .ply file by taking a video of the environment)
    #create_plc.record_and_save(plant_name='piantina1', frames=300)



if __name__ == "__main__":
    main()
    