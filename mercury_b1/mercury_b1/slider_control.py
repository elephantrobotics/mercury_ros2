import rclpy
from pymycobot.mercury import Mercury
from rclpy.node import Node
from sensor_msgs.msg import JointState
import math
import time
import traceback


# 限制频率的时间间隔
UPDATE_INTERVAL = 0.1  # 10 Hz

# 上一次更新的时间戳
last_update_time = 0

class Slider_Subscriber(Node):
    def __init__(self):
        super().__init__("control_slider")
        self.subscription = self.create_subscription(
            JointState,
            "joint_states",
            self.listener_callback,
            10
        )
        self.subscription
     
        # left arm
        self.l = Mercury("/dev/left_arm", 115200)
        # right arm
        self.r = Mercury("/dev/right_arm", 115200)
        self.l.set_movement_type(0) # 速度融合2 很耗时
        self.r.set_movement_type(0)
        time.sleep(0.05)
        
    def listener_callback(self, msg):
        global last_update_time

        current_time = time.time()
        if current_time - last_update_time < UPDATE_INTERVAL:
            return  # 如果间隔时间不足，跳过此次更新

        last_update_time = current_time

        data_list = []
        for index, value in enumerate(msg.position):
            radians_to_angles = round(math.degrees(value), 2)
            data_list.append(radians_to_angles)
            
        # print('data_list: {}'.format(data_list))
        
        left_arm = data_list[:7]
        right_arm = data_list[7:-3]
        middle_arm = data_list[-3:]
        
        print('left_angles: {}, right_angles: {}, middle_angles: {}'.format(left_arm, right_arm, middle_arm))
        try:
            self.l.send_angles(left_arm, 80, _async=True)
            self.r.send_angles(right_arm, 80, _async=True)
            self.r.send_angle(11, middle_arm[0], 80, _async=True)
            self.r.send_angle(12, middle_arm[1], 80, _async=True)
            self.r.send_angle(13, middle_arm[2], 80, _async=True)
        except Exception as e:
            e = traceback.format_exc()
            print("Failed to send angles: {}".format(e))



def main(args=None):
    rclpy.init(args=args)
    slider_subscriber = Slider_Subscriber()
    
    rclpy.spin(slider_subscriber)
    
    slider_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
