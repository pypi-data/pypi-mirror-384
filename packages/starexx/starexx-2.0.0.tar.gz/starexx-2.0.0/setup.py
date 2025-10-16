from setuptools import setup, find_packages

setup(
    name="starexx",
    version="2.0.0",
    author="Ankit Mehta",
    author_email="starexx.m@gmail.com",
    description="Beginner-Friendly syntax python module",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://realstarexx.github.io/docs",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
