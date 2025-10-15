from typing import List, Dict

from bluer_objects import markdown

from bluer_sbc.parts.db import db_of_parts


def design(
    items: List[str],
    dict_of_parts: Dict = {},
    macros: Dict = {},
) -> Dict:
    output = {
        "items": items,
    }

    if dict_of_parts:
        output["macros"] = {
            "parts_images:::": markdown.generate_table(
                db_of_parts.as_images(
                    dict_of_parts,
                    reference="./parts",
                ),
                cols=10,
                log=False,
            ),
            "parts_list:::": db_of_parts.as_list(
                dict_of_parts,
                reference="./parts",
                log=False,
            ),
        }

        output["macros"].update(macros)

    return output
