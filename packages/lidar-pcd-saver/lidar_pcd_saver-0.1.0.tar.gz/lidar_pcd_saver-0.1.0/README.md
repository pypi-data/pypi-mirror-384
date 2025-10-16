This is displayed on your PyPI project page. Use Markdown for formatting.
text# lidar-pcd-saver

A ROS2 tool to subscribe to a LiDAR PointCloud2 topic, process the data (with configurable downsampling and outlier removal), and save it as a PCD file.

## Installation

1. Install ROS2 (e.g., Jazzy) from the official docs: https://docs.ros.org/en/jazzy/Installation.html. This provides `rclpy` and `sensor_msgs`.
2. Install the package:
pip install lidar-pcd-saver
text**Note:** Source your ROS2 setup before use: `source /opt/ros/jazzy/setup.bash` (adjust for your ROS2 distro).

## Usage

Run as a CLI tool:
Basic (defaults: voxel-size=0.05, k-neighbors=10, std-ratio=3.0, buffer-size=40, collect-time=5.0)
lidar-pcd-saver --output /path/to/output.pcd
With custom options
lidar-pcd-saver 
--topic /your/lidar/topic 
--output /path/to/output.pcd 
--binary 
--voxel-size 0.1 
--k-neighbors 20 
--std-ratio 2.5 
--buffer-size 60 
--collect-time 10.0
textSee `--help` for all options.

## Requirements
- Python 3.8+
- NumPy
- SciPy
- ROS2 (for rclpy and sensor_msgs)

## License
MIT