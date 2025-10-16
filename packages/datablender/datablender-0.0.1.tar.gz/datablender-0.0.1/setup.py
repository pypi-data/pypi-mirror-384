from sys import platform
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='datablender',
    version='0.0.1',
    description='Tools for data.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/MontrealMobilite/datablender.git',
    author='Julien Douville',
    packages=find_packages(),
    zip_safe=False,
    test_suite="tests",
    install_requires =[
        'unidecode',
        'aiohttp',
        'asyncpg',
        'sqlalchemy',
        'psycopg2' if platform == "win32" else 'psycopg2-binary',
        'datetime',
        'numpy',
        'pandas',
        'dbf',
        'openpyxl',
        'pyexcel',
        'xlrd',
        'beautifulsoup4',
        'selenium',
        'webdriver_manager',
        'postgis',
        'python-socketio',
        'dbfread',
        'scipy',
        'scikit-learn',
        'pyproj',
        'fiona',
        'geopandas',
        'dill',
        'pysmb'
    ],
    extras_require={
        'dev': [
            'pytest',
            'build',
            'twine'
        ]
    }
)