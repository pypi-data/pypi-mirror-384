from langchain_core.structured_query import StructuredQuery, Visitor
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.chains.query_constructor.base import StructuredQueryOutputParser
from typing import  Any, Tuple, Dict
import json

def _get_structured_query_output_parser(
    attribute_info,
    allowed_comparators=None,
    allowed_operators=None,
    fix_invalid=False,
):
    
    allowed_attributes = []
    for ainfo in attribute_info:
        allowed_attributes.append(
            ainfo.name if (
                isinstance(ainfo, AttributeInfo)
            ) else ainfo["name"]
        )

    return StructuredQueryOutputParser.from_components(
        allowed_comparators=allowed_comparators,
        allowed_operators=allowed_operators,
        allowed_attributes=allowed_attributes,
        fix_invalid=fix_invalid,
    )

def _prepare_search_kwargs(
    structured_query: StructuredQuery, translator: Visitor
) -> Tuple[str, Dict[str, Any]]:
    new_query, search_kwargs = translator.visit_structured_query(
        structured_query
    )
    if structured_query.limit is not None:
        search_kwargs["k"] = structured_query.limit
    return new_query, search_kwargs

def translate_to_structured_query(
    query: str,
    filter_as_str: str,
    limit: int,
    translator: Visitor,
    attribute_info: list,
    allowed_comparators=list,
    allowed_operators=list,
    fix_invalid=False
) -> Tuple[StructuredQuery, Dict[str, Any]]:
    """

    Translate a query string and filter into a structured query and search kwargs.

    Args:
        query (str): The query string to translate.
        filter_as_str (str): The filter string to apply.
        translator (Visitor): The visitor used for translation.
        attribute_info (list): Information about the attributes in the query.
        allowed_comparators (list): List of allowed comparators for the query.
        allowed_operators (list): List of allowed operators for the query.
        fix_invalid (bool): Whether to fix invalid queries.

    Returns:
        Tuple[StructuredQuery, Dict[str, Any]]: A tuple containing the structured query and search kwargs.
    """

    # Create an instance of the translator class
    parser = _get_structured_query_output_parser(
        attribute_info=attribute_info,
        allowed_comparators=allowed_comparators,
        allowed_operators=allowed_operators,
        fix_invalid=fix_invalid
    )

    # Parse the query and filter into a structured query
    structured_query = parser.parse(
        json.dumps(
            {
                "query": query,
                "filter": filter_as_str,
                "limit": limit
            }
        )
    )

    # Prepare the search kwargs
    new_query, search_kwargs = _prepare_search_kwargs(structured_query, translator)

    return new_query, search_kwargs
