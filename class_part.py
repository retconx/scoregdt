from PySide6.QtWidgets import QGroupBox, QGridLayout
import xml.etree.ElementTree as ElementTree

from enum import Enum

class PartTyp(Enum):
    FRAME = "Frame"
    GROUPBOX = "GroupBox"
    
class Part:
    def __init__(self, id:str, typ:PartTyp, titel:str, zeile:int, spalte:int, geschlechtpruefung:bool, bisherigesRoot:ElementTree.Element):
        if id != "":
            self.id = id
        else:
            self.id = self.getNeueId(bisherigesRoot)
        self.typ = typ
        self.titel = titel
        self.zeile = zeile
        self.spalte = spalte
        self.geschlechtpruefung = geschlechtpruefung
    
    def getNeueId(self, bisherigesRoot:ElementTree.Element):
        """
        Gibt eine neue eindeutige Id zurück
        Parameter:
            bisherigesRoot:ElementTree.Element
        Return:
            Neue Id:str
        """
        ids = []
        for partElement in bisherigesRoot.findall("part"):
            ids.append(int(str(partElement.get("id"))))
        letzteId = ids[len(ids) - 1]
        while letzteId in ids:
            letzteId += 1
        return letzteId
    
    def getId(self):
        return self.id
    
    def getTyp(self):
        return self.typ
    
    def getTitel(self):
        return self.titel
    
    def getZeile(self):
        return self.zeile
    
    def getSpalte(self):
        return self.spalte
    
    def geschlechtpruefungAktiv(self):
        return self.geschlechtpruefung
