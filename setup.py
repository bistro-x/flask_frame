import  pkg_resources,pathlib
from setuptools import setup,find_packages

# install_reqs = parse_requirements('./requirements.txt')
# print("install_reqs",install_reqs)
# reqs = [str(ir.req) for ir in install_reqs]

with pathlib.Path('requirements.txt').open() as requirements_txt:
    install_requires = [
        str(requirement)
        for requirement
        in pkg_resources.parse_requirements(requirements_txt)
    ]

print(install_requires)

setup(
    name='flask_rest_frame',
    version='0.1.1',
    author='wuhanchu',
    author_email='whcwuhanchu@gmail.com',
    description=u'基于FLASK快速开发REST接口框架',
    packages= find_packages(),
    install_requires=install_requires
)