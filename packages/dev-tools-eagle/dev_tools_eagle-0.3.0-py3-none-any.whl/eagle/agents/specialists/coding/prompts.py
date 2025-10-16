from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from pydantic import BaseModel, Field
from eagle.agents.react_agent.prompts import (
    YOU_ARE_IN_A_CONVERSATION_STR_EN,
    YOU_ARE_IN_A_CONVERSATION_STR_PT_BR,
    PLAN_STR_EN,
    PLAN_STR_PT_BR,
    OBSERVATION_STR_EN,
    OBSERVATION_STR_PT_BR,
    TOOLS_INTERACTIONS_STR_EN,
    TOOLS_INTERACTIONS_STR_PT_BR,
    OBJECTS_SUMMARY_STR_EN,
    OBJECTS_SUMMARY_STR_PT_BR,
    MUST_CITE_OBJECTS_SUMMARY_STR_EN,
    MUST_CITE_OBJECTS_SUMMARY_STR_PT_BR,
    SYSTEM_PROMPT_TUPLE_EN,
    SYSTEM_PROMPT_TUPLE_PT_BR,
    IMPORTANT_GUIDELINES_STR_EN,
    IMPORTANT_GUIDELINES_STR_PT_BR
)
from eagle.utils.output import convert_schema
from eagle.utils.prompt_utils import PromptGenerator, EagleJsonOutputParser
from typing import ClassVar, List

# Schemas for EN
class ObserveNodeFinalUserPromptOutputSchemaEN(BaseModel):
    action: str = Field(description="Action to be taken by the agent. Can be 'nothing' or 'think'.")
    message: str = Field(description="Message to be returned by the agent. Can be an explanation or internal reasoning.")
    object_ids: list = Field(default=[], description="List of object IDs relevant to the code generation.")

class PlanNodeFinalUserPromptOutputSchemaEN(BaseModel):
    action: str = Field(description="Action to be taken by the agent. Can be 'execute' or 'nothing'.")
    message: str = Field(description="Message to be returned by the agent. Can describe the plan.")
    input_object_ids: list = Field(default=[], description="List of object IDs to be used as inputs for the code.")
    id_existing_code: str = Field(default="", description="ID of any existing code that can be reused. Leave 'null' if a new code needs to be generated.")

class GeneratedObjectDescriptionSchemaEN(BaseModel):
    name: str = Field(description="Name of the object in the context of the demand.")
    description: str = Field(description="Detailed description of the object in the current context, domain, and demand.")

class ExecuteNodeFinalUserPromptOutputSchemaEN(BaseModel):
    code: str = Field(default="", description="Generated Python code.")
    kwargs: dict = Field(default_factory=dict, description="Parameters and values required for executing the function.")
    generic_description: str = Field(default="", description="Generic description of what the code does.")
    generated_objects_description: List[GeneratedObjectDescriptionSchemaEN] = Field(
        description="List of descriptions of the generated objects, each with a name and detailed description."
    )
    message: str = Field(description="Message about what was planned and done, the objects used, the generated objects, etc.")
    new_code_needed: str = Field(default="", description="Observation in case it is necessary to generate additional code to meet the demand. Leave empty if not needed.")

# Schemas for PT_BR
class ObserveNodeFinalUserPromptOutputSchemaPT_BR(BaseModel):
    acao: str = Field(description="Ação a ser tomada pelo agente. Pode ser 'nada' ou 'pensar'.")
    mensagem: str = Field(description="Mensagem a ser retornada pelo agente. Pode ser uma explicação ou raciocínio interno.")
    object_ids: list = Field(default=[], description="Lista de IDs de objetos relevantes para a geração de código.")

class PlanNodeFinalUserPromptOutputSchemaPT_BR(BaseModel):
    acao: str = Field(description="Ação a ser tomada pelo agente. Pode ser 'executar' ou 'nada'.")
    mensagem: str = Field(description="Mensagem a ser retornada pelo agente. Pode descrever o plano.")
    input_object_ids: list = Field(default=[], description="Lista de IDs de objetos a serem usados como inputs para o código.")
    id_codigo_ja_existente: str = Field(default="", description="ID de algum código já existente que pode ser reutilizado. Deixe 'null' se um novo código precisar ser gerado.")

