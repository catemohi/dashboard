from setuptools import find_packages, setup
from os.path import dirname, join


setup(
    name='naumen_api',
    version='1.2',
    author="catemohi",
    author_email="catemohi@gmail.com",
    description="API CRM системы, основанное на парсинге DOM-дерева.",
    long_description=open(join(dirname(__file__), 'README.md'),
                          encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/catemohi/naumen-api",
    lecense='GNU General Public License v3.0',
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4==4.11.1',
        'requests==2.28.1',
    ],
    include_package_data=True,
)
