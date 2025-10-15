#!/usr/bin/env python
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()


setup_args = dict(
    name="ta_sites",
    version="0.5.4",
    packages=[
        "ta_sites",
        "ta_sites.central_reach",
        "ta_sites.basic",
        "ta_sites.quickbooks",
        "ta_sites.salesforce",
        "ta_sites.versant",
        "ta_sites.always_care",
    ],
    author="Serhii Romanets",
    author_email="serhii.romanets@thoughtful.ai",
    description="TA Sites",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.thoughtfulautomation.com/",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords="ta_sites",
    include_package_data=True,
    zip_safe=False,
)

install_requires = [
    "requests",
    "datetime",
    "retry",
]

if __name__ == "__main__":
    setup(**setup_args, install_requires=install_requires)
