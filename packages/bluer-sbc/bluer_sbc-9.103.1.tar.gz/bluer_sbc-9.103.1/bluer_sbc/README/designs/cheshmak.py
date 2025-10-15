from bluer_objects import README
from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.consts import assets2

image_template = assets2 + "cheshmak/{}?raw=true"

marquee = README.Items(
    [
        {
            "name": "cheshmak",
            "marquee": image_template.format("01.png"),
            "url": "./bluer_sbc/docs/cheshmak.md",
        }
    ]
)

items = ImageItems(
    {image_template.format(f"{index+1:02}.png"): "" for index in range(1)}
)
