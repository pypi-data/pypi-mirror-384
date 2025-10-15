from setuptools import setup, find_packages

setup(
    name='sythonlab_airport_docs',
    version='0.1.1',
    packages=find_packages(),
    install_requires=[],
    url='https://github.com/sythonlab/SythonLab-Airport-Docs',
    author='José Angel Alvarez Abraira',
    author_email='sythonlab@gmail.com',
    description='Generation of documentation and mandatory reports required by airports and customs for travel, including Passenger Name Lists (PNL) for airline check-in systems..',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
