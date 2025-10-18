from bluer_objects import README
from bluer_objects.README.items import ImageItems
from bluer_objects.README.consts import assets_url

assets2 = assets_url(
    suffix="shelter",
    volume=2,
)

image_template = assets2 + "/{}?raw=true"


marquee = README.Items(
    [
        {
            "name": "shelter",
            "marquee": f"{assets2}/20251006_181554.jpg",
            "url": "./bluer_sbc/docs/shelter.md",
        }
    ]
)

items = ImageItems(
    {image_template.format(f"{index+1:02}.png"): "" for index in range(4)}
) + ImageItems(
    {
        f"{assets2}/20251005_180841.jpg": "",
        f"{assets2}/20251006_181432.jpg": "",
        f"{assets2}/20251006_181509.jpg": "",
        f"{assets2}/20251006_181554.jpg": "",
    }
)
