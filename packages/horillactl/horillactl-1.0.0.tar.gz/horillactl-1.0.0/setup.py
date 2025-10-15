from setuptools import setup, find_packages

setup(
    name="horillactl",
    version="1.0.0",
    description="CLI tool to build and manage Horilla projects",
    author="Horilla Team",
    author_email="support@horilla.com",
    # url="https://github.com/horilla-opensource/horillactl",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "horillactl=horillactl.ctl:main",
        ],
    },
    install_requires=[],
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Build Tools",
    ],
)
