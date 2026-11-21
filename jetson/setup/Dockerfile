FROM ros:humble-ros-base-jammy
COPY --from=ghcr.io/astral-sh/ruff:0.14.6 /ruff /usr/local/bin/ruff
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash-completion python3-pytest python3-serial \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /home/ros2_user/ros2_ws
COPY setup_ros.sh /home/ros2_user/setup_ros.sh
RUN chmod +x /home/ros2_user/setup_ros.sh \
    && printf '\nsource /opt/ros/humble/setup.bash\nif [ -f /home/ros2_user/ros2_ws/install/setup.bash ]; then source /home/ros2_user/ros2_ws/install/setup.bash; fi\n' >> /etc/bash.bashrc
ENTRYPOINT ["/home/ros2_user/setup_ros.sh"]
CMD ["bash"]