class GeneratedObjectDescriptionSchemaPT_BR(BaseModel):
    nome: str = Field(description="Nome do objeto no contexto da demanda.")
    descricao: str = Field(description="Descrição detalhada do objeto no contexto atual, domínio e demanda.")

class ExecuteNodeFinalUserPromptOutputSchemaPT_BR(BaseModel):
    codigo: str = Field(default="", description="Código Python gerado.")
    kwargs: dict = Field(default_factory=dict, description="Parâmetros e valores necessários para executar a função.")
    descricao_generica: str = Field(default="", description="Descrição genérica do que o código faz.")
    descricao_objetos_gerados: List[GeneratedObjectDescriptionSchemaPT_BR] = Field(
        description="Lista de descrições dos objetos gerados, cada um com um nome e uma descrição detalhada."
    )
    mensagem: str = Field(description="Mensagem sobre o que foi planejado e feito, os objetos usados, os objetos gerados, etc.")
    novo_codigo_necessario: str = Field(default="", description="Observação em caso de ser necessário gerar um código adicional para atender à demanda. Deixe vazio se não for necessário.")

# Output Parsers for PT_BR
class ObserveNodeFinalUserPromptOutputParser(EagleJsonOutputParser):
    CONVERTION_SCHEMA: ClassVar[dict] = {
        "pt-br": {
            "class_for_parsing": ObserveNodeFinalUserPromptOutputSchemaPT_BR,
            "convertion_schema": {
                "acao": {"target_key": "action", "value_mapping": {"nada": "nothing", "pensar": "think"}},
                "mensagem": {"target_key": "message", "value_mapping": {}},
                "object_ids": {"target_key": "object_ids", "value_mapping": {}},
            },
        },
        "en": {
            "class_for_parsing": ObserveNodeFinalUserPromptOutputSchemaEN,
            "convertion_schema": {
                "action": {"target_key": "action", "value_mapping": {}},
                "message": {"target_key": "message", "value_mapping": {}},
                "object_ids": {"target_key": "object_ids", "value_mapping": {}},
            },
        },
    }

    TARGET_SCHEMA: BaseModel = ObserveNodeFinalUserPromptOutputSchemaEN

class PlanNodeFinalUserPromptOutputParser(EagleJsonOutputParser):
    CONVERTION_SCHEMA: ClassVar[dict] = {
        "pt-br": {
            "class_for_parsing": PlanNodeFinalUserPromptOutputSchemaPT_BR,
            "convertion_schema": {
                "acao": {"target_key": "action", "value_mapping": {"executar": "execute", "nada": "nothing"}},
                "mensagem": {"target_key": "message", "value_mapping": {}},
                "input_object_ids": {"target_key": "input_object_ids", "value_mapping": {}},
                "id_codigo_ja_existente": {"target_key": "id_existing_code", "value_mapping": {}},
            },
        },
        "en": {
            "class_for_parsing": PlanNodeFinalUserPromptOutputSchemaEN,
            "convertion_schema": {
                "action": {"target_key": "action", "value_mapping": {}},
                "message": {"target_key": "message", "value_mapping": {}},
                "input_object_ids": {"target_key": "input_object_ids", "value_mapping": {}},
                "id_existing_code": {"target_key": "id_existing_code", "value_mapping": {}},
            },
        },
    }

    TARGET_SCHEMA: BaseModel = PlanNodeFinalUserPromptOutputSchemaEN

