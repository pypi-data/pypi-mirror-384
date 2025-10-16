import re
from pydantic import BaseModel
from langchain_core.messages import AIMessage
from langchain_core.language_models.chat_models import BaseChatModel

def sanitize_json_string(json_string):
    """
    Sanitizes a JSON string by removing comments, invalid control characters,
    and empty lines that are not inside string literals. Ensures "\n" inside
    strings is replaced with "\\n", and removes "\n" outside strings.
    """
    sanitized_string = ""
    in_string = False
    escape_next = False

    for i, char in enumerate(json_string):
        if escape_next:
            escape_next = False
            sanitized_string += char
            continue

        if char == '\\':
            escape_next = True
            sanitized_string += char
            continue

        if char == '"':
            in_string = not in_string
            sanitized_string += char
            continue

        # Replace "\n" with "\\n" if inside a string
        if char == '\n':
            if in_string:
                sanitized_string += '\\n'
            # Skip "\n" if outside a string
            continue

        # Remove `#` and everything after it if not inside a string
        if char == '#' and not in_string:
            # Skip to the end of the line
            while i < len(json_string) and json_string[i] != '\n':
                i += 1
            continue

        # Remove invalid control characters if not inside a string
        if not in_string and ord(char) < 32 and char not in ('\t', '\n', '\r'):
            continue

        sanitized_string += char

    # Remove empty lines that may have been created
    sanitized_string = re.sub(r'\n\s*\n', '\n', sanitized_string)
    
    # Troca todas as keys do tipo 'key': por "key":
    sanitized_string = re.sub(r"'([^']+)'\s*:", r'"\1":', sanitized_string)

    return sanitized_string.strip()

def extract_json_string(msg, type="dict"):
    """
    Extracts a JSON string from a text message by balancing brackets/braces,
    taking into account that brackets/braces within strings should be ignored.
    
    Args:
        msg (str): The message containing a JSON string.
        type (str): The type of JSON structure to extract ('dict' or 'list').
        
    Returns:
        str: The extracted JSON string or None if no JSON is found.
    """
    if type == "dict":
        open_char, close_char = '{', '}'
    elif type == "list":
        open_char, close_char = '[', ']'
    else:
        return None
    
    # Find the first opening character
    start_index = msg.find(open_char)
    if start_index == -1:
        return None
    
    # Balance the opening and closing characters
    balance = 0
    in_string = False
    escape_next = False
    
    for i in range(start_index, len(msg)):
        char = msg[i]
        
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            continue
        
        if char == '"' and not escape_next:
            in_string = not in_string
        
        if not in_string:  # Only count brackets/braces when not in a string
            if char == open_char:
                balance += 1
            elif char == close_char:
                balance -= 1
                
                if balance == 0:
                    # Found the matching closing character
                    json_string = msg[start_index:i+1]
                    return sanitize_json_string(json_string)
    
    return None  # No balanced JSON found

def apply_conversion(data, field_mapping):
    """
    Recursively applies field and value mappings to a JSON object or list of JSON objects.

    Args:
        data (dict | list): The JSON object or list of JSON objects to convert.
        field_mapping (dict): The mapping of fields and their associated value mappings.

    Returns:
        dict | list: The converted JSON object or list of JSON objects.
    """
    if isinstance(data, list):
        # If the data is a list, apply the conversion to each element
        return [apply_conversion(item, field_mapping) for item in data]
    elif isinstance(data, dict):
        # If the data is a dictionary, apply the field and value mappings
        converted = {}
        for source_key, value in data.items():
            if source_key in field_mapping:
                target_key = field_mapping[source_key]["target_key"]
                value_mapping = field_mapping[source_key].get("value_mapping", {})
                if isinstance(value, (dict, list)):
                    # Recursively apply conversion to nested structures
                    converted[target_key] = apply_conversion(value, value_mapping)
                else:
                    # Apply value mapping if it exists
                    converted[target_key] = value_mapping.get(value, value)
            else:
                # Recursively apply conversion to nested structures even if no mapping exists
                converted[source_key] = apply_conversion(value, field_mapping) if isinstance(value, (dict, list)) else value
        return converted
    else:
        # If the data is neither a list nor a dictionary, return it as is
        return data

def convert_schema(message: AIMessage, conversion_schema: dict, source_lang: str, target_schema: BaseModel, llm: BaseChatModel, use_structured_output: bool = False) -> BaseModel:
    """
    Converts a JSON string from one schema to another based on the conversion schema.

    Args:
        text (str): The input text containing the JSON string.
        conversion_schema (dict): The conversion schema mapping fields and values between languages.
        source_lang (str): The source language key in the conversion schema.
        target_schema (BaseModel): The target schema class for validation.

    Returns:
        BaseModel: An instance of the target schema with converted data.
    """
    try:
        if use_structured_output:
            llm_with_structured_output = llm.with_structured_output(conversion_schema[source_lang]["class_for_parsing"])
            parsed_data = llm_with_structured_output.invoke([message])
        else:
            text = message.content
            # Extract JSON string from the input text
            json_str = extract_json_string(text)
            if not json_str:
                raise ValueError("No valid JSON string found in the input text.")

            # Parse the JSON using the source language schema
            source_schema_class = conversion_schema[source_lang]["class_for_parsing"]
            parsed_data = source_schema_class.model_validate_json(json_str)

        # Apply recursive conversion
        field_mapping = conversion_schema[source_lang]["convertion_schema"]
        converted_data = apply_conversion(parsed_data.dict(), field_mapping)

        # Validate and return the target schema instance
        return target_schema(**converted_data)

    except Exception as e:
        raise Exception(f"Failed to convert schema: {e}") from e
