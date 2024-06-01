from enum import Enum
from PySide6.QtGui import QPalette, QColor

class farben(Enum):
    NORMAL = {}
    BLAU = {"hell" : (0, 0, 150), "dunkel" : (150, 200, 255)}
    GRUEN = {"hell" : (0, 150, 0), "dunkel" : (150, 255, 150)}
    ROT = {"hell" : (150, 0, 0), "dunkel" : (255, 150, 150)}

@staticmethod
def getTextPalette(farbe:farben, aktuellePalette:QPalette):
    if farbe == farben.NORMAL:
        return aktuellePalette
    modus = "hell"
    if aktuellePalette.color(QPalette.Base).value() < 150:
        modus = "dunkel"
    r, g, b = farbe.value[modus]
    palette = QPalette()
    palette.setColor(QPalette.WindowText, QColor(r, g, b))
    return palette