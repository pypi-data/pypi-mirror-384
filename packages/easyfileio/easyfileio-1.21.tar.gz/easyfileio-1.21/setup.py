from setuptools import setup, find_packages

setup(
    name='easyfileio',
    version='1.21',
    packages=find_packages(),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url='https://github.com/plzgivemeajob/easyfileio',
    description="an easy way to read and write files in python",
    license='MIT',
    author_email='zeemako@gmail.com'
)