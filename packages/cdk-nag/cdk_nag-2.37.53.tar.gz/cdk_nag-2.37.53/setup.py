import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "cdk-nag",
    "version": "2.37.53",
    "description": "Check CDK v2 applications for best practices using a combination on available rule packs.",
    "license": "Apache-2.0",
    "url": "https://github.com/cdklabs/cdk-nag.git",
    "long_description_content_type": "text/markdown",
    "author": "Arun Donti<donti@amazon.com>",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/cdklabs/cdk-nag.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "cdk_nag",
        "cdk_nag._jsii"
    ],
    "package_data": {
        "cdk_nag._jsii": [
            "cdk-nag@2.37.53.jsii.tgz"
        ],
        "cdk_nag": [
            "py.typed"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "aws-cdk-lib>=2.176.0, <3.0.0",
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
