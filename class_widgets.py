import xml.etree.ElementTree as ElementTree
from enum import Enum
import re, class_enums, logger, molGrammConvert
from PySide6.QtWidgets import (
    QComboBox,
    QRadioButton,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QLabel
)

class WidgetTyp(Enum):
    CHECKBOX = "CheckBox"
    COMBOBOX = "ComboBox"
    LINEEDIT = "LineEdit"
    RADIOBUTTON = "RadioButton"

regexZahl = r"^-?\d+([.,]\d+)?$"

class Widget():
    # def __init__(self, id:str, partId:str, titel:str, erklaerung:str, einheit:str, bisherigesRoot:ElementTree.Element):
    def __init__(self, id:str, partId:str, titel:str, erklaerung:str, einheit:str, alterspruefung:bool, groessepruefung:bool, gewichtpruefung:bool):
        if id != "":
            self.id = id
        # else:
        #     self.id = self.getNeueId(bisherigesRoot)
        self.partId = partId
        self.titel = titel
        self.erklaerung = erklaerung
        self.einheit = einheit
        self.alterspruefung = alterspruefung
        self.groessepruefung = groessepruefung
        self.gewichtpruefung = gewichtpruefung
        self.titelbreite = -1

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
    
    def groessepruefungAktiv(self):
        return self.groessepruefung
    
    def gewichtpruefungAktiv(self):
        return self.gewichtpruefung
    
    def setTitelbreite(self, width:int):
        self.titelbreite = width

    def getTitelbreite(self):
        return self.titelbreite


class ComboBox(Widget):
    def __init__(self, id:str, partId:str, titel:str, erklaerung:str, einheit:str, itemsUndWerte:list, defaultIndex:int, alterspruefung:bool, groessepruefung:bool, gewichtpruefung:bool):
        super().__init__(id, partId, titel, erklaerung, einheit, alterspruefung, groessepruefung, gewichtpruefung)
        # itemsUndWerte: Liste mit (item, wert)-Tuples
        self.itemsUndWerte = itemsUndWerte
        self.combobox = QComboBox()
        for itemUndWert in self.itemsUndWerte:
            itemText = itemUndWert[0]
            self.combobox.addItem(itemText)
        self.defaultIndex = defaultIndex
        self.combobox.setCurrentIndex(defaultIndex)
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
    def __init__(self, id, partId:str, buttongroup:str, titel:str, erklaerung:str, einheit:str, wert:str, checked:bool, alterspruefung:bool, altersregel:str, geschlechtpruefung:bool, groessepruefung:bool, gewichtpruefung:bool):
        super().__init__(id, partId, titel, erklaerung, einheit, alterspruefung, groessepruefung, gewichtpruefung)
        self.buttongroup = buttongroup
        self.wert = wert
        self.checked = checked
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.checked == True)
        self.typ = WidgetTyp.CHECKBOX
        self.altersregel = altersregel
        self.geschlechtpruefung = geschlechtpruefung
        
    def getButtongroup(self):
        return self.buttongroup
    
    def getQt(self):
        return self.checkbox
    
    def getWert(self):
        return self.wert
    
    def getTyp(self):
        return self.typ
    
    def isChecked(self):
        return self.checkbox.isChecked()
    
    def getAltersregeln(self):
        # UND entfernen
        regeln = self.altersregel.split("UND")
        return regeln
    
    def geschlechtpruefungAktiv(self):
        return self.geschlechtpruefung
    
class LineEdit(Widget):
    def __init__(self, id, partId:str, titel:str, erklaerung:str, einheit:str, regexPattern:str, alterspruefung:bool, defaultWert:str, groessepruefung:bool, gewichtpruefung:bool):
        super().__init__(id, partId, titel, erklaerung, einheit, alterspruefung, groessepruefung, gewichtpruefung)
        self.regexPattern = regexPattern
        self.lineedit = QLineEdit(defaultWert)
        self.typ = WidgetTyp.LINEEDIT
        self.zahlengrenzen = {}
        self.relativgrenzen = {}
        
    def getQt(self):
        return self.lineedit
    
    def getWert(self, einheitToggles:dict):
        if re.match(regexZahl, self.lineedit.text()) != None:
            zahl = float(self.lineedit.text().replace(",", "."))
            if self.getId() in einheitToggles:
                et = einheitToggles[self.getId()]
                aktuelleEinheit = et.getAktuelleEinheit()
                if self.einheit == aktuelleEinheit and self.einheit == et.getBerechnungseinheit():
                    return str(zahl)
                elif self.einheit != aktuelleEinheit and self.einheit != et.getBerechnungseinheit():
                    return str(zahl)
                elif self.einheit != aktuelleEinheit and self.einheit == et.getBerechnungseinheit():
                    return str(molGrammConvert.einheitenKonvertieren(et.getStrukturformel(), zahl, molGrammConvert.getKonvertierungseinheiten(et.getEinheitenListe()), False))
                elif self.einheit == aktuelleEinheit and self.einheit != et.getBerechnungseinheit():
                    return str(molGrammConvert.einheitenKonvertieren(et.getStrukturformel(), zahl, molGrammConvert.getKonvertierungseinheiten(et.getEinheitenListe()), True))
            else:
                return str(zahl)
        return self.lineedit.text()
    
    def getEinheit(self, einheitToggles:dict = {}):
        if self.getId() in einheitToggles:
            et = einheitToggles[self.getId()]
            return et.getAktuelleEinheit()
        return self.einheit

    def getWertOhneFaktor(self):
        return str(float(self.lineedit.text().replace(",", ".")))
    
    def regexOk(self):
        return re.match(self.regexPattern, self.lineedit.text()) != None
    
    def getTyp(self):
        return self.typ
    
    def addZahlengrenze(self, zahl:float, regelart:class_enums.Regelarten):
        self.zahlengrenzen[zahl] = regelart
    
    def entferneZahlengrenzen(self):
        self.zahlengrenzen.clear()

    def zahlengrenzeGesetzt(self):
        return len(self.zahlengrenzen) > 0
    
    def getZahlengrenzen(self):
        return self.zahlengrenzen
    
    def zahlengrenzregelnErfuellt(self):
        regelnErfuellt = False
        for zahlengrenze in self.zahlengrenzen:
            if re.match(regexZahl, self.lineedit.text()) != None:
                wert = float(self.lineedit.text().replace(",", "."))
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
    
    def addRelativgrenze(self, id:str, regelart:class_enums.Regelarten):
        self.relativgrenzen[id] = regelart
    
    def relativgrenzeGesetzt(self):
        return len(self.relativgrenzen) > 0
    
    def getRelativgrenzen(self):
        return self.relativgrenzen
    
