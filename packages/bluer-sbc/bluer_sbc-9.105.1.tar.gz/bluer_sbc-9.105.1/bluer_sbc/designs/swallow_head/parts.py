dict_of_parts = {
    "rpi": "",
    "XL4015": "",
    "470-mF": "",
    "Polyfuse": "optional",
    "TVS-diode": "",
    "resistor": "7 x 330-470 Ω + N x 2.2 kΩ + N x 3.3 kΩ",
    "LED": "green + red + yellow + 4 x blue",
    "rpi-camera": "",
    "PCB-single-14x9_5": "2 x",
    "PCB-double-9x7": "2 x",
    "pushbutton": "",
    "ultrasonic-sensor": "4 x",
    "connector": "1 female",
    "nuts-bolts-spacers": " + ".join(
        [
            "M2: ({})".format(
                " + ".join(
                    [
                        "2 x bolt",
                        "2 x 5 mm spacer",
                        "4 x nut",
                    ]
                )
            ),
            "M2.5: ({})".format(
                " + ".join(
                    [
                        "4 x bolt",
                        "8 x 10 mm spacer",
                        "4 x nut",
                    ]
                )
            ),
            "M3: ({})".format(
                " + ".join(
                    [
                        "1 x bolt",
                        "3 x 35 mm spacer",
                        "3 x 25 mm spacer",
                        "7 x 15 mm spacer",
                        "4 x 5 mm spacer",
                        "5 x nut",
                    ]
                )
            ),
        ]
    ),
    "plexiglass": "14 cm x 9.5 cm",
    "white-terminal": "2 x",
    "dupont-cables": "1 x 30 cm + 1 x 10 cm",
    "16-awg-wire": "40 cm x (red + black/blue)",
    "solid-cable-1-15": "10 cm x (red + black/blue)",
    "strong-thread": "1 m",
    "pin-headers": "1 x (female, 2 x 40) -> 2 x 20 + 2 x (male, 1 x 40) -> 4 x 6 + 4 x 2 + 2 x 20",
}
