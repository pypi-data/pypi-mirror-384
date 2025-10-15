from setuptools import find_packages, setup

setup(
    name="cyberintegrations",
    version="0.13.1",
    description="Python library - modules for processing data from the TI and DRP system collected in one library. "
    "This library simplifies work with the products API and gives you the flexibility to customize the "
    "search and retrieval of data from the system.",
    python_requires=">=3.7",
    install_requires=["requests>=2.31.0", "urllib3>=2.0.2"],
    packages=find_packages(
        include=["cyberintegrations", "cyberintegrations.*"]
    ),
    author="Cyberintegrations",
    author_email="cyberintegrationsdev@gmail.com",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
