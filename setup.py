from setuptools import setup, find_packages

setup(
    name="gdpython",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6==6.8.1",
        "PyQt6-Qt6==6.8.2",
        "PyQt6_sip==13.10.0",
        "pygame"
    ],
    author="Michael Lutz",
    author_email="michel.lutz92@gmail.com",
    description="GDPython ist eine QT6/Python basierte Game Engine für die einfache Erstellung von 2D-Spielen.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Michael0992/GDPython",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Games/Entertainment :: Game Development",
    ],
    python_requires=">=3.6",
)
