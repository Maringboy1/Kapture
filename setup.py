from setuptools import setup, find_packages

setup(
    name="kapture",
    version="1.0.0",
    description="Modern screenshot and screen recording tool for Kali Linux (X11)",
    author="Komo",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "PyQt6>=6.4.0",
        "Pillow>=9.0.0",
    ],
    entry_points={
        "console_scripts": [
            "kapture = kapture.__main__:main",
        ],
    },
    include_package_data=True,
)
