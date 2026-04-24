#!/usr/bin/env python3
import math
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse, CancelResponse

from control_msgs.action import FollowJointTrajectory
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectoryPoint

from pymycobot import MercuryE1


JOINT_ORDER = [
    "Joint1", "Joint2", "Joint3",
    "Joint4", "Joint5", "Joint6", "Joint7"
]


class E1TrajectoryBridge(Node):

    def __init__(self):
        super().__init__("e1_trajectory_bridge")

        # ---------------- parameters ----------------
        self.declare_parameter("action_name", "/arm_group_controller/follow_joint_trajectory")
        self.declare_parameter("publish_topic", "/joint_states")
        self.declare_parameter("port", "/dev/ttyUSB0")
        self.declare_parameter("baud", 1000000)
        self.declare_parameter("speed", 40)
        self.declare_parameter("enable_real_robot", True)

        self.action_name = self.get_parameter("action_name").value
        self.topic = self.get_parameter("publish_topic").value
        self.speed = self.get_parameter("speed").value
        self.enable_real = self.get_parameter("enable_real_robot").value

        # ---------------- ROS ----------------
        self.pub = self.create_publisher(JointState, self.topic, 10)

        self.server = ActionServer(
            self,
            FollowJointTrajectory,
            self.action_name,
            execute_callback=self.execute_cb,
            goal_callback=self.goal_cb,
            cancel_callback=self.cancel_cb,
        )

        # ---------------- robot ----------------
        self.robot = None
        if self.enable_real:
            self.robot = MercuryE1(
                self.get_parameter("port").value,
                self.get_parameter("baud").value
            )

            if self.robot.is_power_on != 1:
                self.robot.power_on()

            self.robot.set_fresh_mode(1)

        self.last_pos = [0.0] * len(JOINT_ORDER)

        self.get_logger().info("E1 450-level trajectory bridge started")

    # =====================================================
    # Action callbacks
    # =====================================================
    def goal_cb(self, goal):
        if not goal.trajectory.points:
            self.get_logger().warn("Empty trajectory rejected")
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def cancel_cb(self, goal):
        self.get_logger().info("Trajectory cancel request")
        return CancelResponse.ACCEPT

    # =====================================================
    # Joint ordering (MoveIt -> robot)
    # =====================================================
    def reorder(self, names, positions):
        joint_map = {n: positions[i] for i, n in enumerate(names)}

        ordered = []
        for i, j in enumerate(JOINT_ORDER):
            ordered.append(joint_map.get(j, self.last_pos[i]))

        return ordered

    # =====================================================
    # publish RViz + robot
    # =====================================================
    def publish(self, positions):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = JOINT_ORDER
        msg.position = positions
        self.pub.publish(msg)

        self.last_pos = positions

        if self.robot:
            deg = [math.degrees(p) for p in positions]
            self.robot.send_angles(deg, self.speed)

    # =====================================================
    # core execution (450-style)
    # =====================================================
    def execute_cb(self, goal_handle):

        traj = goal_handle.request.trajectory
        joint_names = traj.joint_names

        start_t = time.monotonic()

        feedback = FollowJointTrajectory.Feedback()
        feedback.joint_names = JOINT_ORDER

        for point in traj.points:

            # ---------------- TIME CONTROL (核心) ----------------
            target = point.time_from_start.sec + point.time_from_start.nanosec * 1e-9

            while time.monotonic() - start_t < target:
                if goal_handle.is_cancel_requested:
                    goal_handle.canceled()
                    return FollowJointTrajectory.Result()
                time.sleep(0.001)

            # ---------------- reorder ----------------
            positions = self.reorder(joint_names, point.positions)

            # ---------------- execute ----------------
            self.publish(positions)

            # ---------------- feedback ----------------
            feedback.desired = point

            fb = JointTrajectoryPoint()
            fb.positions = positions
            feedback.actual = fb

            feedback.error = JointTrajectoryPoint()
            goal_handle.publish_feedback(feedback)

        goal_handle.succeed()

        result = FollowJointTrajectory.Result()
        return result


def main():
    rclpy.init()
    node = E1TrajectoryBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()