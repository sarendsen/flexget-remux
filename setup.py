from setuptools import setup, find_packages

setup(
    name='flexget-remux',
    version='1.0',
    description='',
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'whichcraft'
    ],
    entry_points="""
        [FlexGet.plugins]
        remux = remux.remux"""
)
