import re
from enum import Enum

atomgewicht = {
    "H" : 1.008,
    "C" : 12.011,
    "N" : 14.007,
    "O" : 15.999,
    "Na" : 22.990,
    "Cl" : 35.45,
    "K" : 39.098,
    "Ca" : 40.078,
    "Fe" : 55.845
}

class Konvertierungseinheiten(Enum):
    GpL_MpL = 1 # g/l - mmol/l
    MGpDL_MMpL = 10 # mg/dl - mmol/l
    MGpDL_MYMpL = 10000 # mg/dl - µmol/l
    MGpL_MGpDL = 0.1 # mg/l - mg/dl
    GpDL_GpL = 10 # g/l - g/dl
    PROZ_MMpM = 1 # % - mmol/mol (HbA1c)
    TrigMGpDL_TrigMMpL = 0.0113 # Triglyzeride mg/dl - mmol/l

@staticmethod
def einheitenKonvertieren(formel:str, menge:float, einheiten:Konvertierungseinheiten, linksNachRechts:bool):
    """
    Konvertiert in die entsprechenden Konvertierungseinheiten
    Parameter: 
        formel:str chemische Strukturformel im Formal C27-H46-O 
        menge:float
        einheiten:Konvertierungseinheiten - in einander zu konvertierende Einheiten
        linksNachRechts:bool - True konvertiert erste in zweite, False zweite in erste
    Return:
        Konvertiertes Ergebnis
    """
    erg = 0
    if formel != "None":
        stoffe = formel.split("-")
        atome = {}
        for stoff in stoffe:
            buchstabe = re.search(r"^\D{1,2}", stoff)
            zahl = re.search(r"\d{1,}", stoff)
            if zahl != None:
                atome[buchstabe.group(0)] = int(zahl.group(0)) # type: ignore
            else:
                atome[buchstabe.group(0)] = 1 # type: ignore
        molekulargewicht = 0
        for atom in atome:
            molekulargewicht += atomgewicht[atom] * atome[atom]
        linksNachRechtsExponent = -1
        if not linksNachRechts:
            linksNachRechtsExponent = 1
        erg = menge * pow(molekulargewicht / einheiten.value, linksNachRechtsExponent)
    elif einheiten == Konvertierungseinheiten.PROZ_MMpM: # HbA1c
        if linksNachRechts:
            erg = (menge - 2.15) * 10.929
        else:
            erg = menge / 10.929 + 2.15
    else:
        linksNachRechtsExponent = 1
        if not linksNachRechts:
            linksNachRechtsExponent = -1
        erg = menge * pow(einheiten.value, linksNachRechtsExponent)
    return erg

@staticmethod
def getKonvertierungseinheiten(einheiten:list):
    ke = Konvertierungseinheiten.GpL_MpL
    if len(einheiten) == 2 and einheiten[0] == "mg/dl" and einheiten[1] == "mmol/l":
        ke = Konvertierungseinheiten.MGpDL_MMpL
    elif len(einheiten) == 3 and einheiten[0] == "mg/dl" and einheiten[1] == "mmol/l" and einheiten[2] == "triglyceride":
        ke = Konvertierungseinheiten.TrigMGpDL_TrigMMpL
    elif einheiten[0] == "mg/dl" and einheiten[1] == "µmol/l":
        ke = Konvertierungseinheiten.MGpDL_MYMpL
    elif einheiten[0] == "mg/l" and einheiten[1] == "mg/dl":
        ke = Konvertierungseinheiten.MGpL_MGpDL
    elif einheiten[0] == "g/dl" and einheiten[1] == "g/l":
        ke = Konvertierungseinheiten.GpDL_GpL
    elif einheiten[0] == "%" and einheiten[1] == "mmol/mol":
        ke = Konvertierungseinheiten.PROZ_MMpM
    return ke
