from setuptools import setup, find_packages

setup(
    name="syngate",
    version="3.0.1", 
    author="henry",
    author_email="osas2henry@gmail.com",
    description="File-Based Queue, Scheduler, and Mutex Locker for Python (Windows, macOS, Linux)",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    include_package_data=True,
)