class ExecuteNodeFinalUserPromptOutputParser(EagleJsonOutputParser):
    CONVERTION_SCHEMA: ClassVar[dict] = {
        "pt-br": {
            "class_for_parsing": ExecuteNodeFinalUserPromptOutputSchemaPT_BR,
            "convertion_schema": {
                "codigo": {"target_key": "code", "value_mapping": {}},
                "kwargs": {"target_key": "kwargs", "value_mapping": {}},
                "descricao_generica": {"target_key": "generic_description", "value_mapping": {}},
                "descricao_objetos_gerados": {
                    "target_key": "generated_objects_description",
                    "value_mapping": {
                        "nome": {"target_key": "name", "value_mapping": {}},
                        "descricao": {"target_key": "description", "value_mapping": {}},
                    },
                },
                "novo_codigo_necessario": {"target_key": "new_code_needed", "value_mapping": {}},
            },
        },
        "en": {
            "class_for_parsing": ExecuteNodeFinalUserPromptOutputSchemaEN,
            "convertion_schema": {
                "code": {"target_key": "code", "value_mapping": {}},
                "kwargs": {"target_key": "kwargs", "value_mapping": {}},
                "generic_description": {"target_key": "generic_description", "value_mapping": {}},
                "generated_objects_description": {
                    "target_key": "generated_objects_description",
                    "value_mapping": {
                        "name": {"target_key": "name", "value_mapping": {}},
                        "description": {"target_key": "description", "value_mapping": {}},
                    },
                },
                "new_code_needed": {"target_key": "new_code_needed", "value_mapping": {}},
            },
        },
    }

    TARGET_SCHEMA: BaseModel = ExecuteNodeFinalUserPromptOutputSchemaEN

# General prompt strings

## EN
ERROR_EXPLANATION_STR_EN = """
{%- if previous_error_explanation -%}
A previous attempt to develop code for this demand failed an excessive number of times. See the previous version of the code and the explanation of the error:
------------------- Error Explanation ------------------
{{ previous_error_explanation }}
--------------------------------------------------------
{%- endif %}
"""

OBJECTS_SUMMARY_EXACT_ORDER_STR_EN = """
A below, a summary of the objects that should be used, IN THIS EXACT ORDER, as inputs for the code you need to generate:
------------------ Object Summary ----------------------
{{objects_summary}}
--------------------------------------------------------
"""

## PT_BR
ERROR_EXPLANATION_STR_PT_BR = """
{%- if previous_error_explanation -%}
Uma tentativa anterior de desenvolver um código para essa demanda falhou um número excessivo de vezes. Veja a versão anterior do código e a explicação do erro:
------------------ Explicação do Erro ------------------
{{ previous_error_explanation }}
--------------------------------------------------------
{%- endif %}
"""

OBJECTS_SUMMARY_EXACT_ORDER_STR_PT_BR = """
Abaixo, um sumário dos objetos que deverão entrar, NESTA EXATA ORDEM, como inputs do código que você precisa gerar:
------------------ Sumário de Objetos ------------------
{{objects_summary}}
--------------------------------------------------------
"""

# Prompts for EN
OBSERVE_NODE_PROMPT_STR_EN = """
You must determine if, given the context and the objects available or not in memory, you can generate code to meet the needs.
""" + \
    OBJECTS_SUMMARY_STR_EN + \
    OBSERVATION_STR_EN + \
    PLAN_STR_EN + \
    TOOLS_INTERACTIONS_STR_EN + \
    IMPORTANT_GUIDELINES_STR_EN + \
"""
Now, respond with one of the following outputs:

1. If you think it is not the case to generate code to process objects and create new objects, return a JSON with the following structure:
{
    "action": "nothing",
    "message": <Explanation of why not to generate code and what>
}

2. If you think it is the case to generate code to process objects and create new objects, but you need to think more about it in the next step, return a JSON with the following structure:
{
    "action": "think",
    "message": <Write here your ideas, internal reasoning, questions, and reflections about the type of code you need to generate. Always address yourself in these thoughts, never directing a question to the user. Something like "To solve this problem, I need to generate code that does... and produces...">,
    "object_ids": [<list of IDs of objects you think are relevant for the code you need to generate, whether they are objects to be used as inputs or previously generated codes used before>]
}
"""

PLAN_NODE_PROMPT_STR_EN = """
You must think of a plan to generate code that meets the user's needs.
""" + \
    OBSERVATION_STR_EN + \
    OBJECTS_SUMMARY_STR_EN + \
    PLAN_STR_EN + \
    ERROR_EXPLANATION_STR_EN + \
    TOOLS_INTERACTIONS_STR_EN + \
    IMPORTANT_GUIDELINES_STR_EN + \
