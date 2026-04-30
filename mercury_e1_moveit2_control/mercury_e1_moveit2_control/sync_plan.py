#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROS2 node for synchronizing RViz joint states with a Mercury E1 robot.

This module subscribes to the "joint_states" topic from RViz, converts
the received joint positions from radians to degrees, and sends them
to the Mercury E1 robotic arm. It ensures that the pymycobot
library version meets the minimum requirement.

Author: weijian.wang
Date: 2026-04-24
"""
import time
import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import pymycobot
from packaging import version

# Minimum required pymycobot library version
MIN_REQUIRE_VERSION = '4.0.4'

CURRENT_VERSION = pymycobot.__version__
print(f'current pymycobot library version: {CURRENT_VERSION}')
if version.parse(CURRENT_VERSION) < version.parse(MIN_REQUIRE_VERSION):
    raise RuntimeError(
        f'The version of pymycobot library must be greater than {MIN_REQUIRE_VERSION} or higher. '
        'The current version is {CURRENT_VERSION}. Please upgrade the library version.')
else:
    print('pymycobot library version meets the requirements!')
    from pymycobot import MercuryE1


class SliderSubscriber(Node):
    """ROS2 node for subscribing to joint states and controlling Mercury E1.

    This node listens to the "joint_states" topic, processes the data into
    degrees according to RViz order, and sends the joint angles to the robot.

    Attributes:
        subscription (rclpy.subscription.Subscription): Subscription to the
            "joint_states" topic.
        rviz_order (list[str]): List of joint names in the expected RViz order.
    """

    def __init__(self):
        """Initialize the Slider_Subscriber node and set up connections."""
        super().__init__("control_sync_plan")
        self.subscription = self.create_subscription(
            JointState,
            "joint_states",
            self.listener_callback,
            10
        )

        # Declare robot connection parameters
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baud', 1000000)

        port = self.get_parameter("port").get_parameter_value().string_value
        baud = self.get_parameter("baud").get_parameter_value().integer_value

        self.get_logger().info("port:%s, baud:%d" % (port, baud))
        self.mercury_e1 = MercuryE1(port, baud)
        time.sleep(0.05)
        if self.mercury_e1.is_power_on !=1:
            self.mercury_e1.power_on()
        time.sleep(0.05)
        if self.mercury_e1.get_fresh_mode() != 1:
            self.mercury_e1.set_fresh_mode(1)
        time.sleep(0.05)
        self.mercury_e1.set_limit_switch(2, 0)
        
        # Joint order in RViz
        self.rviz_order = ['Joint1', 'Joint2', 'Joint3', 'Joint4', 
                           'Joint5', 'Joint6', 'Joint7']
        self.last_time = time.time()
        self.last_angles = None

    def listener_callback(self, msg):
        """Callback to process received joint states.

        Converts joint positions from radians to degrees, rearranges them
        according to the RViz order, and sends them to the robot.

        Args:
            msg (JointState): The message containing joint names and positions.
        """
        now = time.time()

        # Frequency Limit 20Hz
        if now - self.last_time < 0.05:
            return
        
        # Create a mapping of joint names to their position values
        joint_state_dict = {name: msg.position[i]
                            for i, name in enumerate(msg.name)}

        # Rearrange joint angles according to RViz order
        data_list = []
        for joint in self.rviz_order:
            if joint in joint_state_dict:
                radians_to_angles = round(
                    math.degrees(joint_state_dict[joint]), 2)
                data_list.append(radians_to_angles)
        
        # Channge Filtering
        if self.last_angles:
            diff = max(abs(a - b) for a, b in zip(data_list, self.last_angles))
            if diff < 1.0:   # Orders under 1 degree will not be shipped
                return

        self.last_angles = data_list
        self.last_time = now
        
        self.get_logger().info(f'joint_angles: {data_list}')
        self.mercury_e1.send_angles(data_list, 25)


def main(args=None):
    """Entry point for the ROS2 node.

    Initializes the ROS2 system, creates the SliderSubscriber node,
    and keeps it running until shutdown.

    Args:
        args (list[str], optional): Command-line arguments for ROS2.
            Defaults to None.
    """
    rclpy.init(args=args)
    slider_subscriber = SliderSubscriber()

    rclpy.spin(slider_subscriber)

    slider_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
