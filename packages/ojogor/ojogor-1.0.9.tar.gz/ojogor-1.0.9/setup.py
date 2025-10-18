from setuptools import setup, find_packages

setup(
    name="ojogor",
    version="1.0.9",
    author="Starexx", 
    author_email="starexx.m@gmail.com",
    description="A simple python web framework",
    long_description="A simple python web framework for small web applications",
    url="https://github.com/realstarexx/ojogor",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License", 
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.7",
    install_requires=[],
)