"""
Now, return with one of the following outputs:
1. If you have thought of a plan, return a JSON with the following structure:
{
    "action": "execute",
    "message": <Write here the plan for the code, describing in detail and in an orderly manner what it should do. Do not write the code itself, only the description of what the code should do. Refer to the IDs of the objects you will use and what the code should do with each of them.>,
    "input_object_ids": [<list of IDs ONLY of the objects to be used, in this exact order, as inputs for the code you need to generate. Objects are always the first inputs of the function to be generated, followed by other arguments.>]
    "id_existing_code": <ID of any existing code, if any, that can be reused exactly as it is, changing only the parameters and the objects to be provided as input. Place an empty string if a new code needs to be generated.>
}

2. If you have not really managed to think of a plan, return a JSON with the following structure:
{
    "action": "nothing",
    "message": <Write here your ideas, internal reasoning, questions, and reflections on what you could do to help resolve this conversation. Always address yourself in these thoughts, never directing a question to the user.>
}
"""

EXECUTE_NODE_PROMPT_STR_EN = """
Observing the conversation and the plan you have already made, generate code that runs on the chosen objects and performs the task you planned.
""" + \
    OBSERVATION_STR_EN + \
    PLAN_STR_EN + \
    OBJECTS_SUMMARY_EXACT_ORDER_STR_EN + \
    MUST_CITE_OBJECTS_SUMMARY_STR_EN + \
    ERROR_EXPLANATION_STR_EN + \
    TOOLS_INTERACTIONS_STR_EN + \
    IMPORTANT_GUIDELINES_STR_EN + \
"""
The CODE must have the following format:
```python
def <FUNCTION_NAME>(args_objects (a list - type 'list' - assuming that the objects inside args_objects will ALWAYS be in the EXACT ORDER PRESENTED ABOVE in the summary),... and then the other arguments besides 'args_object'):
    # From here, you must write the code that processes the objects and returns the result.
    
    # FUNDAMENTAL guidelines:
    # 1. Choose what to put in place of <FUNCTION_NAME> to represent well what the function does.
    # 2. Imports go at the beginning of the code, but INSIDE the function, NEVER outside it!
    # 3. You may use ONLY the following libraries: {{allowed_libraries}}
    # 4. NEVER use 'print(...)' anywhere in the code, nor log anything.
    # 5. The function's return will NECESSARILY be a dictionary with the structure described below:

    return obj1, obj2, obj3, ... # where the returned objects are the results of the code, returned SEPARATED by commas.
```

IMPORTANT: The code, function name, parameter names - EXCEPT 'args_object', which is fixed (!!) - must be GENERIC, that is, in no way related to the specific domain of the objects processed now, but rather to any object of the same type, leaving for the VALUES used in the other input arguments the responsibility of referring to the specific object.
For example, if the object is a DataFrame with sales data and the demand is something like 'calculate total sales', the function name should be something like 'totalize_column' instead of 'totalize_sales', and the parameter receiving the column to be totalized should be something like 'totalization_column' instead of 'sales_column'.
Similarly, if the object to be generated is a figure, always expose important arguments for generating the figure, such as 'title', 'labels', 'colors', etc.
In summary, the function must be ABSOLUTELY agnostic regarding the content of the manipulable object and adaptable, through the parameters, to any other object of the same type, thinking about future uses of the same function in other objects from other domains.

Your RESPONSE, therefore, must follow the following JSON format:
```json
{
    "code": "def ... complete function code, following the template and guidelines indicated above.",
    "kwargs": { dictionary with the parameters and values required for the function to be executed to meet the demand, except 'args_object', which is fixed (!!).}
    "generic_description": <generic description of what the code does, without referring to the specific contents of the objects.>,
    "generated_objects_description": [
        {
            "name": <name of the FIRST object of the returned objects, in the context of the demand>,
            "description": <DETAILED description of the object in the current context, in the current domain, aiming to record in what context each of them was generated, what demand they meet, where they came from, etc.>
        },
        {
            "name": <name of the SECOND object of the returned objects, in the context of the demand>,
            "description": <DETAILED description of the object in the current context, in the current domain, aiming to record in what context each of them was generated, what demand they meet, where they came from, etc.>
        }, ... and so on for all objects returned, IN THE EXACT ORDER THEY ARE RETURNED!!
    ],
    "message": <message about what you planned and did, the objects you used, the objects generated, etc.>,
    "new_code_needed": <Observation in case it is necessary to generate additional code to meet the demand. Be clear about what was already done and what is still needed to be done. Place an empty string if it is not necessary and everything that was needed to do was done.>
}
```
"""

