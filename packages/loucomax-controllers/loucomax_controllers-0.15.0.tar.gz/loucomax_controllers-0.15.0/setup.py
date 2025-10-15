from setuptools import setup, find_packages

setup(
    name="loucomax_controllers",
    version="0.15.0",
    description="Controllers for all devices used in the LouCOMAX (CNRS) project",
    author="BLASIAK Antoine",
    author_email="antoineblasiak66@gmail.com",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "overrides",
        "pythonnet",
        "h5py",
        "matplotlib",
        "configparser",
        "pyusb",
        "pyserial",
        "PyQt5",
        "csu2controller",
        "zaber_motion",
    ],
    python_requires=">=3.8",
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
)