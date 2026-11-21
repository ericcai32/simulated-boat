from setuptools import find_packages, setup

setup(
    name="mission",
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/mission"]),
        ("share/mission", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    tests_require=["pytest"],
    zip_safe=True,
    maintainer="ericcai32",
    maintainer_email="ericcai32@gmail.com",
    description="Scripted target waypoint.",
    license="Apache-2.0",
    entry_points={"console_scripts": ["waypoint_node = mission.waypoint_node:main"]},
)
