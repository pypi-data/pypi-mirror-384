"""
Setup para criar a biblioteca compartilhada
Instalar com: pip install -e /path/to/shared-auth-lib
"""
from setuptools import setup, find_packages

setup(
    name='shared-auth-lib',
    version='1.0.0',
    description='Biblioteca compartilhada para acesso aos dados de autenticação',
    packages=find_packages(),
    install_requires=[
        'Django>=4.2',
    ],
    python_requires='>=3.8',
)