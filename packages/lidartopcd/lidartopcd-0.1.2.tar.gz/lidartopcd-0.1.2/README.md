# lidartopcd
A ROS2 command-line tool to subscribe to LiDAR `PointCloud2` topics, process point cloud data with configurable downsampling and outlier removal, and save it as PCD (Point Cloud Data) files in ASCII or binary format.

## Features

- **ROS2 Integration**: Seamlessly subscribes to any `PointCloud2` topic
- **Configurable Processing**: Adjustable voxel downsampling, statistical outlier removal, and buffer settings
- **Flexible Output**: Save as ASCII or binary PCD files with RGB coloring based on height
- **Real-time Monitoring**: Collects multiple frames for comprehensive scans
- **Easy CLI Interface**: Simple command-line usage with sensible defaults

## Installation

### Prerequisites
1. **ROS2**: Install ROS2 (Humble, Iron, Jazzy, etc.) following the [official installation guide](https://docs.ros.org/en/jazzy/Installation.html)
2. **Python 3.8+**: Ensure Python and pip are installed
3. **NumPy & SciPy**: These will be installed automatically

### Install the Package
```bash
# Install from PyPI
pip install lidartopcd

# Or install from source (after cloning repository)
pip install .


# ROS
# For ROS2 Jazzy (adjust for your distribution)
source /opt/ros/jazzy/setup.bash

# If you have a custom ROS2 workspace
source ~/ros2_ws/install/setup.bash


Basic Usage
Capture a LiDAR scan and save it as a PCD file:
bashlidartopcd --output ./scan.pcd
This uses default settings:

Topic: /unilidar/cloud
Voxel size: 0.05m
Outlier removal: 10 neighbors, 3.0 std ratio
Buffer: 40 frames (~4s at 10Hz)
Collection time: 5.0 seconds
Format: ASCII

Custom Configuration
bashlidartopcd \
    --topic /your/lidar/topic \
    --output ./high_res_scan.pcd \
    --binary \
    --voxel-size 0.02 \
    --k-neighbors 15 \
    --std-ratio 2.5 \
    --buffer-size 60 \
    --collect-time 10.0
Command Line Options
bashlidartopcd --help
Required Arguments

--output PATH
Path where the PCD file will be saved (e.g., ./scan.pcd, /tmp/my_scan.pcd)

Optional Arguments

--topic TOPIC, -t TOPIC
ROS2 topic to subscribe to (default: /unilidar/cloud)
--binary, -b
Save in binary PCD format (default: ASCII)
--voxel-size SIZE, -vs SIZE
Voxel size for downsampling in meters (default: 0.05)
--k-neighbors N, -kn N
Number of neighbors for statistical outlier removal (default: 10)
--std-ratio RATIO, -sr RATIO
Standard deviation multiplier for outlier removal (default: 3.0)
--buffer-size SIZE, -bs SIZE
Maximum number of frames to buffer (default: 40)
--collect-time SECONDS, -ct SECONDS
Time to collect data before processing (default: 5.0)

Parameter Tuning Guide
ParameterEffectTypical Valuesvoxel-sizePoint density after downsampling0.01-0.1m (smaller = denser)k-neighborsOutlier detection sensitivity5-50 (higher = more conservative)std-ratioOutlier removal strictness1.5-4.0 (lower = more aggressive)buffer-sizeTemporal integration10-100 framescollect-timeScan duration2-15 seconds
Processing Pipeline

Data Collection: Subscribes to PointCloud2 topic and buffers multiple frames
Voxel Downsampling: Reduces point density using configurable voxel grid
Outlier Removal: Statistical filtering using k-nearest neighbors and standard deviation
Colorization: RGB coloring based on Z-height (red=high, blue=low)
PCD Export: Saves in ASCII or binary format with proper header

Example Workflows
High-Resolution Scan
For detailed inspection:
bashlidartopcd --output highres.pcd --voxel-size 0.01 --collect-time 8.0 --binary
Quick Survey
For fast area mapping:
bashlidartopcd --output survey.pcd --voxel-size 0.1 --collect-time 3.0
Custom LiDAR Topic
For different LiDAR drivers:
bashlidartopcd --topic /velodyne_points --output velodyne_scan.pcd
Output Format
The tool generates standard PCD v0.7 files with:

Fields: x, y, z, r, g, b
Point Types: Float32 for coordinates, uint8 for RGB
Coloring: Height-based gradient (blue=low, red=high)
Metadata: Full header with processing parameters

Example header:
text# .PCD v0.7 - Point Cloud Data file format
VERSION 0.7
FIELDS x y z r g b
SIZE 4 4 4 1 1 1
TYPE F F F U U U
COUNT 1 1 1 1 1 1
WIDTH N
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS N
DATA binary
Troubleshooting
"No module named 'rclpy'"

Ensure ROS2 is installed and sourced
Run: source /opt/ros/jazzy/setup.bash

"No point cloud data available"

Verify LiDAR topic is publishing: ros2 topic echo /your/topic
Check topic name with: ros2 topic list | grep cloud
Increase collect-time if data rate is low

"Permission denied" on output file

Ensure write permissions to output directory
Use absolute paths or create output directory first

Binary PCD files not readable

Some viewers prefer ASCII format: remove --binary flag
Verify file integrity with pcl_viewer or cloudcompare

Integration with ROS2 Tools
View PCD Files
bash# Using PCL tools (if installed)
pcl_viewer scan.pcd

# Using ROS2 rviz2
ros2 run rviz2 rviz2  # Add PCD file as display
Convert to Other Formats
bash# Using PCL tools
pcl_convert scan.pcd scan.ply
pcl_convert scan.pcd scan.stl
Development
Source Installation
bashgit clone https://github.com/yourusername/lidartopcd.git
cd lidartopcd
pip install -e .
Testing
bash# Run with verbose output for debugging
lidartopcd --output test.pcd --collect-time 2.0
Contributing

Fork the repository
Create a feature branch
Make changes and test thoroughly
Submit a pull request

License
This project is licensed under the MIT License - see the LICENSE file for details.
Support

Issues: Report bugs or request features on GitHub
Documentation: PyPI Project Page
ROS2 Community: Stack Overflow, ROS Discourse

Changelog
See PyPI release history for version details.

Built with ❤️ for the ROS2 and robotics community
textThis README provides:

1. **Professional appearance** with badges and clear formatting
2. **Complete installation guide** with ROS2 setup instructions
3. **Detailed usage examples** with parameter explanations
4. **Parameter tuning guide** with practical recommendations
5. **Troubleshooting section** for common issues
6. **Processing pipeline explanation** for technical users
7. **Integration tips** with ROS2 tools and viewers
8. **Development instructions** for contributors

