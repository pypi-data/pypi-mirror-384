import os
import sys

from setuptools import find_packages
from setuptools import setup

this_dir = os.path.dirname(__file__)
sys.path.append(this_dir)


def read(fname):
    return open(os.path.join(this_dir, fname)).read()


install_requires = [
    "boto3==1.35.54",
    "botocore==1.35.54",
    "jmespath==1.0.1",
    "python-dateutil==2.9.0.post0",
    "s3transfer==0.10.3",
    "six==1.16.0",
    "urllib3==2.2.3",
]

setup(
    name="FireEye-AWS",
    version="0.6.0-dev",
    author="Hardik Nanda",
    author_email="hnanda21@gmail.com",
    description="AWS Monitoring Toolkit",
    license="Apache-2.0 License",
    keywords="fireeye aws cloudwatch logs logs-insights",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Environment :: Console",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.11",
        "Development Status :: 1 - Planning",
        "Topic :: Software Development",
    ],
    install_requires=install_requires,
    python_requires=">=3.8",
    entry_points={"console_scripts": ["fireeye = fireeye.__main__:main"]},
)
