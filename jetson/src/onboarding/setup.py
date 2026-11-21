from setuptools import find_packages, setup

setup(
    name="onboarding",
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/onboarding"]),
        ("share/onboarding", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    tests_require=["pytest"],
    zip_safe=True,
    maintainer="ericcai32",
    maintainer_email="ericcai32@gmail.com",
    description="Worked example and member onboarding nodes.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "no_go_band_node = onboarding.no_go_band_node:main",
            "chloe_node = onboarding.chloe_node:main",
            "matteus_node = onboarding.matteus_node:main",
            "yul_node = onboarding.yul_node:main",
            "dylan_node = onboarding.dylan_node:main",
        ]
    },
)
