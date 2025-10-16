from setuptools import setup, find_packages

setup(
    name="pylibcontroller",
    version="0.1.0",
    author="Berat",
    description="A Python library manager that automatically installs missing libraries",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pylibcontroller",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
