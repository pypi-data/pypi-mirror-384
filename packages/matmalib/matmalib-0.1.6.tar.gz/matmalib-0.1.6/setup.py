from setuptools import setup, find_packages

setup(
    name='matmalib',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'matplotlib',
        'colormap',
        'networkx' ,
        'py3dmol'
    ],
)

