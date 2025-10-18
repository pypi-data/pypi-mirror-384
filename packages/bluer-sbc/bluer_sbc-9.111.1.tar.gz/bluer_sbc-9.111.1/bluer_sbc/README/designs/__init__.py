from bluer_sbc.README.design import design
from bluer_sbc.README.designs import (
    cheshmak,
    battery_bus,
    adapter_bus,
    swallow,
    swallow_head,
    bryce,
    nafha,
    shelter,
    ultrasonic_sensor_tester,
    x,
)


docs = [
    {
        "items": design_info["items"],
        "path": f"../docs/{design_name}.md",
        "macros": design_info.get("macros", {}),
    }
    for design_name, design_info in {
        "battery-bus": design(
            battery_bus.items,
            battery_bus.parts,
        ),
        "adapter-bus": design(
            adapter_bus.items,
            adapter_bus.parts,
        ),
        "bryce": design(
            bryce.items,
        ),
        "cheshmak": design(
            cheshmak.items,
        ),
        "nafha": design(
            nafha.items,
        ),
        "shelter": design(
            shelter.items,
        ),
        "swallow-head": design(
            swallow_head.items,
            swallow_head.parts,
        ),
        "swallow": design(
            swallow.items,
            swallow.parts,
        ),
        "ultrasonic-sensor-tester": design(
            ultrasonic_sensor_tester.items,
        ),
        "x": design(
            x.items,
        ),
    }.items()
]
