from bluer_objects.README.items import ImageItems

from bluer_ugv.README.consts import bluer_ugv_assets
from bluer_ugv.README.arzhang.consts import arzhang_assets2
from bluer_ugv.README.rangin.consts import rangin_assets2
from bluer_ugv.README.swallow.consts import swallow_assets2


docs = [
    {
        "path": "../docs/UGVs",
    },
    {
        "path": "../docs/UGVs/swallow.md",
        "items": ImageItems(
            {
                f"{swallow_assets2}/20250701_2206342_1.gif": "",
                f"{swallow_assets2}/20250913_203635~2_1.gif": "",
            }
        ),
    },
    {
        "path": "../docs/UGVs/arzhang.md",
        "items": ImageItems(
            {
                f"{arzhang_assets2}/20251005_112530.jpg": "",
            }
        ),
    },
    {
        "path": "../docs/UGVs/arzhang2.md",
        "items": ImageItems(
            {
                f"{arzhang_assets2}/20251005_112530.jpg": "",
            }
        ),
    },
    {
        "path": "../docs/UGVs/arzhang3.md",
        "items": ImageItems({f"{bluer_ugv_assets}/bluer-light.png": ""}),
    },
    {
        "path": "../docs/UGVs/rangin.md",
        "items": ImageItems({f"{rangin_assets2}/rangin.png": ""}),
    },
]