EXECUTE_NODE_WITH_EXISTING_CODE_PROMPT_STR_EN = """
To solve the demand, you have already chosen an existing code that can be reused. The chosen code is as follows:
```python
{{ existing_code }}
```
""" + \
    OBSERVATION_STR_EN + \
    PLAN_STR_EN + \
    OBJECTS_SUMMARY_EXACT_ORDER_STR_EN + \
    MUST_CITE_OBJECTS_SUMMARY_STR_EN + \
    ERROR_EXPLANATION_STR_EN + \
    TOOLS_INTERACTIONS_STR_EN + \
    IMPORTANT_GUIDELINES_STR_EN + \
"""
Your RESPONSE, therefore, must follow the following JSON format:
```json
{
    "kwargs": { dictionary with the parameters and values required for the function to be executed to meet the demand, except 'args_object', which is fixed (!!).},
    "generated_objects_description": [
        {
            "name": <name of the FIRST object of the returned objects, in the context of the demand>,
            "description": <DETAILED description of the object in the current context, in the current domain, aiming to record in what context each of them was generated, what demand they meet, where they came from, etc.>
        },
        {
            "name": <name of the SECOND object of the returned objects, in the context of the demand>,
            "description": <DETAILED description of the object in the current context, in the current domain, aiming to record in what context each of them was generated, what demand they meet, where they came from, etc.>
        }, ... and so on for all objects returned, IN THE EXACT ORDER THEY ARE RETURNED!!
    ],
    "message": <message about what you planned and did, the objects you used, the objects generated, etc.>,
    "new_code_needed": <Observation in case it is necessary to generate additional code to meet the demand. Be clear about what was already done and what is still needed to be done. Place an empty string if it is not necessary and everything that was needed to do was done.>
}
```
"""

# Prompts for PT_BR
OBSERVE_NODE_PROMPT_STR_PT_BR = """
Você deve determinar se, dado o contexto e os objetos disponíveis ou não em memória, você pode gerar um código que atenda às necessidades.
""" + \
    OBJECTS_SUMMARY_STR_PT_BR + \
    OBSERVATION_STR_PT_BR + \
    PLAN_STR_PT_BR + \
    TOOLS_INTERACTIONS_STR_PT_BR + \
    IMPORTANT_GUIDELINES_STR_PT_BR + \
"""
Agora, responda com uma das seguintes saídas:

1. Se você acha que não é o caso de gerar um código para processar objetos e criar novos objetos, retorne um JSON com a seguinte estrutura:
{
    "acao": "nada",
    "mensagem": <Explicação do porquê de não gerar código e quais>
}

2. Se você acha que é o caso de gerar um código para processar objetos e criar novos objetos, mas precisa pensar mais sobre isso no próximo passo, retorne um JSON com a seguinte estrutura:
{
    "acao": "pensar",
    "mensagem": <Escreva aqui suas ideias, raciocínios internos, perguntas e reflexões sobre o tipo de código que você precisa gerar. Sempre dirija-se a si mesmo nesses pensamentos, nunca endereçando uma pergunta ao usuário. Algo como "Para resolver esse problema, preciso gerar um código que faça... e produza...">,
    "object_ids": [<lista de IDs dos objetos que você acha relevantes para o código que precisa gerar, sejam eles objetos a serem usados como inputs ou códigos gerados anteriormente>]
}
"""

