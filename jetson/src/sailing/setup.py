from setuptools import find_packages, setup

setup(
    name="sailing",
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/sailing"]),
        ("share/sailing", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    tests_require=["pytest"],
    zip_safe=True,
    maintainer="ericcai32",
    maintainer_email="ericcai32@gmail.com",
    description="Scripted sailing commands and project Teensy communication.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "reinforcement_learning_node = sailing.reinforcement_learning.reinforcement_learning_node:main",
            "teensy_node = sailing.teensy.teensy_node:main",
        ]
    },
)
