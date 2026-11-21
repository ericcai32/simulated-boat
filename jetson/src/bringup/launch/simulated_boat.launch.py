from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    rate = {
        "publish_rate": ParameterValue(
            LaunchConfiguration("publish_rate"), value_type=float
        )
    }
    return LaunchDescription(
        [
            DeclareLaunchArgument("publish_rate", default_value="10.0"),
            DeclareLaunchArgument("dry_run", default_value="true"),
            DeclareLaunchArgument(
                "project",
                default_value="no_go_band",
                choices=["no_go_band", "chloe", "matteus", "yul", "dylan"],
            ),
            DeclareLaunchArgument("teensy_port", default_value=""),
            DeclareLaunchArgument("baud_rate", default_value="9600"),
            Node(
                package="simulation",
                executable="simulation_node",
                parameters=[rate],
                output="screen",
            ),
            Node(
                package="mission",
                executable="waypoint_node",
                parameters=[rate],
                output="screen",
            ),
            Node(
                package="sailing",
                executable="reinforcement_learning_node",
                parameters=[rate],
                output="screen",
            ),
            Node(
                package="onboarding",
                executable=[LaunchConfiguration("project"), "_node"],
                output="screen",
            ),
            Node(
                package="sailing",
                executable="teensy_node",
                parameters=[
                    {
                        "project": ParameterValue(
                            LaunchConfiguration("project"), value_type=str
                        ),
                        "dry_run": ParameterValue(
                            LaunchConfiguration("dry_run"), value_type=bool
                        ),
                        "teensy_port": ParameterValue(
                            LaunchConfiguration("teensy_port"), value_type=str
                        ),
                        "baud_rate": ParameterValue(
                            LaunchConfiguration("baud_rate"), value_type=int
                        ),
                    }
                ],
                output="screen",
            ),
        ]
    )
