"""
Setup configuration for label-studio-sso package
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="label-studio-sso",
    version="6.0.7",
    author="AIdoop Team",
    author_email="admin@aidoop.com",
    description="Native JWT authentication for Label Studio OSS - simple and secure SSO integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aidoop/label-studio-sso",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Django>=3.2",
        "PyJWT>=2.0.0",
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-django>=4.5",
            "black>=22.0",
            "flake8>=4.0",
        ],
    },
    keywords="label-studio label-studio-oss sso jwt authentication single-sign-on open-source oss",
    project_urls={
        "Bug Reports": "https://github.com/aidoop/label-studio-sso/issues",
        "Source": "https://github.com/aidoop/label-studio-sso",
        "Documentation": "https://github.com/aidoop/label-studio-sso/blob/main/README.md",
    },
)
