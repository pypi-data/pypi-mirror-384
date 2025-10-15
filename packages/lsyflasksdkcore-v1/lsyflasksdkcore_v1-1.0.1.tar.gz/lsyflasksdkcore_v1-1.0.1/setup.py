from setuptools import setup, find_packages
import os

# Get the long description from the README file
here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
install_requires = []
requirements_path = os.path.join(here, "requirements.txt")
if os.path.exists(requirements_path):
    with open(requirements_path, "r", encoding="utf-8") as fh:
        install_requires = [line.strip() for line in fh.readlines() if line.strip() and not line.startswith("#")]

# Read license
license_text = ""
license_path = os.path.join(here, "LICENSE")
if os.path.exists(license_path):
    with open(license_path, "r", encoding="utf-8") as fh:
        license_text = fh.read()

setup(
    name="lsyflasksdkcore_v1",
    version="1.0.1",
    author="fhp",
    author_email="chinafengheping@outlook.com",
    description="领数云flask SDK核心库（https://github.com/9kl/lsyflasksdkcore_v1）",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/9kl/lsyflasksdkcore_v1",
    packages=find_packages(),
    license=license_text,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=install_requires,
)
