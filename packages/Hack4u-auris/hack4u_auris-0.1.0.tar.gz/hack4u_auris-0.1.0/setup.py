from setuptools import setup, find_packages

# Leer el contenido del archivo README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Hack4u_auris",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
    author="Aurisssss",
    description="Biblioteca para consultar cursos de Hack4u.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://hack4u.io",
)
