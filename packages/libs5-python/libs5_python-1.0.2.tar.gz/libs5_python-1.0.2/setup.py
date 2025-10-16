from setuptools import setup

setup(
    name='libs5-python',
    version='1.0.0',
    author='Arkadiusz Hypki',
    description='libs5-python is a package with Python scripts, and helper classes.',
    packages=['src/net'],
    include_package_data=True,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[
    ],
)
