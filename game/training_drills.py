from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrainingDrill:
    key: str
    name: str
    description: str
    success_hint: str


TRAINING_DRILLS: tuple[TrainingDrill, ...] = (
    TrainingDrill(
        "free",
        "Tiro libero",
        "Prova liberamente mira, potenza, durezza e collisioni.",
        "Nessun obiettivo: osserva il comportamento delle bocce.",
    ),
    TrainingDrill(
        "approach25",
        "Accosto 25 cm",
        "Ferma la boccia entro 25 cm dal jack.",
        "SUCCESSO: distanza ≤ 25 cm.",
    ),
    TrainingDrill(
        "approach50",
        "Accosto 50 cm",
        "Ferma la boccia entro 50 cm dal jack.",
        "SUCCESSO: distanza ≤ 50 cm.",
    ),
    TrainingDrill(
        "hit",
        "Bocciata",
        "Colpisci la boccia bersaglio blu.",
        "SUCCESSO: almeno un contatto con una boccia.",
    ),
    TrainingDrill(
        "cluster",
        "Cluster",
        "Apri il gruppo e resta vicino al jack.",
        "SUCCESSO: collisione + boccia entro 50 cm.",
    ),
    TrainingDrill(
        "corridor",
        "Corridoio",
        "Passa nel corridoio e accosta al jack.",
        "SUCCESSO: boccia nel corridoio e entro 50 cm.",
    ),
    TrainingDrill(
        "penalty",
        "Penalty box",
        "Ferma tutta la boccia nel quadrato 35×35 cm.",
        "SUCCESSO: boccia completamente nel target box.",
    ),
)


def get_drill(index: int) -> TrainingDrill:
    return TRAINING_DRILLS[index % len(TRAINING_DRILLS)]
