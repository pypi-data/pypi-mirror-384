from setuptools import setup, find_packages

setup(
    name="weatherclient-eldar",
    version="0.1.0",
    description="Simple Python client for OpenWeatherMap API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Eldar Eliyev",
    author_email="eldar@example.com",
    url="https://github.com/eldar/weatherclient",
    packages=find_packages(),
    install_requires=["requests"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
