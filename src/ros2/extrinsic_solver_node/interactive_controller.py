#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from vision_msgs.msg import (Detection2D, Detection2DArray, Detection3D,
                             Detection3DArray)

from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from typing import Dict, List, Optional, Tuple
import threading

class InteractiveController(Node):
    def __init__(self):
        # QoS profile for reliable communication
        qos_profile = QoSProfile(
            # reliability=ReliabilityPolicy.RELIABLE,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.latest_aruco_detection: Optional[Detection2DArray] = None
        self.latest_board_detection: Optional[Detection3DArray] = None

        self.aruco_buffer = []
        self.board_buffer = []

        super().__init__('interactive_controller')

        # Publisher_
        self.publisher_aruco = self.create_publisher(Detection2DArray, '/calibration/collect_trigger/aruco_detections', qos_profile)
        self.publisher_board = self.create_publisher(Detection3DArray, '/calibration/collect_trigger/calibration_board_detections', qos_profile)
        self.get_logger().info("Interactive controller started. Press 'a' + Enter to collect data.")

        # Subscribers
        self.aruco_subscription = self.create_subscription(
            Detection2DArray, "/calibration/aruco_locator/aruco_detections", self.aruco_callback, qos_profile
        )

        self.board_subscription = self.create_subscription(
            Detection3DArray,
            "/calibration/lidar_board_detector/calibration_board_detections",
            self.board_callback,
            qos_profile,
        )

        self.create_timer(0.1, self.publish)  # 每 0.1 秒跑一次

        # 啟動互動執行緒
        thread = threading.Thread(target=self.interactive_loop, daemon=True)
        thread.start()


        # while rclpy.ok():
        #     if self.latest_aruco_detection is not None:
        #         self.publisher_aruco.publish(self.latest_aruco_detection)
        #         print(f"send latest_aruco_detection msg")

        #     if self.latest_board_detection is not None:
        #         self.publisher_board.publish(self.latest_board_detection)
        #         print(f"send latest_board_detection msg")

        #     key = input("Press 'a' to collect data, or 'q' to quit: ").strip().lower()
        #     if key == 'a':
        #         self.publisher_.publish(Bool(data=True))
        #         self.get_logger().info("Triggered data collection.")
        #     elif key == 'q':
        #         self.get_logger().info("Exiting controller.")
        #         break
    
    def interactive_loop(self):
        while rclpy.ok():
            cmd = input("Press 'a' to accept, 'd' to discard, 'q' to quit: ").strip().lower()
            if cmd == 'a':
                if self.latest_aruco_detection and self.latest_board_detection:
                    self.aruco_buffer.append(self.latest_aruco_detection)
                    self.board_buffer.append(self.latest_board_detection)
                    print(f"current buffer size: {len(self.aruco_buffer)}")
            elif cmd == 'd':
                    if len(self.aruco_buffer) > 0:
                        self.aruco_buffer.pop()
                        self.board_buffer.pop()
                        print(f"current buffer size: {len(self.aruco_buffer)}")
                    else:
                        print(f"Buffer is Empty!")
            elif cmd == 'q':
                self.get_logger().info("Exiting interactive controller")
                break

    def publish(self):
        for aruco, board in zip (self.aruco_buffer, self.board_buffer):
            if aruco is not None:
                self.publisher_aruco.publish(aruco)
            if board is not None:
                self.publisher_board.publish(board)
        # if self.latest_aruco_detection is not None:
        #     self.publisher_aruco.publish(self.latest_aruco_detection)
        #     # self.get_logger().info("Published latest ArUco detection")

        # if self.latest_board_detection is not None:
        #     self.publisher_board.publish(self.latest_board_detection)
        #     # self.get_logger().info("Published latest Board detection")

        

    def aruco_callback(self, msg: Detection2DArray):
        """
        Handle ArUco detection messages.

        Educational note: ArUco markers provide precise 2D corner detections
        that correspond to known 3D marker geometry. These 2D-3D correspondences
        are essential for solving the PnP problem.
        """
        self.get_logger().debug(
            f"ArUco detection: {len(msg.detections)} markers at "
            f"t={msg.header.stamp.sec}.{msg.header.stamp.nanosec:09d}"
        )

        # Only cache non-empty detections
        if msg.detections:
            # with self.lock:
            print("get ArUco detection")
            self.latest_aruco_detection = msg

            # # Try to process if we have both detection types
            # self._try_solve_calibration()
        else:
            print("Ignoring empty ArUco detection")

    def board_callback(self, msg: Detection3DArray):
        """
        Handle board detection messages.

        Educational note: Board detections provide the 3D pose of the
        calibration board in LiDAR coordinates. This pose is used to
        transform marker coordinates from local to world space.
        """
        self.get_logger().debug(
            f"Board detection: {len(msg.detections)} boards at "
            f"t={msg.header.stamp.sec}.{msg.header.stamp.nanosec:09d}"
        )

        # Only cache non-empty detections
        if msg.detections:
            # with self.lock:
            self.latest_board_detection = msg
            print("get board detection")

            # # Try to process if we have both detection types
            # self._try_solve_calibration()
        else:
            print("Received empty board detection")

def main(args=None):
    rclpy.init(args=args)
    node = InteractiveController()
    try:
        rclpy.spin(node)   # 保持節點活著，觸發 callback
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    print(f"Hello world")
    main()