PLAN_NODE_PROMPT_STR_PT_BR = """
Você deve pensar em um plano para gerar um código que atenda às necessidades do usuário.
""" + \
    OBSERVATION_STR_PT_BR + \
    OBJECTS_SUMMARY_STR_PT_BR + \
    PLAN_STR_PT_BR + \
    ERROR_EXPLANATION_STR_PT_BR + \
    TOOLS_INTERACTIONS_STR_PT_BR + \
    IMPORTANT_GUIDELINES_STR_PT_BR + \
"""
Agora, retorne com uma das seguintes saídas:
1. Caso tenha pensado em um plano, retorne um JSON com a seguinte estrutura:
{
    "acao": "executar",
    "mensagem": <Escreva aqui o plano do código, descrevendo em detalhes e de forma ordenada o que ele deve fazer. Não escreva o código em si, apenas a descrição do que o código deve fazer. Faça referência aos IDs dos objetos que você usará e o que o código deve fazer com cada um deles.>,
    "input_object_ids": [<lista de IDs APENAS dos objetos a serem usados, nesta exata ordem, como inputs do código que você precisa gerar. Os objetos são sempre os primeiros inputs da função a ser gerada, seguidos pelos outros argumentos.>]
    "id_codigo_ja_existente": <ID de algum código já existente, se houver, que pode ser reutilizado exatamente como está, mudando apenas os parâmetros e os objetos a serem fornecidos como input. Coloque uma string vazia se um novo código precisar ser gerado.>
}

2. Caso não tenha realmente conseguido pensar em um plano, retorne um JSON com a seguinte estrutura:
{
    "acao": "nada",
    "mensagem": <Escreva aqui suas ideias, raciocínios internos, perguntas e reflexões sobre o que você poderia fazer para ajudar a resolver essa conversa. Sempre dirija-se a si mesmo nesses pensamentos, nunca endereçando uma pergunta ao usuário.>
}
"""

EXECUTE_NODE_PROMPT_STR_PT_BR = """
Observando a conversa e o plano que você já fez, gere um código que rode sobre os objetos escolhidos e realize a tarefa que você planejou.
""" + \
    OBSERVATION_STR_PT_BR + \
"""
Abaixo, um sumário dos objetos que deverão entrar, NESTA EXATA ORDEM, como inputs do código que você precisa gerar:
------------------ Sumário de Objetos ------------------
{{objects_summary}}
--------------------------------------------------------
""" + \
    OBSERVATION_STR_PT_BR + \
    PLAN_STR_PT_BR + \
    OBJECTS_SUMMARY_EXACT_ORDER_STR_PT_BR + \
    MUST_CITE_OBJECTS_SUMMARY_STR_PT_BR + \
    ERROR_EXPLANATION_STR_PT_BR + \
    TOOLS_INTERACTIONS_STR_PT_BR + \
    IMPORTANT_GUIDELINES_STR_PT_BR + \
