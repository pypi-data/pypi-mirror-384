from bluer_objects import README
from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.consts import assets2


image_template = assets2 + "swallow/design/v5/{}?raw=true"

marquee = README.Items(
    [
        {
            "name": "swallow",
            "marquee": image_template.format("01.jpg"),
            "url": "./bluer_sbc/docs/swallow.md",
        }
    ]
)

items = ImageItems(
    {image_template.format(f"{index+1:02}.jpg"): "" for index in range(6)}
)
