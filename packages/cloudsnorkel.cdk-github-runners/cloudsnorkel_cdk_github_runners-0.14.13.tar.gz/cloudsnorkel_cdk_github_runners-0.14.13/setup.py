import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "cloudsnorkel.cdk-github-runners",
    "version": "0.14.13",
    "description": "CDK construct to create GitHub Actions self-hosted runners. Creates ephemeral runners on demand. Easy to deploy and highly customizable.",
    "license": "Apache-2.0",
    "url": "https://github.com/CloudSnorkel/cdk-github-runners.git",
    "long_description_content_type": "text/markdown",
    "author": "Amir Szekely<amir@cloudsnorkel.com>",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/CloudSnorkel/cdk-github-runners.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "cloudsnorkel.cdk_github_runners",
        "cloudsnorkel.cdk_github_runners._jsii"
    ],
    "package_data": {
        "cloudsnorkel.cdk_github_runners._jsii": [
            "cdk-github-runners@0.14.13.jsii.tgz"
        ],
        "cloudsnorkel.cdk_github_runners": [
            "py.typed"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "aws-cdk-lib>=2.155.0, <3.0.0",
        "constructs>=10.0.5, <11.0.0",
        "jsii>=1.115.0, <2.0.0",
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
        "Development Status :: 4 - Beta",
        "License :: OSI Approved"
    ],
    "scripts": []
}
"""
)

with open("README.md", encoding="utf8") as fp:
    kwargs["long_description"] = fp.read()


setuptools.setup(**kwargs)
