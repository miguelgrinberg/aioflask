import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aioflask",
    version="0.0.1",
    author="Miguel Grinberg",
    author_email="miguel.grinberg@gmail.com",
    description="Flask running on asyncio.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/miguelgrinberg/aioflask",
    packages=setuptools.find_packages(),
    install_requires=[
        'greenletio',
        'flask',
        'uvicorn',
    ],
    entry_points={
        'flask.commands': [
            'run=aioflask.cli:run'
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
