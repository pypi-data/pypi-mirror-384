from bs4 import Tag


def extract_form_inputs(form_element: Tag) -> dict[str, str]:
    result = {}

    for element in form_element.find_all("input"):
        if _is_form_input_valid(element):
            result[element.attrs["id"]] = element.attrs["value"]

    return result


def _is_form_input_valid(element: Tag) -> bool:
    return "id" in element.attrs and "value" in element.attrs
