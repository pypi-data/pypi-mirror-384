from typing import Union

import unidecode


def normalise_name(name: Union[list, tuple, str]) -> str:
    normalised_name = str(name)
    normalised_name = unidecode.unidecode(normalised_name)
    normalised_name = "".join(c for c in normalised_name if c.isalnum() or c.isspace())
    normalised_name = normalised_name.replace(" ", "_").lower()
    return normalised_name
