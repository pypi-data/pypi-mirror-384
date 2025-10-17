from setuptools import setup

setup(
    name='hidroconta',
    version='1.7.0',
    packages=['hidroconta'],
    install_requires=[
        'pandas>=1.3.5',
        'requests>=2.26.0',
        'datetime>=5.5'
    ],
    python_requires='>=3.9',
    author='JavierL',
    author_email='javier.lopez@hidroconta.com',
    description='Facilitate access to Demeter REST interface endpoints, provided by Hidroconta S.A.U.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)