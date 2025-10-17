from setuptools import find_packages, setup

setup(
    name="elinor",
    version="0.0.20",
    author="Dashvvood",
    author_email="mathismottis@gmail.com",
    description="some util functions",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "tqdm",
        "dotenv",
        "deprecated",
    ],
    extra_require={
        "dev": [
            "pybase64",
            "pillow",
            "pandas",
            "pyyaml",
            "bs4",
            "requests",
            "regex",
            "rapidfuzz",
            "ffmpeg-python"
        ]
    }
)