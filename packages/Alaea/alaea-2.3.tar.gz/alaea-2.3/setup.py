"""
https://pypi.org/project/Alaea/#history
"""
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Alaea",
    version="2.3",
    author="Christmas",
    author_email="273519355@qq.com",
    description="Some simple tools by Christmas",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'numpy',
        'netCDF4',
        'xarray',
        'colorlog',
        'requests'
    ],
)

