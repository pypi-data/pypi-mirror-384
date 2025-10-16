#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
import sensor_msgs_py.point_cloud2 as point_cloud2
import numpy as np
from collections import deque
import threading
import os
import time
from scipy.spatial import cKDTree
import argparse
import struct

class LidarPCDSaver(Node):
    def __init__(self, topic: str):
        super().__init__('lidar_pcd_saver')
        self.subscription = self.create_subscription(
            PointCloud2,
            topic,
            self.lidar_callback,
            10
        )
        self.lock = threading.Lock()
        self.frames_buffer = deque()
        self.last_received_time = None

    def __init__(self, topic: str, buffer_maxlen: int):
        super().__init__('lidar_pcd_saver')
        self.subscription = self.create_subscription(
            PointCloud2,
            topic,
            self.lidar_callback,
            10
        )
        self.lock = threading.Lock()
        self.frames_buffer = deque(maxlen=buffer_maxlen)
        self.last_received_time = None

    def lidar_callback(self, msg):
        try:
            points = point_cloud2.read_points_numpy(msg, field_names=["x", "y", "z"], skip_nans=True)
            with self.lock:
                self.frames_buffer.append(points)
                self.last_received_time = time.time()
        except Exception as e:
            print(f"Error in lidar_callback: {e}")

    def is_lidar_online(self):
        with self.lock:
            return self.last_received_time is not None and (time.time() - self.last_received_time) < 2.0

    def process_point_cloud(self, voxel_size: float, k_neighbors: int, std_ratio: float):
        try:
            with self.lock:
                if not self.frames_buffer:
                    print("No point cloud data available")
                    return None
                merged = np.vstack(list(self.frames_buffer))
                print(f"Merged {len(self.frames_buffer)} frames with {len(merged)} points")

            # Voxel downsampling
            min_bound = np.min(merged, axis=0)
            max_bound = np.max(merged, axis=0)
            n_voxels = np.ceil((max_bound - min_bound) / voxel_size).astype(int)
            voxel_grid = {}
            for point in merged:
                idx = tuple(np.floor((point - min_bound) / voxel_size).astype(int))
                voxel_grid.setdefault(idx, []).append(point)
            downsampled = [np.mean(voxel_grid[idx], axis=0) for idx in voxel_grid if voxel_grid[idx]]
            if not downsampled:
                print("No points after downsampling")
                return None
            points_array = np.array(downsampled)
            print(f"Downsampled to {len(points_array)} points")

            # Statistical outlier removal using cKDTree
            tree = cKDTree(points_array)
            distances, _ = tree.query(points_array, k=k_neighbors + 1)
            mean_distances = np.mean(distances[:, 1:], axis=1)
            global_mean = np.mean(mean_distances)
            global_std = np.std(mean_distances)
            inliers = mean_distances < (global_mean + std_ratio * global_std)
            points_array = points_array[inliers]
            print(f"After outlier removal: {len(points_array)} points")

            # Colorize based on height
            if points_array.shape[0] == 0:
                print("No points after processing")
                return None
            z_vals = points_array[:, 2]
            z_min, z_max = np.min(z_vals), np.max(z_vals)
            z_range = z_max - z_min if z_max != z_min else 1.0
            normalized = (z_vals - z_min) / z_range
            colors = np.zeros((points_array.shape[0], 3), dtype=np.uint8)
            colors[:, 0] = (normalized * 255).astype(np.uint8)  # Red
            colors[:, 2] = ((1.0 - normalized) * 255).astype(np.uint8)  # Blue
            return points_array, colors
        except Exception as e:
            print(f"Error processing point cloud: {e}")
            return None

    def save_pcd(self, file_path: str, binary: bool = False, 
                 voxel_size: float = 0.05, k_neighbors: int = 10, 
                 std_ratio: float = 3.0):
        try:
            processed = self.process_point_cloud(voxel_size, k_neighbors, std_ratio)
            if processed is None:
                print("No point cloud to save")
                return False
            points, colors = processed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            num_points = len(points)
            header = (
                "# .PCD v0.7 - Point Cloud Data file format\n"
                "VERSION 0.7\n"
                "FIELDS x y z r g b\n"
                "SIZE 4 4 4 1 1 1\n"
                "TYPE F F F U U U\n"
                "COUNT 1 1 1 1 1 1\n"
                f"WIDTH {num_points}\n"
                "HEIGHT 1\n"
                "VIEWPOINT 0 0 0 1 0 0 0\n"
                f"POINTS {num_points}\n"
                f"DATA {'binary' if binary else 'ascii'}\n"
            )

            if binary:
                with open(file_path, 'wb') as f:
                    f.write(header.encode('ascii'))
                    for pt, clr in zip(points, colors):
                        f.write(struct.pack('<fffBBB', pt[0], pt[1], pt[2], clr[0], clr[1], clr[2]))
            else:
                with open(file_path, 'w') as f:
                    f.write(header)
                    for pt, clr in zip(points, colors):
                        f.write(f"{pt[0]:.6f} {pt[1]:.6f} {pt[2]:.6f} {clr[0]} {clr[1]} {clr[2]}\n")

            print(f"Saved PCD to: {file_path}")
            return True
        except Exception as e:
            print(f"Error saving PCD: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(
        description="Save PCD from LiDAR subscription with configurable processing parameters."
    )
    parser.add_argument(
        '--topic', 
        type=str, 
        default='/unilidar/cloud', 
        help='ROS2 topic to subscribe to (default: /unilidar/cloud)'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        required=True, 
        help='Path to save the PCD file (e.g., /path/to/output.pcd)'
    )
    parser.add_argument(
        '--binary', 
        action='store_true', 
        help='Save in binary format (default: ascii)'
    )
    parser.add_argument(
        '--voxel-size',
        type=float,
        default=0.05,
        help='Voxel size for downsampling (default: 0.05 meters)'
    )
    parser.add_argument(
        '--k-neighbors',
        type=int,
        default=10,
        help='Number of neighbors for outlier removal (default: 10)'
    )
    parser.add_argument(
        '--std-ratio',
        type=float,
        default=3.0,
        help='Standard deviation ratio for outlier removal (default: 3.0)'
    )
    parser.add_argument(
        '--buffer-size',
        type=int,
        default=40,
        help='Buffer size for frames (default: 40, ~4 seconds at 10Hz)'
    )
    parser.add_argument(
        '--collect-time',
        type=float,
        default=5.0,
        help='Time to collect data before saving (default: 5.0 seconds)'
    )

    args = parser.parse_args()

    # Validate parameters
    if args.voxel_size <= 0:
        print("Error: voxel-size must be positive")
        return
    if args.k_neighbors < 1:
        print("Error: k-neighbors must be at least 1")
        return
    if args.std_ratio <= 0:
        print("Error: std-ratio must be positive")
        return
    if args.buffer_size <= 0:
        print("Error: buffer-size must be positive")
        return
    if args.collect_time <= 0:
        print("Error: collect-time must be positive")
        return

    print(f"Parameters:")
    print(f"  Topic: {args.topic}")
    print(f"  Output: {args.output}")
    print(f"  Format: {'binary' if args.binary else 'ascii'}")
    print(f"  Voxel size: {args.voxel_size}m")
    print(f"  K neighbors: {args.k_neighbors}")
    print(f"  Std ratio: {args.std_ratio}")
    print(f"  Buffer size: {args.buffer_size}")
    print(f"  Collect time: {args.collect_time}s")

    rclpy.init()
    node = LidarPCDSaver(args.topic, buffer_size=args.buffer_size)

    # Spin in a separate thread to collect data
    thread = threading.Thread(target=lambda: rclpy.spin(node), daemon=True)
    thread.start()

    # Wait for data to accumulate
    print(f"Collecting data for {args.collect_time} seconds...")
    time.sleep(args.collect_time)

    # Wait a bit more to ensure we have recent data
    if not node.is_lidar_online():
        print("Warning: LiDAR appears offline, data might be stale")

    # Save the PCD
    success = node.save_pcd(
        args.output, 
        binary=args.binary,
        voxel_size=args.voxel_size,
        k_neighbors=args.k_neighbors,
        std_ratio=args.std_ratio
    )

    if success:
        print("PCD saved successfully!")
    else:
        print("Failed to save PCD")

    # Shutdown
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()