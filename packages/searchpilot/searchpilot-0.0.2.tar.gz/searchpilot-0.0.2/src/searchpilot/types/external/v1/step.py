# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from ...._models import BaseModel

__all__ = ["Step"]


class Step(BaseModel):
    id: int

    account_slug: str

    adaptation: Literal[
        "carbon.adjusters.body.adjusters.add_before_css_selector",
        "carbon.adjusters.body.adjusters.prepend_to_css_selector",
        "carbon.adjusters.body.adjusters.append_to_css_selector",
        "carbon.adjusters.body.adjusters.add_after_css_selector",
        "carbon.adjusters.body.adjusters.add_class",
        "carbon.adjusters.body.adjusters.set_attribute_value",
        "carbon.adjusters.body.adjusters.update_element_type",
        "carbon.adjusters.body.adjusters.replace_inner_css_selector",
        "carbon.adjusters.body.adjusters.replace_inner_css_selector_with_text",
        "carbon.adjusters.body.adjusters.find_replace_within",
        "carbon.adjusters.body.adjusters.remove_css_selector",
        "carbon.adjusters.body.adjusters.remove_class",
        "carbon.adjusters.body.adjusters.remove_attribute",
        "carbon.adjusters.body.adjusters.set_json_element",
        "carbon.adjusters.body.adjusters.update_json_element",
        "carbon.adjusters.body.adjusters.delete_json_element",
        "carbon.adjusters.body.adjusters.insert_element_existing_json_array",
        "carbon.adjusters.headers.adjusters.header_append",
        "carbon.adjusters.headers.adjusters.set_header",
        "carbon.adjusters.headers.adjusters.update_header",
        "carbon.adjusters.headers.adjusters.remove_header",
        "carbon.adjusters.headers.adjusters.remove_header_value_by_regex",
        "carbon.adjusters.headers.adjusters.change_status_code",
        "carbon.adjusters.headers.adjusters.path_redirect",
    ]
    """
    - `carbon.adjusters.body.adjusters.add_before_css_selector` - Insert block of
      HTML - before the element
    - `carbon.adjusters.body.adjusters.prepend_to_css_selector` - Insert block of
      HTML - after the opening tag
    - `carbon.adjusters.body.adjusters.append_to_css_selector` - Insert block of
      HTML - before the closing tag
    - `carbon.adjusters.body.adjusters.add_after_css_selector` - Insert block of
      HTML - after the element
    - `carbon.adjusters.body.adjusters.add_class` - Add additional class to an
      element
    - `carbon.adjusters.body.adjusters.set_attribute_value` - Set or update an
      attribute of an element
    - `carbon.adjusters.body.adjusters.update_element_type` - Update HTML tag type
      (e.g. from h1 to h2)
    - `carbon.adjusters.body.adjusters.replace_inner_css_selector` - Replace
      contents of an element with HTML
    - `carbon.adjusters.body.adjusters.replace_inner_css_selector_with_text` -
      Replace contents of an element with text
    - `carbon.adjusters.body.adjusters.find_replace_within` - Find & replace over an
      element
    - `carbon.adjusters.body.adjusters.remove_css_selector` - Remove an element
    - `carbon.adjusters.body.adjusters.remove_class` - Remove a class from an
      element
    - `carbon.adjusters.body.adjusters.remove_attribute` - Remove an attribute of an
      element
    - `carbon.adjusters.body.adjusters.set_json_element` - Set the value of a JSON
      element
    - `carbon.adjusters.body.adjusters.update_json_element` - Update the value of a
      JSON element
    - `carbon.adjusters.body.adjusters.delete_json_element` - Delete an element from
      a JSON block
    - `carbon.adjusters.body.adjusters.insert_element_existing_json_array` - Insert
      element into existing JSON array
    - `carbon.adjusters.headers.adjusters.header_append` - Append an additional
      value to a header
    - `carbon.adjusters.headers.adjusters.set_header` - Set the value of an HTTP
      Header
    - `carbon.adjusters.headers.adjusters.update_header` - Overwrite the value of an
      existing header
    - `carbon.adjusters.headers.adjusters.remove_header` - Remove a Header
    - `carbon.adjusters.headers.adjusters.remove_header_value_by_regex` - Find and
      replace on Header contents
    - `carbon.adjusters.headers.adjusters.change_status_code` - Change the status
      code of the response
    - `carbon.adjusters.headers.adjusters.path_redirect` - Redirect to a new URL
    """

    customer_slug: str

    enabled: bool

    name: str
    """Descriptive name to help identify the Step"""

    parameters: object

    rule_id: int

    section_slug: str
