from setuptools import setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="teste-nuget-python",
    version="1.0.1",
    license="MIT License",
    author="Ricardo Braga",
    author_email="rickalbbraga@gmail.com",
    description="Um pacote de teste para aprender a criar pacotes com o Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="hello world", # Palavras-chave separadas por espaço.
    packages=["hello_world"], # Substitua pelo nome do seu pacote.
    # install_requires=[], # Caso tenha dependências, descomente e adicione as dependências aqui.
)