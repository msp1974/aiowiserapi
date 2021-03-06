import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aio-wiser-api",
    version="0.1.0",
    python_requires=">=3.7",
    author="Angelo Santagata",
    author_email="angelosantagata@gmail.com",
    description="An async API for accessing data on the Drayton Wiser Heating system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/msp1974/aiowiserapi",
    packages=setuptools.find_packages(),
    install_requires=[
	"aiofiles>=0.4.0", 
	"aiohttp>=3.6.2"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
