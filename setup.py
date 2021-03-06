import setuptools
import os

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="weather",
    version="0.0.0a0",
    author="Jack Luby",
    author_email="jack.o.luby@gmail.com",
    description="Personal weather forecasting CLI package.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "License :: Other/Proprietary License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    entry_points={
    'console_scripts': [f'{file[:-3]} = weather.{file[:-3]}:main' for file in os.listdir("src/weather") if file[-3:] == ".py"]
    },
    install_requires=[line.strip() for line in open("requirements.txt").readlines()]
)