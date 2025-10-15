import os
from setuptools import setup, find_packages

# Read version from package
def get_version():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, 'puter', '__init__.py'), encoding='utf-8') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    raise RuntimeError('Unable to find version string.')

# Read README
def get_long_description():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        return f.read()

setup(
    name='puter-python-sdk',
    version=get_version(),
    packages=find_packages(),
    package_data={
        'puter': ['*.json'],
    },
    include_package_data=True,
    install_requires=[
        'requests>=2.25.0',
    ],
    author='Slymi',
    author_email='justin@slymi.org',  
    description='Python SDK for accessing free AI models through Puter.js',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/CuzImSlymi/puter-python-sdk',
    project_urls={
        'Bug Reports': 'https://github.com/CuzImSlymi/puter-python-sdk/issues',
        'Source': 'https://github.com/CuzImSlymi/puter-python-sdk',
        'Documentation': 'https://github.com/CuzImSlymi/puter-python-sdk#readme',
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    keywords='ai puter sdk chatbot api artificial-intelligence',
    python_requires='>=3.7',
)

