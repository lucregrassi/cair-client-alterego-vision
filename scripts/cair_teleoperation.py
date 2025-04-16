import rospy
from geometry_msgs.msg import Twist
import socket
import threading
import time

class CairTeleoperation:
    def __init__(self, command_port=54321):
        # ROS publisher
        self.pub = rospy.Publisher('/robot_alterego6/cmd_vel', Twist, queue_size=10)
        rospy.init_node('cair_teleoperation', anonymous=False)

        # UDP configuration
        self.command_port = command_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', self.command_port))
        self.running = False

        # Gradual increment settings
        self.increment_step = 0.1  # Step size for incremental updates
        self.sleep_time = 0.1  # Time (seconds) between increments

    def start_udp_listener(self):
        self.running = True
        thread = threading.Thread(target=self.udp_listener)
        thread.start()

    def udp_listener(self):
        while self.running:
            try:
                data, addr = self.socket.recvfrom(1024)
                command = data.decode('utf-8').strip()
                rospy.loginfo(f"Received command: {command}")
                self.handle_command(command)
            except Exception as e:
                rospy.logerr(f"Error in UDP listener: {e}")

    def handle_command(self, command):
        target_linear = 0.0
        target_angular = 0.0

        if command == "MOVE_FORWARD":
            target_linear = 1.0
        elif command == "MOVE_BACKWARD":
            target_linear = -1.0
        elif command == "ROTATE_LEFT":
            target_angular = 0.3
        elif command == "ROTATE_RIGHT":
            target_angular = -0.3
        elif command == "STOP":
            twist_msg = Twist()
            twist_msg.linear.x = 0.0
            twist_msg.angular.z = 0.0
            self.pub.publish(twist_msg)
            rospy.loginfo("Published STOP command.")
            return
        else:
            rospy.logwarn(f"Unknown command: {command}")
            return

        # Gradually adjust velocities
        current_linear = 0.0
        current_angular = 0.0

        while abs(current_linear - target_linear) > self.increment_step or abs(current_angular - target_angular) > self.increment_step:
            if current_linear < target_linear:
                current_linear = min(current_linear + self.increment_step, target_linear)
            elif current_linear > target_linear:
                current_linear = max(current_linear - self.increment_step, target_linear)

            if current_angular < target_angular:
                current_angular = min(current_angular + self.increment_step, target_angular)
            elif current_angular > target_angular:
                current_angular = max(current_angular - self.increment_step, target_angular)

            # Publish the updated Twist message
            twist_msg = Twist()
            twist_msg.linear.x = current_linear
            twist_msg.angular.z = current_angular
            self.pub.publish(twist_msg)
            rospy.loginfo(f"Published incremental message: {twist_msg}")

            time.sleep(self.sleep_time)  # Delay between increments
                    # Final adjustment to ensure exact target values

    def stop_udp_listener(self):
        self.running = False
        self.socket.close()


if __name__ == "__main__":
    manager = CairTeleoperation()
    try:
        rospy.loginfo("Starting UDP listener...")
        manager.start_udp_listener()
        rospy.spin()  # Keep the ROS node running
    except rospy.ROSInterruptException:
        rospy.loginfo("Shutting down CairTeleoperation.")
        manager.stop_udp_listener()
