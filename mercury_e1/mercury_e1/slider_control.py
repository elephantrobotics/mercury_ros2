import rclpy
from pymycobot.mercury_e1 import MercuryE1
from rclpy.node import Node
from sensor_msgs.msg import JointState
import math
import time

class Slider_Subscriber(Node):
    """ROS2 node that subscribes to joint states and sends commands to Mercury E1."""
    def __init__(self):
        super().__init__("control_slider")
        self.subscription = self.create_subscription(
            JointState,
            "joint_states",
            self.listener_callback,
            10
        )
        
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
        self.mercury_e1.set_limit_switch(2, 0)

        self.last_time = time.time()
        self.last_angles = None
        
    def listener_callback(self, msg: JointState):
        """Handle received joint state messages and send angles to the robot.

        Args:
            msg (JointState): ROS2 JointState message containing joint positions
                in radians.

        Returns:
            None
        """
        now = time.time()

        # Frequency Limit 20Hz
        if now - self.last_time < 0.05:
            return

        data_list = []
        for value in msg.position:
            angle = round(math.degrees(value), 1)
            data_list.append(angle)

        # Channge Filtering
        if self.last_angles:
            diff = max(abs(a - b) for a, b in zip(data_list, self.last_angles))
            if diff < 1.0:   # Orders under 1 degree will not be shipped
                return

        self.last_angles = data_list
        self.last_time = now

        self.get_logger().info('joint_angles: {}'.format(data_list))
        self.mercury_e1.send_angles(data_list, 25)


def main(args=None):
    """Main entry point for the Slider_Subscriber node.

    Args:
        args (list, optional): Command-line arguments for ROS2. Defaults to None.

    Returns:
        None
    """
    rclpy.init(args=args)
    slider_subscriber = Slider_Subscriber()

    rclpy.spin(slider_subscriber)

    slider_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
