from pkg_resources import parse_requirements
from setuptools import setup

install_reqs = parse_requirements('./requirements.txt')
print("install_reqs",install_reqs)
reqs = [str(ir.req) for ir in install_reqs]


setup(
    name='flask_rest_frame',
    version='1.0',
    author='wuhanchu',
    author_email='whcwuhanchu@gmail.com',
    description=u'基于FLASK快速开发REST接口框架',
    packages=['jujube_pill'],
    install_requires=reqs
)