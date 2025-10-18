from setuptools import setup, find_packages

setup(
    name="test_package293202",
    version="0.2",
    packages=find_packages(),
    install_requires=[
        # Add your package dependencies here
    ],
    entry_points={
        'console_scripts': [
            'test_command = test_package:hello',
        ]
    }
)