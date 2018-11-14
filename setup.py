from setuptools import setup, find_packages

setup(
    name='flexget-remux',
    version='1.0',
    description='',
    packages=find_packages(exclude=['tests']),
    entry_points="""
        [FlexGet.plugins]
        remux = remux.remux"""
)
