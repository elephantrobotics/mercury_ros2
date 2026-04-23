import rclpy
import time
import traceback
import math
from pymycobot.mercury_e1 import MercuryE1
from rclpy.node import Node
from sensor_msgs.msg import JointState


class Talker(Node):
    def __init__(self):
        super().__init__("follow_display")


        # Declare robot connection parameters
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('buad', 1000000)

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
        
        self.mercury_e1.set_motor_enabled(254, 0)
        time.sleep(0.05)
        print("Rlease all servos over.\n")
        
        self.command_pub = self.create_publisher(
            msg_type=JointState,
            topic="joint_states",
            qos_profile=10
        )

    def publish_joint_command(self, angles_deg):
        """Mirror a 7-axis target to RVIZ as radians."""
        if self.command_pub is None:
            return

        command = JointState()
        command.header.stamp = self.get_clock().now().to_msg()
        command.name = ["Joint1", "Joint2", "Joint3", "Joint4", "Joint5", "Joint6", "Joint7"]
        command.position = [math.radians(value) for value in angles_deg[:7]]
        command.velocity = []
        command.effort = []
        self.command_pub.publish(command)
        
    def start(self):

        rate = self.create_rate(30)

        while rclpy.ok():
            rclpy.spin_once(self)
            try:
                # Get robot joint angles
                angles = self.mercury_e1.get_angles()
                if isinstance(angles, list) and len(angles) > 6:
                    self.publish_joint_command(angles)
                else:
                    self.get_logger().warn("Failed to get valid angles: {}".format(angles))

                rate.sleep()
            except Exception as e:
                e = traceback.format_exc()
                print(str(e))
        
def main(args=None):
    """Main function to run the Talker node.

    Args:
        args (list, optional): Command-line arguments for ROS2. Defaults to None.
    """
    rclpy.init(args=args)

    talker = Talker()
    talker.start()
    rclpy.spin(talker)

    talker.destroy_node()
    rclpy.shutdown()
    

if __name__ == "__main__":
    main()

