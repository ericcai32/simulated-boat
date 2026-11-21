from setuptools import find_packages, setup

setup(
    name="simulation",
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/simulation"]),
        ("share/simulation", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    tests_require=["pytest"],
    zip_safe=True,
    maintainer="ericcai32",
    maintainer_email="ericcai32@gmail.com",
    description="Repeatable sensor data and delayed actuator feedback.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": ["simulation_node = simulation.simulation_node:main"]
    },
)
