[![Unit Tests](https://github.com/smartassistant-unicamp/eagle/actions/workflows/test.yml/badge.svg)](https://github.com/smartassistant-unicamp/eagle/actions/workflows/test.yml)
<p align="center">
    <img src="./assets/EAGLE.jpg" alt="EAGLE Logo" />
</p>

# Enhanced Agents for Generative Language Excellence

## Do que se trata este projeto?

Esse projeto implementa a visão do [framework CoALA (Cognitive Architectures for Language Agents)](https://github.com/ysymyth/awesome-language-agents) no contexto do [LangGraph](https://www.langchain.com/langgraph), com agentes, ferramentas e estratégias de integração multiagentes para servirem de exemplo para novas implementações.

## Instalação

### Pré-requisitos (considerando o uso do Conda para gerenciar o ambiente python)

- [Miniforge 3](https://conda-forge.org/download/): O Miniforge é uma distribuição mínima do conda, que é um gerenciador de pacotes e ambientes virtuais. Ele será usado para criar um ambiente virtual para instalar as dependências do projeto.

### Criando o ambiente virtual

1. Uma vez instalado o Conda, abra o terminal e digite o seguinte comando:

```bash
conda create -n eagle python=3.10
```

2. Após a criação do ambiente, ative-o com o comando:

```bash
conda activate eagle
```

3. Instale a versão mais recente do Poetry com o comando:

```bash
pip install poetry==1.8.5
```

1. Instale as dependências do projeto com o comando:

```bash
poetry install
```

## Testes
Para executar os testes, execute os seguintes passos:

1. Ative o ambiente virtual com o comando:

```bash
conda activate eagle
```

2. Copie o arquivo `sample.test.env` para `.test.env` e preencha as variáveis de ambiente com as informações necessárias para o seu amnbiente de testes.

```bash
cp sample.test.env .test.env
```

### Ponto de Atenção

Os testes e exemplos dos notebooks estão baseados nos modelos `AzureChatOpenAI` para os LLMs e `AzureOpenAIEmbeddings` para os embeddings. Caso seja necessário utilizar outros nomes de modelos, tipos ou ajustar as relações com as variáveis de ambiente, essas alterações podem ser feitas na pasta [`tests/models`](tests/models).

## Exemplos de uso das funcionalidades

A pasta `notebooks` contém exemplos de uso das ferramentas. Para executar os exemplos:

1. Ative o ambiente virtual com o comando:

```bash
conda activate eagle
```

2. Ative a extensão de widgets do jupyter com o comando:

```bash
jupyter nbextension enable --py widgetsnbextension
```

3. Ative o jupyter lab com o comando:

```bash
jupyter lab
```

4. Abra o browser e execute os notebooks da pasta `notebooks`.
