from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='codebank',
    version='0.2.4',
    description='summa oru pip module',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='PraneshPk ',
    author_email='praneshvaradharaj@gmail.com',
    url='https://github.com/PraneshPK2005/codebank',
    packages=find_packages(),
    install_requires=[
        'numpy'    
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)