"""
O CÓDIGO deve ter o seguinte formato:
```python
def <NOME_DA_FUNÇÃO>(args_objects (uma lista - tipo 'list' mesmo - partindo do princípio de que os objetos dentro de args_objects estarão SEMPRE na EXATA ORDEM APRESENTADA ACIMA no sumário),... e depois os demais argumentos além da 'args_object'):
    # A partir daqui, você deve escrever o código que processa os objetos e retorna o resultado.
    
    # Diretrizes FUNDAMENTAIS:
    # 1. Escolha o que colocar no lugar de <NOME_DA_FUNÇÃO> para representar bem o que a função faz.
    # 2. Os 'import ...' vão no início do código, mas DENTRO da função, e JAMAIS fora dela!
    # 3. Você poderá usar EXCLUSIVAMENTE as seguintes bibliotecas: {{allowed_libraries}}
    # 4. JAMAIS use 'print(...)' em qualquer lugar do código, nem faça log de nada.
    # 5. O retorno da função será NECESSARIAMENTE um dicionário com a estrutura descrita abaixo:

    return obj1, obj2, obj3, ... # onde os objetos retornados são os resultados do código, retornados SEPARADOS por vírgulas.
```

IMPORTANTE: O código, o nome da função, os nomes dos parâmetros - MENOS 'args_object', que é fixo (!!) -, devem ser GENÉRICOS, ou seja, de forma alguma relacionados ao domínio específico dos objetos processados agora, mas sim a qualquer objeto do mesmo tipo, deixando para os VALORES usados nos outros argumentos de entrada a responsabilidade de se referirem ao objeto específico.
Por exemplo, se o objeto é um DataFrame com dados de vendas e a demanda for algo como 'calcular o total de vendas', o nome da função deverá ser algo como 'totalizar_coluna' em vez de 'totalizar_vendas', e o parâmetro que recebe a coluna a ser totalizada deverá ser algo como 'coluna_totalização' em vez de 'coluna_de_vendas'.
De forma semelhante, se o objeto a ser gerado é uma figura, exponha sempre argumentos importantes para a geração da figura, como 'título', 'rótulos', 'cores', etc.
Em resumo, a função deve ser ABSOLUTAMENTE agnóstica em relação ao conteúdo do objeto manipulável e adaptável, pelos parâmetros, a qualquer outro objeto do mesmo tipo, pensando em usos futuros da mesma função em outros objetos de outros domínios.

Sua RESPOSTA, portanto, deve seguir o seguinte formato JSON:
```json
{
    "codigo": "def ... código completo da função, conforme o template e as diretrizes indicados anteriormente.",
    "kwargs": { dicionário com os parâmetros e valores necessários para que a função seja executada para atender à demanda, exceto 'args_object'.},
    "descricao_generica": <descrição genérica do que o código faz, sem se referir aos conteúdos específicos dos objetos.>,
    "descricao_objetos_gerados": [
        {
            "nome": <nome do PRIMEIRO objeto dos objetos retornados, no contexto da demanda>,
            "descricao": <DESCRIÇÃO DETALHADA do objeto no contexto atual, no domínio atual, visando registrar em que contexto cada um deles foi gerado, qual demanda atendem, de onde vieram, etc.>
        },
        {
            "nome": <nome do SEGUNDO objeto dos objetos retornados, no contexto da demanda>,
            "descricao": <DESCRIÇÃO DETALHADA do objeto no contexto atual, no domínio atual, visando registrar em que contexto cada um deles foi gerado, qual demanda atendem, de onde vieram, etc.>
        }, ... e assim por diante para todos os objetos retornados, NA EXATA ORDEM EM QUE SÃO RETORNADOS!!
    ],
    "mensagem": <mensagem sobre o que você planejou e fez, os objetos que você usou, os objetos gerados, etc.>,
    "novo_codigo_necessario": <Observação em caso de ser necessário fazer gerar um código adicional para atender a demanda. Seja claro quanto àquilo do plano que já foi feito e o que ainda falta fazer. Coloque uma string vazia se não for necessário e tudo o que era necessário fazer foi feito.>
}
```
"""

EXECUTE_NODE_WITH_EXISTING_CODE_PROMPT_STR_PT_BR = """
Para resolver a demanda, você já escolheu um código existente que pode ser reutilizado. O código escolhido é o seguinte:
```python
{{ existing_code }}
```
""" + \
    OBSERVATION_STR_PT_BR + \
    PLAN_STR_PT_BR + \
    OBJECTS_SUMMARY_EXACT_ORDER_STR_PT_BR + \
    MUST_CITE_OBJECTS_SUMMARY_STR_PT_BR + \
    ERROR_EXPLANATION_STR_PT_BR + \
    TOOLS_INTERACTIONS_STR_PT_BR + \
    IMPORTANT_GUIDELINES_STR_PT_BR + \
