from setuptools import setup, find_packages
import re

def get_version():
    with open("foundry/version.py", "r") as f:
        content = f.read()
    match = re.search(r'__version__\s*=\s*["\'](.+?)["\']', content)
    return match.group(1)


with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="luxforge-foundry",
    version= get_version(),
    author="LuxForge",
    author_email="lab@luxforge.dev",
    description="Audit-grade logging and modular tooling for Foundry systems",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/LuxForge/LuxForge-Foundry",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
    python_requires=">=3.8",
    install_requires=[
        "keyboard"  # if used in menu
    ],
)