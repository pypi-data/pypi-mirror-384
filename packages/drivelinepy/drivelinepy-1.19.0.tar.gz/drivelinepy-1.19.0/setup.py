from setuptools import setup, find_packages
import os

# print working directory
print("Current working directory: ", os.getcwd())
print("Contents of current working directory: ", os.listdir())

# Read the contents of your README file
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='drivelinepy',
    version='1.19.0',
    author='Garrett York',
    author_email='garrett@drivelinebaseball.com',
    description='A Python package for Driveline Baseball API interactions',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/drivelineresearch/drivelinepy',
    packages=find_packages(),
    install_requires=[
        'python-dotenv>=1.0.1,<2.0.0',
        'requests>=2.31.0,<3.0.0',
        'urllib3>=2.2.0,<3.0.0'
    ],
    classifiers=[
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)