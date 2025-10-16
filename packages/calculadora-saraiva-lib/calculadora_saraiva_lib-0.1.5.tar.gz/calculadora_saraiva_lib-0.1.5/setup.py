from setuptools import setup, find_packages # type: ignore

# Lendo o README.md para o PyPI
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="calculadora_saraiva_lib",  # ⚡ Nome com hífen para o PyPI
    version="0.1.5",
    description="Biblioteca de operações matemáticas básicas em Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Gustavo Saraiva Mariano",
    author_email="gsaraivam10@gmail.com",
    url="https://github.com/saraivagustavo/calculadora-fastapi-lib-aula",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)