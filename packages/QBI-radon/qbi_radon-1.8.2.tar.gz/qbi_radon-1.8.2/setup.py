from setuptools import setup


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="QBI_radon",
    version="1.8.2",
    description="Radon Transformation for Pytorch 2",
    author="Minh Nhat Trinh",
    license_files=["LICENSE"],
    packages=["QBI_radon"],
    install_requires=[
        "torch >= 2.0",

    ],
    classifiers=[
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
)
