from bluer_objects.README.items import ImageItems, Items
from bluer_sbc.parts.db import db_of_parts
from bluer_sbc.parts.consts import parts_url_prefix

from bluer_ugv.README.rangin.items import items
from bluer_ugv.designs.rangin.parts import dict_of_parts
from bluer_ugv.README.rangin.consts import rangin_mechanical_design

docs = [
    {
        "items": items,
        "path": "../docs/rangin",
    },
    {
        "path": "../docs/rangin/parts.md",
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
        "path": "../docs/rangin/mechanical.md",
        "items": Items(
            [
                {
                    "name": "arzhang",
                    "marquee": f"{rangin_mechanical_design}/robot.png?raw=true",
                    "url": f"{rangin_mechanical_design}/robot.stl",
                },
                {
                    "name": "90",
                    "marquee": f"{rangin_mechanical_design}/robot-90.png?raw=true",
                    "url": f"{rangin_mechanical_design}/robot-90.stl",
                },
                {
                    "name": "90 (without the cage)",
                    "marquee": f"{rangin_mechanical_design}/robot-90-2.png?raw=true",
                    "url": f"{rangin_mechanical_design}/robot-90.stl",
                },
            ]
        ),
    },
    {
        "path": "../docs/rangin/computers.md",
    },
]
