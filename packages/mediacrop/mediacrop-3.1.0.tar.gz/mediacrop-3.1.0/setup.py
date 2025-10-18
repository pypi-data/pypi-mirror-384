from setuptools import setup

setup(
    name="mediacrop",
    version="3.1.0",
    author="Mallik Mohammad Musaddiq",
    author_email="mallikmusaddiq1@gmail.com",
    description="A CLI tool featuring a localhost web interface for visually determining FFmpeg crop coordinates of any media file.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/mallikmusaddiq1/mediacrop",
    license="MIT",
    py_modules=["mediacrop", "http_handler", "utils"],  # yeh important hai, sab ek folder me hai
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "mediacrop=mediacrop:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Multimedia :: Video",
        "Topic :: Multimedia :: Graphics :: Editors",
        "Topic :: Utilities",
    ],
)