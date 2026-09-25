from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BocciaBrand:
    key: str
    display_name: str
    official_name: str


# World Boccia Approved Ball Suppliers 2025–2028.
# I nomi sono usati come riferimenti testuali ai produttori.
BOCCIA_BRANDS: tuple[BocciaBrand, ...] = (
    BocciaBrand("apowatec", "Apowatec", "Apowatec"),
    BocciaBrand("boccas_balls", "Boccas Balls", "Boccas Balls, Unipessoal Lda"),
    BocciaBrand("bocha_brasil", "Bocha Brasil", "Bocha Brasil"),
    BocciaBrand("bom_de_bocha", "Bom de Bocha", "Bom De Bocha Esportes"),
    BocciaBrand("handi_life_sport", "Handi Life Sport", "Handi Life Sport"),
    BocciaBrand("polysports", "PolySports", "PolySports"),
    BocciaBrand("ree_sport", "Ree Sport", "Ree Sport"),
    BocciaBrand(
        "prodigy_frontier",
        "Prodigy Frontier",
        "Tutti per Tutti / Prodigy Frontier",
    ),
    BocciaBrand("victory_sports", "Victory Sports", "Victory Sports"),
)


def get_brand(key: str) -> BocciaBrand:
    normalized = str(key).strip().lower()
    for brand in BOCCIA_BRANDS:
        if brand.key == normalized:
            return brand
    return BOCCIA_BRANDS[4]


def cycle_brand(current_key: str, direction: int = 1) -> BocciaBrand:
    current = get_brand(current_key)
    index = next(
        index
        for index, brand in enumerate(BOCCIA_BRANDS)
        if brand.key == current.key
    )
    index = (index + direction) % len(BOCCIA_BRANDS)
    return BOCCIA_BRANDS[index]
