from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hawkeyezero",
    version="1.0.0",
    description="Hawkeye-Zero - special trained model to detect 11 diffrent types of space debris. The idea wasn’t to build a perfect system — just to explore how far object detection can go in real-world space debris applications. Also very important thing was to care about easy and quick access to use model functions and data, so I've created special structure for this project to allowed developers to use model in diffrent environments in API's or as a simple python tool.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    project_urls={
      
        "Source Code & Docs" :"https://github.com/Gabrli/Hawkeye-Zero",
    },
    keywords="yolo, computer vision, deep learning, machine learning, object detection, python, automation, data science, ai, neural networks, image processing, data preparation",
    packages=find_packages(),
    author="Gabriel Wiśniewski",
    author_email="gabrys.wisniewski@op.pl",
    classifiers=[
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "Topic :: Software Development :: Libraries",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Operating System :: OS Independent",
    ],
    install_requires=[
     "pyyaml",
    ],
  
)