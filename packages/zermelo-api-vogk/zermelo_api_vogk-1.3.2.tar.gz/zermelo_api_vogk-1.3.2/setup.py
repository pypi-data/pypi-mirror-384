from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="zermelo_api_vogk",
    version="1.3.2",
    description="A small module to create a Zermelo accesstoken and put some data from Zermelo in dataclasses",
    package_dir={"": "app"},
    packages=find_packages(where="app"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KlaasVogel/zermelo_api_vogk",
    author="Klaas Vogel",
    author_email="zermelo_api@klaasvogel.nl",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    install_requires=["aiohttp"],
    extras_require={
        "dev": [],
    },
    python_requires=">=3.12",
)
