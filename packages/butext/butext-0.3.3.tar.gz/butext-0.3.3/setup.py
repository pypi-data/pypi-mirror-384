from setuptools import setup, find_packages
setup(
    name='butext',
    version='0.3.3',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'wordcloud'
    ]
)