import pkg_resources
import pathlib
from setuptools import find_packages, setup

with pathlib.Path("requirements.txt").open() as requirements_txt:
    install_requires = [
        str(requirement)
        for requirement in pkg_resources.parse_requirements(requirements_txt)
    ]

setup(
    name="flask_frame",
    version="0.4.16",
    author="wuhanchu",
    author_email="whcwuhanchu@gmail.com",
    description="基于FLASK快速开发REST接口框架",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=install_requires,
)
