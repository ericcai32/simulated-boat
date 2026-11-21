# Docker setup

## Quick start

Start Docker. From the repository root on your host:

```bash
docker build -t simulated-boat-local jetson/setup
docker run -it --rm --name simulated-boat-dev -v "$(pwd)/jetson/src:/home/ros2_user/ros2_ws/src" simulated-boat-local
```

PowerShell: use `${PWD}/jetson/src` instead of `$(pwd)/jetson/src`.
The container builds and sources the workspace. Inside it, run the example:

```bash
ros2 launch bringup simulated_boat.launch.py
```

To inspect topics, open another host terminal:

```bash
docker exec -it simulated-boat-dev bash
ros2 topic list
ros2 topic echo /no_go_zone_band
```

## Launch your project

After editing, stop the launch with Ctrl-C. Inside the container:

```bash
colcon build --symlink-install
source install/setup.bash
ros2 launch bringup simulated_boat.launch.py project:=<name>
```

Replace `<name>` with your assigned node name. Use `no_go_band` for the example (default).
Each launch starts your selected node, the simulator, and the Teensy bridge.
No setup or launch-file edits are needed.

## Connect a Teensy

Replace the example serial port with your board's port. Add `project:=<name>` to
any launch command below to select your project; otherwise it runs `no_go_band`.

### Linux (native Docker Engine)

Add device forwarding to the Docker run command:

```bash
docker run -it --rm --name simulated-boat-dev --device=/dev/ttyACM0:/dev/ttyACM0 -v "$(pwd)/jetson/src:/home/ros2_user/ros2_ws/src" simulated-boat-local
```

Inside the container:

```bash
ros2 launch bringup simulated_boat.launch.py dry_run:=false teensy_port:=/dev/ttyACM0
```

Default baud: 9600. Override with `baud_rate:=...`.

### macOS / Windows (Docker Desktop)

Run the relay on your host, from the repository root.

**macOS — install once:**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r tools/requirements.txt
```

**macOS — each session:**

```bash
.venv/bin/python -m serial.tools.list_ports
.venv/bin/python tools/serial_relay.py --port /dev/cu.usbmodem123
```

**Windows PowerShell — install once:**

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r tools/requirements.txt
```

**Windows PowerShell — each session:**

```powershell
.\.venv\Scripts\python.exe -m serial.tools.list_ports
.\.venv\Scripts\python.exe tools/serial_relay.py --port COM3
```

Use the port shown by `list_ports`. Leave the relay running, start Docker normally,
then run inside the container:

```bash
ros2 launch bringup simulated_boat.launch.py dry_run:=false teensy_port:=socket://host.docker.internal:7000
```

No `-p` flag is needed. Change serial baud with the relay's `--baud-rate` option.

## Checks

Inside the container:

```bash
colcon test --return-code-on-test-failure
colcon test-result --verbose
ruff check src
ruff format --check src
```
