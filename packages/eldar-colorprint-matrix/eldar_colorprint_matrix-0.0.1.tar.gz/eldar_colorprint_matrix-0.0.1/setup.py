from setuptools import setup, find_packages

setup(
    name='eldar-colorprint-matrix',
    version='0.0.1',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[],
    author='Eldar',
    author_email='eldar@example.com',
    description='A simple Python library for colorful terminal text output',
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/eldar/colorprint',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
