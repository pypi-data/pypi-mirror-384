import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "jjrawlins-cdk-ami-builder",
    "version": "0.0.56",
    "description": "Creates an EC2 AMI using an Image Builder Pipeline and returns the AMI ID.",
    "license": "Apache-2.0",
    "url": "https://github.com/JaysonRawlins/cdk-ami-builder.git",
    "long_description_content_type": "text/markdown",
    "author": "Jayson Rawlins<jayson.rawlins@gmail.com>",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/JaysonRawlins/cdk-ami-builder.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "jjrawlins_cdk_ami_builder",
        "jjrawlins_cdk_ami_builder._jsii"
    ],
    "package_data": {
        "jjrawlins_cdk_ami_builder._jsii": [
            "cdk-ami-builder@0.0.56.jsii.tgz"
        ],
        "jjrawlins_cdk_ami_builder": [
            "py.typed"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "aws-cdk-lib>=2.85.0, <3.0.0",
        "constructs>=10.0.5, <11.0.0",
        "jsii>=1.116.0, <2.0.0",
        "publication>=0.0.3",
        "typeguard>=2.13.3,<4.3.0"
    ],
    "classifiers": [
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Typing :: Typed",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved"
    ],
    "scripts": []
}
"""
)

with open("README.md", encoding="utf8") as fp:
    kwargs["long_description"] = fp.read()


setuptools.setup(**kwargs)
