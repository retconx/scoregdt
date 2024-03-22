import xml.etree.ElementTree as ElementTree
from enum import Enum
import re, class_enums, logger
from PySide6.QtWidgets import (
    QComboBox,
    QRadioButton,
    QLineEdit,
    QCheckBox
)

class WidgetTyp(Enum):
    CHECKBOX = "CheckBox"
    COMBOBOX = "ComboBox"
    LINEEDIT = "LineEdit"
    RADIOBUTTON = "RadioButton"

regexZahl = r"^\d+([.,]\d)?$"

class Widget():
    # def __init__(self, id:str, partId:str, titel:str, erklaerung:str, einheit:str, bisherigesRoot:ElementTree.Element):
    def __init__(self, id:str, partId:str, titel:str, erklaerung:str, einheit:str, alterspruefung:bool):
        if id != "":
            self.id = id
        # else:
        #     self.id = self.getNeueId(bisherigesRoot)
        self.partId = partId
        self.titel = titel
        self.erklaerung = erklaerung
        self.einheit = einheit
        self.alterspruefung = alterspruefung

    # def getNeueId(self, bisherigesRoot:ElementTree.Element):
    #     """
    #     Gibt eine neue eindeutige Id zurück
    #     Parameter:
    #         bisherigesRoot:ElementTree.Element
    #     Return:
    #         Neue Id:str
    #     """
    #     ids = []
    #     for partElement in bisherigesRoot.findall("part"):
    #         for widgetElement in partElement:
    #             ids.append(int(str(widgetElement.get("id"))))
    #     letzteId = ids[len(ids) - 1]
    #     while letzteId in ids:
    #         letzteId += 1
    #     return letzteId
    
    def getId(self):
        return self.id
    
    def getPartId(self):
        return self.partId
    
    def getTitel(self):
        return self.titel
    
    def getErklaerung(self):
        return self.erklaerung
    
    def getEinheit(self):
        return self.einheit
    
    def alterspruefungAktiv(self):
        return self.alterspruefung


class ComboBox(Widget):
    def __init__(self, id:str, partId:str, titel:str, erklaerung:str, einheit:str, itemsUndWerte:list, alterspruefung:bool):
        super().__init__(id, partId, titel, erklaerung, einheit, alterspruefung)
        # itemsUndWerte: Liste mit (item, wert)-Tuples
        self.itemsUndWerte = itemsUndWerte
        self.combobox = QComboBox()
        for itemUndWert in self.itemsUndWerte:
            itemText = itemUndWert[0]
            self.combobox.addItem(itemText)
        self.typ = WidgetTyp.COMBOBOX
    
    def getQt(self):
        return self.combobox
    
    def getItemText(self, itemNummer:int):
        return self.itemsUndWerte[itemNummer][0]
    
    def getWert(self, itemNummer:int):
        return self.itemsUndWerte[itemNummer][1]
    
    def getTyp(self):
        return self.typ
    
class CheckBox(Widget):
    def __init__(self, id, partId:str, titel:str, erklaerung:str, einheit:str, wert:str, checked:bool, alterspruefung:bool, altersregel:str):
        super().__init__(id, partId, titel, erklaerung, einheit, alterspruefung)
        self.wert = wert
        self.checked = checked
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.checked == True)
        self.typ = WidgetTyp.CHECKBOX
        self.altersregel = altersregel
        
    def getQt(self):
        return self.checkbox
    
    def getWert(self):
        return self.wert
    
    def getTyp(self):
        return self.typ
    
    def isChecked(self):
        return self.checkbox.isChecked()
    
    def getAltersregel(self):
        return self.altersregel
    
