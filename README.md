# simulated-boat

CUSail's ROS 2 onboarding workspace with simulated boat data. [Docker setup](jetson/setup/README.md).

## Your project

Edit `jetson/src/onboarding/onboarding/<name>_node.py`. ROS startup and launch
setup are provided; fill in the `...` with your publishers, subscriptions, and logic.

For Teensy output, implement your `encode_<name>_output` function and add a
subscription in `jetson/src/sailing/sailing/teensy/teensy_node.py`.
See [launch commands](jetson/setup/README.md#launch-your-project).

## Example: no_go_band

`no_go_band_node.py` subscribes to `/wind_angle` and publishes `/no_go_zone_band`
(`UInt8`). Distance from the bow maps to bands 0–3: ≤45°, ≤90°, ≤135°, and ≤180°.
The Teensy packet is `[0xFF, band, 0xEE]`.

## Simulated topics

Scripted data publishes at 10 Hz. Waypoints advance within 3 meters and repeat;
buoy detections alternate 5 seconds on / 25 seconds silent. Actuator feedback
normally follows commands by 0.3 seconds and stays simulated when a Teensy is connected.

A repeating fault cycle includes excessive heel, capsizing, and stuck actuator feedback,
followed by recovery.

| Topics | ROS message | Contents |
| --- | --- | --- |
| `/gps` | `sensor_msgs/NavSatFix` | Latitude/longitude in decimal degrees |
| `/imu` | `geometry_msgs/Vector3` | x roll, y pitch, z yaw in degrees; yaw 0 north, 90 east |
| `/wind_angle` | `std_msgs/Int32` | 0–359°; bow 0, starboard 90, stern 180, port 270 |
| `/current_waypoint` | `interface/Waypoint` | id, latitude, longitude |
| `/buoy_position` | `geometry_msgs/Vector3` | Camera meters: x right, y down, z forward |
| `/mainsail_angle`, `/jib_angle` | `std_msgs/Int32` | 0–90°; all in to all out |
| `/rudder_angle` | `std_msgs/Int32` | −45° port through +45° starboard |
| `/jib_side_flag` | `std_msgs/UInt8` | 0 port, 1 starboard |
| `/received_mainsail_angle`, `/received_jib_angle` | `std_msgs/Int32` | Simulated sail feedback, 0–90° |
| `/received_rudder_angle` | `std_msgs/Int32` | Simulated rudder feedback, −45° to +45° |
| `/received_jib_side_flag` | `std_msgs/UInt8` | Simulated side feedback, 0 or 1 |


Scalar messages use `.data`.
