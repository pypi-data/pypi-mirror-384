from bluer_objects import README
from bluer_objects.README.items import ImageItems
from bluer_objects.README.consts import assets_url
from bluer_objects.README.consts import designs_url

assets2_battery_bus = assets_url(
    suffix="battery-bus",
    volume=2,
)

marquee = README.Items(
    [
        {
            "name": "battery bus",
            "marquee": f"{assets2_battery_bus}/20251007_221902.jpg",
            "url": "./bluer_sbc/docs/battery-bus.md",
        }
    ]
)

items = ImageItems(
    {
        f"{assets2_battery_bus}/concept.png": "",
        designs_url(
            "battery-bus/electrical/wiring.png?raw=true",
        ): designs_url(
            "battery-bus/electrical/wiring.svg",
        ),
        f"{assets2_battery_bus}/20251007_221902.jpg": "",
        f"{assets2_battery_bus}/20251007_220642.jpg": "",
        f"{assets2_battery_bus}/20251007_220520.jpg": "",
        f"{assets2_battery_bus}/20251007_220601.jpg": "",
    }
)