class LineEdit(Widget):
    def __init__(self, id, partId:str, titel:str, erklaerung:str, einheit:str, regexPattern:str, alterspruefung:bool):
        super().__init__(id, partId, titel, erklaerung, einheit, alterspruefung)
        self.regexPattern = regexPattern
        self.lineedit = QLineEdit()
        self.typ = WidgetTyp.LINEEDIT
        self.zahlengrenzen = {}
        self.faktor = 1
        
    def getQt(self):
        return self.lineedit
    
    def getWert(self):
        if re.match(regexZahl, self.lineedit.text()) != None:
            zahl = float(self.lineedit.text().replace(",", "."))
            faktorzahl = self.faktor * zahl
            logger.logger.info("Faktor " + str(self.faktor) + " auf " + self.lineedit.text() + " angewendet")
            return str(faktorzahl)
        return self.lineedit.text()
    
    def getWertOhneFaktor(self):
        return str(float(self.lineedit.text().replace(",", ".")))
    
    def regexOk(self):
        return re.match(self.regexPattern, self.lineedit.text()) != None
    
    def getTyp(self):
        return self.typ
    
    def addZahlengrenze(self, zahl:float, regelart:class_enums.Regelarten):
        self.zahlengrenzen[zahl] = regelart

    def zahlengrenzeGesetzt(self):
        return len(self.zahlengrenzen) > 0
    
    def zahlengrenzregelnErfuellt(self):
        regelnErfuellt = False
        for zahlengrenze in self.zahlengrenzen:
            if re.match(regexZahl, self.lineedit.text()) != None:
                wert = float(self.lineedit.text())
                if self.zahlengrenzen[zahlengrenze] == class_enums.Regelarten.KLEINERALS:
                    regelnErfuellt = wert < zahlengrenze
                elif self.zahlengrenzen[zahlengrenze] == class_enums.Regelarten.KLEINERGLEICHALS:
                    regelnErfuellt = wert <= zahlengrenze
                elif self.zahlengrenzen[zahlengrenze] == class_enums.Regelarten.ISTGLEICH:
                    regelnErfuellt = wert == zahlengrenze
                elif self.zahlengrenzen[zahlengrenze] == class_enums.Regelarten.GROESSERALS:
                    regelnErfuellt = wert > zahlengrenze
                elif self.zahlengrenzen[zahlengrenze] == class_enums.Regelarten.GROESSERGLEICHALS:
                    regelnErfuellt = wert >= zahlengrenze
            else:
                logger.logger.warning("Regelprüfung mit Vergleichszahl nicht möglich, da LineEdit-Wert " + self.lineedit.text() + " keine Zahl")
            if not regelnErfuellt:
                break
        return regelnErfuellt

    def getGrenzzahl(self, zahl:float):
        grenzen = [grenze for grenze in self.zahlengrenzen]
        return getNaechstliegendeZahl(grenzen, zahl)
    
    def setFaktor(self, faktor:float):
        self.faktor = faktor
    
class RadioButton(Widget):
    def __init__(self, id, partId:str, titel:str, erklaerung:str, einheit:str, wert:str, checked:bool, alterspruefung:bool, altersregel:str):
        super().__init__(id, partId, titel, erklaerung, einheit, alterspruefung)
        self.wert = wert
        self.checked = checked
        self.radiobutton = QRadioButton()
        self.radiobutton.setChecked(self.checked == True)
        self.typ = WidgetTyp.RADIOBUTTON
        self.altersregel = altersregel
        
    def getQt(self):
        return self.radiobutton
    
    def getWert(self):
        return self.wert
    
    def getTyp(self):
        return self.typ
    
    def isChecked(self):
        return self.radiobutton.isChecked()
    
    def getAltersregel(self):
        return self.altersregel

@staticmethod
def getNaechstliegendeZahl(zahlenliste:list, zahl:float):
    """
    Gibt die die Zahl einer Liste zurück, die einer übergebenen Zahl am nächsten liegt
    Parameter:
        zahlenliste:list
        zahl:float, zu prüfende Zahl
    Return:
        Der zu prüfenden Zahl am nächsten liegende Zahl der zahlenliste
    """
    grenzzahl = zahl
    differenzen = [abs(zahl - zahlengrenze) for zahlengrenze in zahlenliste]
    differenzenKopie = differenzen.copy()
    differenzenKopie.sort()
    kleinsteDifferenz = differenzenKopie[0]
    i = 0
    for differenz in differenzen:
        if differenz == kleinsteDifferenz:
            grenzzahl = zahlenliste[i]
            break
        i += 1
    return grenzzahl