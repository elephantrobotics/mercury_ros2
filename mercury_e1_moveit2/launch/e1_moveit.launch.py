from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, SetParameter
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    use_sim_time = LaunchConfiguration("use_sim_time")
    start_sync_bridge = LaunchConfiguration("start_sync_bridge")
    sync_real_robot = LaunchConfiguration("sync_real_robot")

    robot_port = LaunchConfiguration("port")
    robot_baud = LaunchConfiguration("baud")
    robot_speed = LaunchConfiguration("robot_speed")

    package_share = FindPackageShare("mercury_e1_moveit2")

    return LaunchDescription([

        # ================= args =================
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false"
        ),

        DeclareLaunchArgument(
            "start_sync_bridge",
            default_value="true"
        ),

        DeclareLaunchArgument(
            "sync_real_robot",
            default_value="false"
        ),

        DeclareLaunchArgument("port", default_value="/dev/ttyUSB0"),
        DeclareLaunchArgument("baud", default_value="1000000"),
        DeclareLaunchArgument("robot_speed", default_value="30"),

        SetParameter(name="use_sim_time", value=use_sim_time),

        # ================= MoveIt core =================
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([package_share, "launch", "rsp.launch.py"])
            )
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([package_share, "launch", "static_virtual_joint_tfs.launch.py"])
            )
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([package_share, "launch", "move_group.launch.py"])
            )
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([package_share, "launch", "moveit_rviz.launch.py"])
            )
        ),

    ])