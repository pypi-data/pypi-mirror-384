"""
Setup script for Vyre Python SDK
"""

from setuptools import setup, find_packages # pyright: ignore[reportMissingModuleSource]
import os

# Read version from __init__.py
def get_version():
    init_path = os.path.join(os.path.dirname(__file__), 'vyre', '__init__.py')
    with open(init_path, 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"\'')
    return '1.0.0'

# Read README
def get_long_description():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r') as f:
            return f.read()
    return ''

setup(
    name='vyre-sdk',
    version=get_version(),
    description='Python SDK for Vyre AI Chat API',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    author='Vyre Team',
    author_email='support@vyre.com',
    url='https://github.com/vyre/vyre-python-sdk',
    packages=find_packages(),
    install_requires=[
        'requests>=2.25.0',
        'aiohttp>=3.7.0',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.7',
    keywords='vyre ai chat sdk api',
    project_urls={
        'Documentation': 'https://docs.vyre.com',
        'Source': 'https://github.com/vyre/vyre-python-sdk',
        'Tracker': 'https://github.com/vyre/vyre-python-sdk/issues',
    },
)
