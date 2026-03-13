import pathlib
from setuptools import find_packages, setup

# 直接读取 requirements.txt 文件，去除空行和注释
with pathlib.Path("requirements.txt").open() as requirements_txt:
    install_requires = [
        line.strip()
        for line in requirements_txt
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="flask_frame",
    version="1.1.39",
    author="wuhanchu",
    author_email="whcwuhanchu@gmail.com",
    description="基于FLASK快速开发REST接口框架",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=install_requires,
)
