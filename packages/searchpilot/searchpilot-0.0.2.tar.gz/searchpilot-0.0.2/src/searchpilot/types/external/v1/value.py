# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from ...._models import BaseModel

__all__ = ["Value", "Conversion"]


class Conversion(BaseModel):
    step: Literal[
        "carbon.converters.converters.to_lower",
        "carbon.converters.converters.to_upper",
        "carbon.converters.converters.to_title_case",
        "carbon.converters.converters.strip",
        "carbon.converters.converters.extract_regex",
        "carbon.converters.converters.regex_replace",
        "carbon.converters.converters.split_to_array",
        "carbon.converters.converters.slice",
        "carbon.converters.converters.extract_from_json",
        "carbon.converters.converters.first_element",
        "carbon.converters.converters.last_element",
        "carbon.converters.converters.largest",
        "carbon.converters.converters.smallest",
    ]
    """
    - `carbon.converters.converters.to_lower` - Convert to lower case
    - `carbon.converters.converters.to_upper` - Convert to upper case
    - `carbon.converters.converters.to_title_case` - Convert to title case
    - `carbon.converters.converters.strip` - Strip whitespace
    - `carbon.converters.converters.extract_regex` - Find Value using regex
    - `carbon.converters.converters.regex_replace` - Replace value using regex
    - `carbon.converters.converters.split_to_array` - Split the Value into an array
      of values
    - `carbon.converters.converters.slice` - Slice (only keep part) of the Value
    - `carbon.converters.converters.extract_from_json` - Extract from block of JSON
    - `carbon.converters.converters.first_element` - First element in the array
    - `carbon.converters.converters.last_element` - Last element in the array
    - `carbon.converters.converters.largest` - The largest element in the array
    - `carbon.converters.converters.smallest` - The smallest element in the array
    """

    step_parameters: object


class Value(BaseModel):
    id: int

    account_slug: str

    conversions: List[Conversion]

    customer_slug: str

    name: str
    """Can only contain lowercase alphanumerics and underscores."""

    section_slug: str

    source: Literal[
        "carbon.extractors.extractors.css_selector_attribute",
        "carbon.extractors.extractors.match_response_header_key",
        "carbon.extractors.extractors.match_request_header_key",
        "carbon.extractors.extractors.match_hostname",
        "carbon.extractors.extractors.match_url",
        "carbon.extractors.extractors.count",
        "carbon.extractors.extractors.from_dataset",
        "carbon.extractors.extractors.constant",
        "carbon.extractors.extractors.generate_random",
        "request_constant",
        "request_uri",
        "request_hostname",
        "request_get_parameter",
        "request_get_header",
        "from_dataset",
    ]
    """
    - `carbon.extractors.extractors.css_selector_attribute` - Extract the value from
      the HTML of the page being requested
    - `carbon.extractors.extractors.match_response_header_key` - Extract the value
      from the HTTP response Headers of the page being requested
    - `carbon.extractors.extractors.match_request_header_key` - Extract the value
      from the HTTP request Headers of the page being requested
    - `carbon.extractors.extractors.match_hostname` - Extract the hostname from the
      URL of the page being requested
    - `carbon.extractors.extractors.match_url` - Extract the value from the URL of
      the page being requested
    - `carbon.extractors.extractors.count` - Extract a count of elements from the
      HTML
    - `carbon.extractors.extractors.from_dataset` - Extract a value from a dataset
    - `carbon.extractors.extractors.constant` - I'll enter the value manually
    - `carbon.extractors.extractors.generate_random` - Generate a random number
      based on the canonical url of the page
    - `request_constant` - Constant
    - `request_uri` - Extract from request path
    - `request_hostname` - Extract from request hostname
    - `request_get_parameter` - Extract from a request parameter
    - `request_get_header` - Extract from a request header
    - `from_dataset` - Extract a value from a dataset
    """

    source_parameters: object

    description: Optional[str] = None
    """Descriptive name that identifies the Value"""

    is_in_preview_spec: Optional[bool] = None
