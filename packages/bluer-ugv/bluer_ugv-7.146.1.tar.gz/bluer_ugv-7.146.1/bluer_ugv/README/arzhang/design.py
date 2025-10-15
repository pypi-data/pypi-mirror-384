from bluer_objects.README.items import ImageItems
from bluer_sbc.parts.db import db_of_parts
from bluer_sbc.parts.consts import parts_url_prefix

from bluer_ugv.README.arzhang.consts import arzhang_mechanical_design
from bluer_ugv.designs.arzhang.parts import dict_of_parts

docs = [
    {
        "path": "../docs/arzhang/design",
    },
    {
        "path": "../docs/arzhang/design/specs.md",
    },
    {
        "path": "../docs/arzhang/design/parts.md",
        "items": db_of_parts.as_images(
            dict_of_parts,
            reference=parts_url_prefix,
        ),
        "macros": {
            "parts:::": db_of_parts.as_list(
                dict_of_parts,
                reference=parts_url_prefix,
                log=False,
            ),
        },
    },
    {
        "path": "../docs/arzhang/design/mechanical",
        "cols": 2,
        "items": ImageItems(
            {
                f"{arzhang_mechanical_design}/robot-with-cover-v2.png": f"{arzhang_mechanical_design}/robot.stl",
                f"{arzhang_mechanical_design}/robot.png": f"{arzhang_mechanical_design}/robot.stl",
                f"{arzhang_mechanical_design}/cage.png": f"{arzhang_mechanical_design}/cage.stl",
                f"{arzhang_mechanical_design}/measurements.png": "",
            }
        ),
    },
    {
        "path": "../docs/arzhang/design/mechanical/v1.md",
        "items": ImageItems(
            {
                f"{arzhang_mechanical_design}/v1/robot.png": f"{arzhang_mechanical_design}/v1/robot.stl",
                f"{arzhang_mechanical_design}/v1/cage.png": f"{arzhang_mechanical_design}/v1/cage.stl",
                f"{arzhang_mechanical_design}/v1/measurements.png": "",
            }
        ),
    },
]
