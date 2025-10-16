from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

requirements = [
    'matplotlib', 'numpy', 'xarray', 'rasterio', 'pyproj', 
    'shapely', 'cartopy', 'contextily', 'scipy', 'seaborn'
]

setup(
    name="sensingpy",
    version="1.0.0",
    author="Sergio Heredia",
    author_email="sergiohercar1@gmail.com",
    description="A package for geospatial image processing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aouei/geopy",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
)