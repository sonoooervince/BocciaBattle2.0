from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RealBocciaSet:
    key: str
    brand_key: str
    brand_name: str
    model: str
    hardnesses: tuple[str, ...]
    material: str
    gold_cost: int
    source: str
    verified_real_product: bool = True


REAL_BOCCIA_SETS: tuple[RealBocciaSet, ...] = (
    RealBocciaSet(
        "handi_standard_pro",
        "handi_life_sport",
        "Handi Life Sport",
        "Boccia Standard Pro",
        ("Medium",),
        "PU",
        0,
        "Handi Life Sport 2025 catalogue",
    ),
    RealBocciaSet(
        "handi_superior_classic",
        "handi_life_sport",
        "Handi Life Sport",
        "Boccia Superior Classic",
        ("Hard", "Medium-Hard", "Medium", "Medium-Soft", "Soft"),
        "PU",
        900,
        "Handi Life Sport 2025 catalogue",
    ),
    RealBocciaSet(
        "handi_superior_supersoft",
        "handi_life_sport",
        "Handi Life Sport",
        "Boccia Superior Supersoft",
        ("Supersoft",),
        "PU",
        1200,
        "Handi Life Sport 2025 catalogue",
    ),
    RealBocciaSet(
        "handi_superior_shine",
        "handi_life_sport",
        "Handi Life Sport",
        "Boccia Superior Shine",
        ("Medium-Hard", "Medium", "Medium-Soft"),
        "High-tech PU",
        1200,
        "Handi Life Sport 2025 catalogue",
    ),
    RealBocciaSet(
        "handi_ledo_suede",
        "handi_life_sport",
        "Handi Life Sport",
        "Boccia LEDO Suede",
        ("Hard", "Medium-Hard", "Medium", "Medium-Soft", "Soft", "Supersoft"),
        "Suede leather",
        1500,
        "Handi Life Sport 2025 catalogue",
    ),
    RealBocciaSet(
        "handi_new_standard",
        "handi_life_sport",
        "Handi Life Sport",
        "Boccia New Standard",
        ("Medium-Hard",),
        "Leather",
        650,
        "Handi Life Sport 2025 catalogue",
    ),
    RealBocciaSet(
        "apowatec_tokyo",
        "apowatec",
        "Apowatec",
        "TOKYO",
        ("Soft", "Medium", "Hard"),
        "Synthetic leather",
        1800,
        "World Boccia / Apowatec price list",
    ),
    RealBocciaSet(
        "apowatec_connect_pro",
        "apowatec",
        "Apowatec",
        "CONNECT Pro",
        ("Super Soft", "Soft", "Medium", "Hard"),
        "Synthetic leather",
        1400,
        "Apowatec product catalogue",
    ),
    RealBocciaSet(
        "apowatec_820r_plus",
        "apowatec",
        "Apowatec",
        "820R Plus",
        ("Soft", "Medium", "Hard"),
        "Synthetic leather",
        1100,
        "World Boccia / Apowatec price list",
    ),
    RealBocciaSet(
        "apowatec_raijin_r",
        "apowatec",
        "Apowatec",
        "RAIJIN-R",
        ("Soft", "Medium Soft", "Medium", "Medium Hard", "Hard"),
        "Competition material",
        2100,
        "World Boccia / Apowatec price list",
    ),
    RealBocciaSet(
        "polysports_apollo",
        "polysports",
        "PolySports",
        "Apollo",
        ("Soft", "Medium", "Hard"),
        "Competition material",
        1500,
        "World Boccia / PolySports price list",
    ),
    RealBocciaSet(
        "polysports_ares",
        "polysports",
        "PolySports",
        "Ares",
        ("Soft", "Medium", "Hard"),
        "Competition material",
        1500,
        "World Boccia / PolySports price list",
    ),
    RealBocciaSet(
        "polysports_hermes",
        "polysports",
        "PolySports",
        "Hermes",
        ("Soft", "Medium", "Hard"),
        "Competition material",
        1500,
        "World Boccia / PolySports price list",
    ),
    RealBocciaSet(
        "polysports_dionysus",
        "polysports",
        "PolySports",
        "Dionysus",
        ("Soft", "Medium", "Hard"),
        "Competition material",
        700,
        "World Boccia / PolySports price list",
    ),
    RealBocciaSet(
        "polysports_zeus",
        "polysports",
        "PolySports",
        "Zeus",
        ("Soft", "Medium", "Hard"),
        "Competition material",
        2400,
        "World Boccia / PolySports price list",
    ),
    RealBocciaSet(
        "polysports_genuine_leather",
        "polysports",
        "PolySports",
        "Genuine Leather",
        ("Soft", "Medium", "Hard"),
        "Genuine leather",
        1700,
        "World Boccia / PolySports price list",
    ),
    RealBocciaSet(
        "ree_dream_back_skin",
        "ree_sport",
        "Ree Sport",
        "Dream - Natural Back Skin",
        ("Soft", "Medium", "Hard"),
        "Natural back skin",
        1700,
        "World Boccia / Ree Sports price list",
    ),
    RealBocciaSet(
        "ree_dream_leatherette",
        "ree_sport",
        "Ree Sport",
        "Dream - Leatherette",
        ("Soft", "Medium", "Hard"),
        "Leatherette",
        1500,
        "World Boccia / Ree Sports price list",
    ),
    RealBocciaSet(
        "ree_dream_cowhide",
        "ree_sport",
        "Ree Sport",
        "Dream - Natural Cowhide",
        ("Soft", "Medium", "Hard", "Super Hard"),
        "Natural cowhide",
        1800,
        "World Boccia / Ree Sports price list",
    ),
    RealBocciaSet(
        "ree_dream_sheepskin",
        "ree_sport",
        "Ree Sport",
        "Dream - Natural Sheepskin",
        ("Soft", "Medium", "Hard"),
        "Natural sheepskin",
        1800,
        "World Boccia / Ree Sports price list",
    ),
    RealBocciaSet(
        "boccas_brasil",
        "boccas_balls",
        "Boccas Balls",
        "Boccas Brasil",
        ("Super Soft", "Soft", "Hard"),
        "Competition material",
        1200,
        "Boccas official store",
    ),
    RealBocciaSet(
        "boccas_povoa",
        "boccas_balls",
        "Boccas Balls",
        "Boccas Póvoa",
        ("Soft", "Medium", "Hard"),
        "Competition material",
        1200,
        "Boccas official store",
    ),
    RealBocciaSet(
        "boccas_leather_tokyo",
        "boccas_balls",
        "Boccas Balls",
        "Boccas Leather Tokyo",
        ("Super Soft", "Soft", "Hard"),
        "Leather",
        1900,
        "Boccas official store",
    ),
    RealBocciaSet(
        "boccas_suede_tokyo",
        "boccas_balls",
        "Boccas Balls",
        "Boccas Suede Tokyo",
        ("Super Soft", "Soft", "Hard"),
        "Suede",
        1900,
        "Boccas official store",
    ),
    RealBocciaSet(
        "bom_natural_leather",
        "bom_de_bocha",
        "Bom de Bocha",
        "Kit de Bocha Adaptada Paralímpica em Couro Natural com Maleta",
        ("Soft", "Medium", "Hard"),
        "Natural leather",
        1100,
        "Bom de Bocha official store",
    ),
    RealBocciaSet(
        "bom_synthetic_leather",
        "bom_de_bocha",
        "Bom de Bocha",
        "Kit de Bocha Adaptada Paralímpica em Couro Sintético com Maleta",
        ("Soft", "Medium", "Hard"),
        "Synthetic leather",
        900,
        "Bom de Bocha official store",
    ),
    RealBocciaSet(
        "tutti_t2020",
        "prodigy_frontier",
        "Tutti per Tutti / Prodigy Frontier",
        "T2020",
        ("Hard", "Medium", "Soft"),
        "Synthetic leather",
        900,
        "Tutti per Tutti catalogue",
    ),
    RealBocciaSet(
        "tutti_elite",
        "prodigy_frontier",
        "Tutti per Tutti / Prodigy Frontier",
        "Elite",
        ("Super Hard", "Hard", "Medium", "Soft"),
        "Synthetic suede",
        1600,
        "Tutti per Tutti / retailer catalogue",
    ),
    RealBocciaSet(
        "victory_competition_set",
        "victory_sports",
        "Victory Sports",
        "Boccia Ball with Cloth Bag",
        (
            "Super Soft",
            "Soft",
            "Soft Medium",
            "Medium",
            "Hard",
            "Super Hard",
        ),
        "Natural / artificial leather",
        1900,
        "World Boccia / Victory Sports brochure",
    ),
)


def get_real_set(key: str) -> RealBocciaSet:
    for item in REAL_BOCCIA_SETS:
        if item.key == key:
            return item
    return REAL_BOCCIA_SETS[0]


def approximate_profile_key(hardness: str) -> str:
    value = hardness.strip().lower().replace("-", " ")
    if "super soft" in value or "supersoft" in value:
        return "super_morbido"
    if "medium soft" in value or "soft medium" in value:
        return "morbide"
    if value == "soft":
        return "morbide"
    if "super hard" in value:
        return "super_duro"
    if "medium hard" in value:
        return "dura"
    if value == "hard":
        return "dura"
    return "medie"
