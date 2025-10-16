# Lien entre les noms d'algorithmes et les champs à traiter pour le texte
TEXT_ALGO = {
    "wind": {
        "generic": {
            "params": {
                "wind": {"field": "FF__HAUTEUR10", "default_units": "km/h"},
                "gust": {"field": "RAF__HAUTEUR10", "default_units": "km/h"},
                "direction": {"field": "DD__HAUTEUR10", "default_units": "°"},
                "wwmf": {"field": "WWMF__SOL", "default_units": "wwmf"},
            }
        }
    },
    "tempe": {
        "generic": {
            "params": {"tempe": {"field": "T__HAUTEUR2", "default_units": "°C"}}
        }
    },
    "weather": {
        "generic": {
            "params": {
                "wwmf": {"field": "WWMF__SOL", "default_units": "wwmf"},
                "precip": {"field": "PRECIP__SOL", "default_units": "mm"},
                "rain": {"field": "EAU__SOL", "default_units": "mm"},
                "snow": {"field": "NEIPOT__SOL", "default_units": "cm"},
                "lpn": {"field": "LPN__SOL", "default_units": "m"},
            }
        }
    },
    "thunder": {
        "generic": {
            "params": {
                "orage": {"field": "RISQUE_ORAGE__SOL", "default_units": "%"},
                "gust": {"field": "RAF__HAUTEUR10", "default_units": "m/s"},
            }
        }
    },
    "visibility": {
        "generic": {
            "params": {
                "visi": {"field": "VISI__SOL", "default_units": "m"},
                "type_fg": "TYPE_FG__SOL",
            }
        }
    },
    "nebulosity": {
        "generic": {
            "params": {"nebul": {"field": "NEBUL__SOL", "default_units": "octa"}}
        }
    },
    "rainfall": {
        "generic": {
            "params": {
                "precip": {"field": "PRECIP__SOL", "default_units": "mm"},
                "rain": {"field": "EAU__SOL", "default_units": "mm"},
                "snow": {"field": "NEIPOT__SOL", "default_units": "cm"},
                "lpn": {"field": "LPN__SOL", "default_units": "m"},
            }
        }
    },
    "snow": {
        "generic": {
            "params": {
                "snow": {"field": "NEIPOT__SOL", "default_units": "cm"},
                "lpn": {"field": "LPN__SOL", "default_units": "m"},
            }
        }
    },
}
