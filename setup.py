from setuptools import find_packages, setup, version

setup(
    name="musicbot",
    version="0.0.1",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    entry_points={
        "console_scripts": [
            "musicbot=musicbot.musicbot:main",
        ],
    },
)
