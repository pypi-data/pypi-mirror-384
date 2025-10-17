import os

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))

# Find version
__version__ = None
exec(open(f"{here}/zvolv_sdk/version.py").read())

long_description = ""
with open(os.path.join(here, "README.md"), encoding="utf-8") as readme:
    long_description = readme.read()


setup(
    name='zvolv-sdk-corp',
    version=__version__,
    packages=find_packages(),
    license='MIT',
    description='The Zvolv API Platform SDK for Python',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Akshay Jadhav',
    author_email='support@zvolv.com',
    python_requires=">=3.6.0",
    url='https://github.com/zvolvapi/python-zvolv-sdk',
    download_url='https://github.com/zvolvapi/python-zvolv-sdk/archive/v_01.tar.gz',    # I explain this later on
    keywords=['zvolv', 'zvolv-api', 'web-api', 'sdk', 'rest-api-client'],
    install_requires=[
        'requests>=2.23.0',
        'pydantic>=2.7.3',
        'elasticsearch_dsl>=8.13.1',
        'redis'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        "Operating System :: OS Independent",
        'License :: OSI Approved :: MIT License',  
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
