from bluer_objects import README
from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.consts import assets2


image_template = assets2 + "swallow/design/head-v1/{}?raw=true"

marquee = README.Items(
    [
        {
            "name": "swallow head",
            "marquee": image_template.format("01.jpg"),
            "url": "./bluer_sbc/docs/swallow-head.md",
        }
    ]
)

items = ImageItems(
    {image_template.format(f"{index+1:02}.jpg"): "" for index in range(6)}
)
