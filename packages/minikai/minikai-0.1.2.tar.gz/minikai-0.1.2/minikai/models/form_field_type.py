from typing import Literal, cast

FormFieldType = Literal["checkbox", "dateTime", "radio", "text"]

FORM_FIELD_TYPE_VALUES: set[FormFieldType] = {
    "checkbox",
    "dateTime",
    "radio",
    "text",
}


def check_form_field_type(value: str) -> FormFieldType:
    if value in FORM_FIELD_TYPE_VALUES:
        return cast(FormFieldType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {FORM_FIELD_TYPE_VALUES!r}")
