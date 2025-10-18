from enum import Enum


class CitraElsetType(Enum):
    MEAN_KOZAI_GP = "SGP4 with Kozai mean motion"
    MEAN_BROUWER_GP = "SGP4 with Brouwer mean motion"
    MEAN_BROUWER_XP = "SGP4-XP with Brouwer mean motion"
    OSCULATING = "SP with Brouwer mean motion"
