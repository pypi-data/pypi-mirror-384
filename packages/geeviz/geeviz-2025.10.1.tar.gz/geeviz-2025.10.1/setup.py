import setuptools
import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
###################################################################
# Name Package
packages = ["geeViz"]

# Provide what folders beyond the root of the package should be included in the package
package_data = {
    "geeViz": [
        "examples/data/**",
        "examples/data/**/**",
        "examples/*.py",
        "examples/*.ipynb",
        "phEEnoViz/*.py",
        "phEEnoViz/examples/*.py",
        "phEEnoViz/examples/*.ipynb",
        "geeView/**",
        "geeView/**/**",
        "geeView/**/**/**",
        "geeView/**/**/**/**",
        "geeView/**/**/**/**/**",
    ],
}
###################################################################
with open("geeViz/README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


# GetVersion function taken from: https://github.com/google/earthengine-api/blob/master/python/setup.py
# def GetVersion(package):
#     print(package)
#     with open(package + "/__init__.py") as f:
#         return re.findall(r"__version__\s*=\s*\'([.\d]+)\'", f.read())[0]


def GetVersion(package):
    print(package)
    with open(package + "/__init__.py", encoding="utf-8") as f:
        return f.read().split("__version__ = ")[-1][1:-2]
        # return re.findall(r"__version__\s*=\s*\'([.\d]+)\'", f.read())[0]


setuptools.setup(
    name="geeviz",
    version=GetVersion(packages[0]),
    author="Ian Housman",
    author_email="ian.housman@gmail.com",
    description="A package to help with GEE data processing, analysis, and visualization",
    long_description=long_description,
    license="Apache",
    keywords="google earth engine earthengine gee remote sensing landsat sentinel sentinel-2 modis forestry forest land cover use change detection nlcd",
    long_description_content_type="text/markdown",
    project_urls={
        "Repository": "https://github.com/gee-community/geeviz",
        "Documentation": "https://geeviz.org/",
    },
    # packages=setuptools.find_packages(),
    packages=packages,
    package_data=package_data,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
    ],
    install_requires=[
        "earthengine-api",
        "oauth2client",
        "google-cloud-storage",
        "pandas",
        "geemap",
        "matplotlib",
        "IPython",
        "requests",
        "folium",
        "simpledbf",
    ],
    # data_files = [('gee-py-viz',data_files)],
)
