from setuptools import setup, find_packages

setup(
    name='gilgamesh_summarizer',
    version='0.1.6',
    packages=find_packages(),
    install_requires=[
        'rdflib',
        'unsloth',
        'transformers',
        'torch',
        'networkx',
        'tqdm',
        'pandas',
        'pyjedai',
        'pyparsing'
    ],
    python_requires='>=3.10',
    author='Kostas Plas',
    author_email='kplas@di.uoa.gr',
    description='A package for summarizing RDF graphs for Question Answering pipelines',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)
