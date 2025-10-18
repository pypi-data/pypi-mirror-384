from bluer_objects import README
from bluer_objects.README.items import ImageItems
from bluer_objects.README.consts import assets_url

from bluer_sbc.README.designs.consts import assets2

image_template = assets2 + "shelter/{}?raw=true"

assets2_shelter = assets_url(
    suffix="shelter",
    volume=2,
)

marquee = README.Items(
    [
        {
            "name": "shelter",
            "marquee": f"{assets2_shelter}/20251006_181554.jpg",
            "url": "./bluer_sbc/docs/shelter.md",
        }
    ]
)

items = ImageItems(
    {image_template.format(f"{index+1:02}.png"): "" for index in range(4)}
) + ImageItems(
    {
        f"{assets2_shelter}/20251005_180841.jpg": "",
        f"{assets2_shelter}/20251006_181432.jpg": "",
        f"{assets2_shelter}/20251006_181509.jpg": "",
        f"{assets2_shelter}/20251006_181554.jpg": "",
    }
)
