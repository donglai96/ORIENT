"""
@author Donglai Ma
@email donglaima96@gmail.com
@create date 2022-05-17 18:04:44
@modify date 2022-05-17 18:04:44
@desc setup file for OREINT, this used on m1 mac, so tensorflow is intalled previously
"""
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open

setup(
    name='ORIENT',
    version='1.0',
    description='Real time Electron flux data and tool for visulizing',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/donglai96/ORIENT',
    packages=find_packages(),
    author='Donglai Ma',
    author_email='dma96@atmos.ucla.edu',
    license='MIT',
    classifiers=['Development Status :: 4 - Beta',
                 'Intended Audience :: Science/Research',
                 'Topic :: Scientific/Engineering',
                 'License :: OSI Approved :: MIT License',
                 'Programming Language :: Python :: 3.8',
                 ],
    keywords='predict radiation-belt',

    install_requires=['pandas','matplotlib','scipy','mechanize','astropy','pyspedas','tensorflow','shap'],
    python_requires='>=3.8',
    include_package_data=True,
)

