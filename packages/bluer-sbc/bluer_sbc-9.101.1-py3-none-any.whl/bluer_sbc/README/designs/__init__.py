from bluer_sbc.README.design import design
from bluer_sbc.README.designs.cheshmak import items as cheshmak_items
from bluer_sbc.README.designs.battery_bus import items as battery_bus_items
from bluer_sbc.README.designs.swallow import items as swallow_items
from bluer_sbc.README.designs.swallow_head import items as swallow_head_items
from bluer_sbc.README.designs.bryce import items as bryce_items
from bluer_sbc.README.designs.nafha import items as nafha_items
from bluer_sbc.README.designs.shelter import items as shelter_items
from bluer_sbc.README.designs.x import items as x_items
from bluer_sbc.README.designs.ultrasonic_sensor_tester import (
    items as ultrasonic_sensor_tester_items,
)

from bluer_sbc.designs.battery_bus.parts import dict_of_parts as battery_bus_parts
from bluer_sbc.designs.swallow.parts import dict_of_parts as swallow_parts
from bluer_sbc.designs.swallow_head.parts import dict_of_parts as swallow_head_parts

docs = [
    {
        "items": design_info["items"],
        "path": f"../docs/{design_name}.md",
        "macros": design_info.get("macros", {}),
    }
    for design_name, design_info in {
        "battery-bus": design(
            battery_bus_items,
            battery_bus_parts,
        ),
        "bryce": design(
            bryce_items,
        ),
        "cheshmak": design(
            cheshmak_items,
        ),
        "nafha": design(
            nafha_items,
        ),
        "shelter": design(
            shelter_items,
        ),
        "swallow-head": design(
            swallow_head_items,
            swallow_head_parts,
        ),
        "swallow": design(
            swallow_items,
            swallow_parts,
        ),
        "ultrasonic-sensor-tester": design(
            ultrasonic_sensor_tester_items,
        ),
        "x": design(
            x_items,
        ),
    }.items()
]