class RadioButton(Widget):
    def __init__(self, id, partId:str, titel:str, erklaerung:str, einheit:str, wert:str, checked:bool, alterspruefung:bool, altersregel:str, groessepruefung:bool, gewichtpruefung:bool):
        super().__init__(id, partId, titel, erklaerung, einheit, alterspruefung, groessepruefung, gewichtpruefung)
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
    
    def getAltersregeln(self):
        # UND entfernrn
        regeln = self.altersregel.split("UND")
        return regeln

class EinheitToggle():
    def __init__(self, lineEditWidget:LineEdit, konvertgruppe:str, einheitenListe:list, strukturformel:str, zahlengrenzen:list, konvertIstBerechnungseinheit:bool, mitButton:bool):
        self.lineEditWidget = lineEditWidget
        self.konvertgruppe = konvertgruppe
        self.einheitenListe = einheitenListe
        self.strukturformel = strukturformel
        self.konvertIstBerechnungseinheit = konvertIstBerechnungseinheit
        self.mitButton = mitButton
        self.toggleButton = None
        if mitButton:
            self.toggleButton = QPushButton(einheitenListe[1])
            self.toggleButton.setStyleSheet("font-weight:normal")
        self.einheitenLabel = None
        self.aktuelleEinheit = einheitenListe[0]
        self.zahlengrenzen = zahlengrenzen
        self.zahlengrenzenListe = []
        self.zahlengrenzenListe.append(zahlengrenzen)
        zahlengrenzenNeu = []
        ke = molGrammConvert.getKonvertierungseinheiten(einheitenListe)
        for zg in zahlengrenzen:
            zahlengrenzenNeu.append(molGrammConvert.einheitenKonvertieren(strukturformel, zg, ke, True))
        self.zahlengrenzenListe.append(zahlengrenzenNeu)
        self.aktuelleZahlengrenzen = self.zahlengrenzenListe[0]

    def getEinheitenListe(self):
        return self.einheitenListe
    
    def getLineEdit(self):
        return self.lineEditWidget.getQt()
    
    def getKonvertgruppe(self):
        return self.konvertgruppe
    
    def getBerechnungseinheit(self):
        if self.konvertIstBerechnungseinheit:
            return self.einheitenListe[1]
        return self.einheitenListe[0]
            
    def getQt(self):
        return self.toggleButton
    
    def setEinheitenLabel(self, label:QLabel):
        self.einheitenLabel = label
    
    def getEinheitenLabel(self):
        return self.einheitenLabel
    
    def getAktuelleEinheit(self):
        return self.aktuelleEinheit
    
    def getStrukturformel(self):
        return self.strukturformel
    
    def getAktuelleZahlengrenzenAlsString(self):
        zahlengrenzenAlsString = []
        for azg in self.aktuelleZahlengrenzen: 
            azgAlsString = "{:.1f}".format(azg)
            zahlengrenzenAlsString.append(azgAlsString.replace(".", ",").replace(",0", ""))
        return zahlengrenzenAlsString
    
    def toggle(self):
        if self.aktuelleEinheit == self.einheitenListe[0]:
            self.aktuelleEinheit = self.einheitenListe[1]
            self.aktuelleZahlengrenzen = self.zahlengrenzenListe[1]
        else:
            self.aktuelleEinheit = self.einheitenListe[0]
            self.aktuelleZahlengrenzen = self.zahlengrenzenListe[0]
        # Zahlengrenzen im LineEdit togglen
        lineEditZahlengrenzen = self.lineEditWidget.getZahlengrenzen()
        grenzregeln = []
        for zg in lineEditZahlengrenzen:
            grenzregeln.append(lineEditZahlengrenzen[zg])
        self.lineEditWidget.entferneZahlengrenzen()
        i = 0
        for zg in self.aktuelleZahlengrenzen:
            self.lineEditWidget.addZahlengrenze(zg, grenzregeln[i])
            i += 1

@staticmethod
def getNaechstliegendeZahl(zahlenliste:list, zahl:float):
    """
    Gibt die Zahl einer Liste zurück, die einer übergebenen Zahl am nächsten liegt
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