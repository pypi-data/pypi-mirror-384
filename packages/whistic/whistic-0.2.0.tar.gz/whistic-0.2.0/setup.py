from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="whistic",
    version="0.2.0",
    author="Phil Massyn",
    author_email="phil.massyn@icloud.com",
    description="Python SDK to interface with the Whistic API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/massyn/whistic",
    project_urls={
        "Bug Tracker": "https://github.com/massyn/whistic/issues",
        "Documentation": "https://github.com/massyn/whistic#readme",
        "Source Code": "https://github.com/massyn/whistic",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Security",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    keywords="whistic api sdk vendor management third-party risk",
    include_package_data=True,
    zip_safe=False,
)