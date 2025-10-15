from setuptools import setup, find_packages

setup(
    name='splunk_hec_logger',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'requests',
    ],
    author='Rostislav Anisimov',
    author_email='rostislav.anisimov@gmail.com',
    description='A simple Splunk HEC logger.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
