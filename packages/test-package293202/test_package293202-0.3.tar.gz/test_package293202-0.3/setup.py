from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name="test_package293202",
    version="0.3",
    packages=find_packages(),
    install_requires=[
        # Add your package dependencies here
    ],
    entry_points={
        'console_scripts': [
            'test_command = test_package:hello',
        ]
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
)