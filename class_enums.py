from enum import Enum

class Regelarten(Enum):
    KLEINERALS = "KLEINERALS"
    KLEINERGLEICHALS = "KLEINERGLEICHALS"
    ISTGLEICH = "ISTGLEICH"
    GROESSERALS = "GROESSERALS"
    GROESSERGLEICHALS = "GROESSERGLEICHALS"

class Rechenarten(Enum):
    PLUS = "PLUS"
    MINUS = "MINUS"
    MAL = "MAL"
    DURCH = "DURCH"
    HOCH = "HOCH"