"""
Sua RESPOSTA, portanto, deve seguir o seguinte formato JSON:
```json
{
    "kwargs": { dicionário com os parâmetros e valores necessários para que a função seja executada para atender à demanda, exceto 'args_object', que é fixo (!!).},
    "descricao_objetos_gerados": [
        {
            "nome": <nome do PRIMEIRO objeto dos objetos processados pela função, no contexto da demanda>,
            "descricao": <DESCRIÇÃO DETALHADA do objeto no contexto atual, no domínio atual, visando registrar em que contexto cada um deles foi gerado, qual demanda atendem, de onde vieram, etc.>
        },
        {
            "nome": <nome do SEGUNDO objeto dos objetos processados pela função, no contexto da demanda>,
            "descricao": <DESCRIÇÃO DETALHADA do objeto no contexto atual, no domínio atual, visando registrar em que contexto cada um deles foi gerado, qual demanda atendem, de onde vieram, etc.>
        }, ... e assim por diante para todos os objetos processados pela função, NA EXATA ORDEM EM QUE SÃO RETORNADOS!!
    ],
    "mensagem": <mensagem sobre o que você planejou e fez, os objetos que você usou, os objetos gerados etc.>,
    "novo_codigo_necessario": <Observação em caso de ser necessário fazer gerar um código adicional para atender a demanda. Seja claro quanto àquilo do plano que já foi feito e o que ainda falta fazer. Coloque uma string vazia se não for necessário e tudo o que era necessário fazer foi feito.>
}
```
"""

# Prompts for EN
OBSERVE_NODE_PROMPT_EN = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_EN,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_STR_EN + OBSERVE_NODE_PROMPT_STR_EN,
            template_format="jinja2",
        ),
    ]
)

PLAN_NODE_PROMPT_EN = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_EN,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_STR_EN + PLAN_NODE_PROMPT_STR_EN,
            template_format="jinja2",
        ),
    ]
)

EXECUTE_NODE_PROMPT_EN = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_EN,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_STR_EN + EXECUTE_NODE_PROMPT_STR_EN,
            template_format="jinja2",
        ),
    ]
)

EXECUTE_NODE_WITH_EXISTING_CODE_PROMPT_EN = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_EN,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_STR_EN + EXECUTE_NODE_WITH_EXISTING_CODE_PROMPT_STR_EN,
            template_format="jinja2",
        ),
    ]   
)

# Prompts for PT_BR
OBSERVE_NODE_PROMPT_PT_BR = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_PT_BR,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_STR_PT_BR + OBSERVE_NODE_PROMPT_STR_PT_BR,
            template_format="jinja2",
        ),
    ]
)

PLAN_NODE_PROMPT_PT_BR = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_PT_BR,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_STR_PT_BR + PLAN_NODE_PROMPT_STR_PT_BR,
            template_format="jinja2",
        ),
    ]
)

EXECUTE_NODE_PROMPT_PT_BR = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_PT_BR,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_STR_PT_BR + EXECUTE_NODE_PROMPT_STR_PT_BR,
            template_format="jinja2",
        ),
    ]
)

EXECUTE_NODE_WITH_EXISTING_CODE_PROMPT_PT_BR = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_PT_BR,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_STR_PT_BR + EXECUTE_NODE_WITH_EXISTING_CODE_PROMPT_STR_PT_BR,
            template_format="jinja2",
        ),
    ]
)

_PROMPTS_DICT = {
    "observe": {
        "output_parser": ObserveNodeFinalUserPromptOutputParser,
        "languages": {
            "pt-br": OBSERVE_NODE_PROMPT_PT_BR,
            "en": OBSERVE_NODE_PROMPT_EN,
        },
    },
    "plan": {
        "output_parser": PlanNodeFinalUserPromptOutputParser,
        "languages": {
            "pt-br": PLAN_NODE_PROMPT_PT_BR,
            "en": PLAN_NODE_PROMPT_EN,
        },
    },
    "execute": {
        "output_parser": ExecuteNodeFinalUserPromptOutputParser,
        "languages": {
            "pt-br": EXECUTE_NODE_PROMPT_PT_BR,
            "en": EXECUTE_NODE_PROMPT_EN,
        },
    },
    "execute_with_existing_code": {
        "output_parser": ExecuteNodeFinalUserPromptOutputParser,
        "languages": {
            "pt-br": EXECUTE_NODE_WITH_EXISTING_CODE_PROMPT_PT_BR,
            "en": EXECUTE_NODE_WITH_EXISTING_CODE_PROMPT_EN,
        },
    },
}

# Initialize the PromptGenerator with the prompts dictionary
prompts_generator = PromptGenerator(prompts_dict=_PROMPTS_DICT)
