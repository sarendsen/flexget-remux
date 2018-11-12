from setuptools import setup, find_packages

setup(
    name='flexget-remux',
    version='1.0',
    description='',
    packages=find_packages(exclude=['tests']),
    install_requires=['FlexGet>2.2'],
    tests_require=['pytest'],
    entry_points="""
        [FlexGet.plugins]
        remux = remux.remux"""
)
