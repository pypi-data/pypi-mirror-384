from setuptools import setup, find_packages

setup(
    name='statilib',
    version='0.1.0',
    description='A simple statistics library',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Abdulrahman F. Alosaimi',
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=[],
)