from setuptools import setup, find_packages
from Monisha import appname, version, install, DATA01, DATA02

with open("README.md", "r") as o:
    description = o.read()
    
setup(
    name=appname,
    license='MIT',
    version=version,
    description='ㅤ',
    author='Monisha',
    classifiers=DATA02,
    author_email=DATA01,
    python_requires='~=3.10',
    packages=find_packages(),
    install_requires=install,
    long_description=description,
    keywords=['apps', 'python', 'extensions'],
    long_description_content_type="text/markdown")
