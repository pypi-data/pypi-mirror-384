"""
Setup configuration for openai-without-pydantic package
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read version from __init__.py
def get_version():
    with open(os.path.join(this_directory, 'openai_wrapper', '__init__.py'), encoding='utf-8') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return '0.1.0'

setup(
    name='openai-without-pydantic',
    version=get_version(),
    author='DeveloperAlex',
    author_email='',  # Add your email here
    description='A simple Python wrapper for OpenAI API without Pydantic dependencies',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/DeveloperAlex/pypi_OpenAI_Without_Pydantic',
    project_urls={
        'Bug Reports': 'https://github.com/DeveloperAlex/pypi_OpenAI_Without_Pydantic/issues',
        'Source': 'https://github.com/DeveloperAlex/pypi_OpenAI_Without_Pydantic',
    },
    packages=find_packages(exclude=['tests', '*.tests', '*.tests.*', 'tests.*']),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
    keywords='openai api wrapper pydantic-free no-pydantic ai llm gpt',
    python_requires='>=3.7',
    install_requires=[
        'requests>=2.25.0',
    ],
    extras_require={
        'dev': [
            'python-dotenv>=0.19.0',
            'pytest>=7.0.0',
            'pytest-cov>=3.0.0',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
