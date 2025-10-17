from setuptools import setup, find_packages
from Cython.Build import cythonize
setup(
    name='common_stats-thaichim',
    version='0.0.3',
    description='A simple library for basic statistical calculations',
    long_description=open('USAGE.md').read(),
    long_description_content_type='text/markdown',
    author='Nawawan Thaichim',
    author_email='woonzy09@email.com',
    packages=find_packages(),
    install_requires=[
        "pytest"
    ],
    license='MIT',
    python_requires='>=3.7',
    ext_modules=cythonize("common_stats/statistics.pyx", compiler_directives={'language_level' : "3"}), 
    
)