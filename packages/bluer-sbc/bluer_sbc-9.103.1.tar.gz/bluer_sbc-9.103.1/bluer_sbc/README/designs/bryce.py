from bluer_objects import README
from bluer_objects.README.items import ImageItems

from bluer_sbc.README.designs.consts import assets2

image_template = assets2 + "bryce/{}?raw=true"

marquee = README.Items(
    [
        {
            "name": "bryce",
            "marquee": image_template.format("08.jpg"),
            "url": "./bluer_sbc/docs/bryce.md",
        }
    ]
)

items = ImageItems(
    {image_template.format(f"{index+1:02}.jpg"): "" for index in range(9)}
)
