import re, math

class RechenoperationException(Exception):
    def __init__(self, message:str):
        self.message = message

class Rechenoperation:
    moeglicheOperationen = [["^"], ["*", "/"], ["+", "-"]]
    moeglicheEinoperandenOperationen = {
        "sqrt" : math.sqrt,
        "ln" : math.log,
        "log10" : math.log10,
        "e" : math.e
    }
    patternZahl = r"^-?\d+([.,]\d+)?$"
    def __init__(self, formel:str):
        self.originalFormel = formel.strip().replace(" ", "").replace(",", ".")
        self.tempFormel = self.originalFormel
        self.operanden = []
        self.operationen = []

    def operationInMoeglicheOperationen(self, operation:str):
        """
        Prüft, ob sich eine Operation unter den möglichen Operationen befindet
        Parameter:
            operation:str
        Return:
            True oder False
        """ 
        moeglicheOperation = False
        for moeglicheOperationsGruppe in self.moeglicheOperationen:
            if operation in moeglicheOperationsGruppe:
                moeglicheOperation = True
                break
        return moeglicheOperation
    
    def getInnersteKlammerninhalte(self, formel:str):
        """
        Gibt die Klammerinhalte der untersten Ebene einer mathematischen Formel zurück z. B. (2+3) * (7 + (2 * sqrt5)) -> ['2 + 3', '2 * sqrt5']
        Paramater:
            formel:str 
        Return:
            Liste von Klammerinhalten
        """
        positionInFormel = 0
        tempInhalt = ""
        klammerInhalte = []
        oeffnendeKlammern = 0
        schliessendeKlammern = 0
        klammerOffen = False
        while positionInFormel < len(formel):
            if oeffnendeKlammern == schliessendeKlammern:
                tempInhalt = ""
            if formel[positionInFormel] =="(":
                klammerOffen = True
                oeffnendeKlammern += 1
                tempInhalt = ""
            elif formel[positionInFormel] ==")":
                klammerOffen = False
                schliessendeKlammern += 1
                if tempInhalt != "":
                    klammerInhalte.append(tempInhalt)
                tempInhalt = ""
            elif klammerOffen:
                tempInhalt += formel[positionInFormel]
            positionInFormel += 1
        if oeffnendeKlammern > schliessendeKlammern:
            raise RechenoperationException("Mehr öffnende (" + str(oeffnendeKlammern) + ") als schließende Klammern(" + str(schliessendeKlammern) + ") im Ausdruck " + formel)
        elif oeffnendeKlammern < schliessendeKlammern:
            raise RechenoperationException("Mehr schließende (" + str(schliessendeKlammern) + ") als öffnende Klammern(" + str(oeffnendeKlammern) + ") im Ausdruck " + formel)
        return klammerInhalte
    
    def __aktualisiereFormel(self, formel:str, dezimalstellenIntern:int):
        """
        Aktualisiert eine mathematische Formel in zwei Schritten:
        1. Ausführung von Einoperand-Operationen (sqrt, log...)
        2: Schrittweises Ausführen von Operationen in der Reihenfolge der Liste möglicher Operationen (Einhaltung der Punkt vor Strich-Regel)
        Parameter: 
            formel:str
            dezimalstellenIntern:int Anzahl der Dezimalstellen, mit denen intern gerechnet werden soll, -1 = unbegrenzt
        Return:
            formel mit entsprechenden Ergebnisersetzungen der jeweils durchgeführten Operationen
        """
        # Einoperand-Operationen ausführen
        operationDurchgefuehrt = True
        while operationDurchgefuehrt:
            positionInFormel = 0
            operationDurchgefuehrt = False
            while positionInFormel < len(formel):
                einoperandOperation = ""
                for moeglicheEinoperandenOperation in self.moeglicheEinoperandenOperationen:
                    if moeglicheEinoperandenOperation == formel[positionInFormel:positionInFormel + len(moeglicheEinoperandenOperation)]:
                        einoperandOperation = moeglicheEinoperandenOperation
                        break
                if einoperandOperation != "":
                    startposEinoperandOperation = positionInFormel
                    positionInFormel += len(einoperandOperation)
                    endposEinoperandOperation = positionInFormel
                    einoperand = ""
                    while positionInFormel < len(formel) and (re.match(r"^\d+([.,]?|[.,]\d+?)$", einoperand + formel[positionInFormel]) != None):
                        einoperand += formel[positionInFormel]
                        positionInFormel += 1
                    ergebnisformatierung = "{:." + str(dezimalstellenIntern) + "f}"
                    if einoperand != "":
                        if dezimalstellenIntern == -1:
                            einoperandErgebnis = str(self.moeglicheEinoperandenOperationen[einoperandOperation](float(einoperand)))
                        else:
                            einoperandErgebnis = ergebnisformatierung.format(self.moeglicheEinoperandenOperationen[einoperandOperation](float(einoperand)))
                    else:
                        if dezimalstellenIntern == -1:
                            einoperandErgebnis = str(self.moeglicheEinoperandenOperationen[einoperandOperation])  
                        else:
                            einoperandErgebnis = ergebnisformatierung.format(self.moeglicheEinoperandenOperationen[einoperandOperation])  
                    formel = formel[:startposEinoperandOperation] + einoperandErgebnis + formel[endposEinoperandOperation + len(einoperand):]
                    operationDurchgefuehrt = True
                positionInFormel += 1
        self.operanden = []
        self.operationen = []
        positionInFormel = 0
        tempOperand = ""
        while positionInFormel < len(formel):
            if self.operationInMoeglicheOperationen(formel[positionInFormel]):
                if positionInFormel > 0 and not self.operationInMoeglicheOperationen(formel[positionInFormel - 1]):
                    self.operationen.append(formel[positionInFormel])
                    if len(tempOperand) > 0:
                        if re.match(self.patternZahl, tempOperand) != None:
                            self.operanden.append(tempOperand)
                            tempOperand = ""
                        else:
                            raise RechenoperationException("Operand " + tempOperand + " ist keine Zahl")
                elif formel[positionInFormel] == "-": # negative Zahl
                    tempOperand = "-"
            else:
                tempOperand += formel[positionInFormel]
            positionInFormel += 1
        if len(tempOperand) > 0:
            if re.match(self.patternZahl, tempOperand) != None:
                self.operanden.append(tempOperand)
            else:
                raise RechenoperationException("Operand " + tempOperand + " ist keine Zahl")
        return formel

    def __getErgebnis(self, formel:str, dezimalstellenErgebnis:int, dezimalstellenIntern:int):
        """
        Gibt das Ergebnis einer mathematischen Formel zurück
        Parameter:
            formel:str
            dezimalstellenErgebnis:int Anzahl der Dezimalstellen, mit denen das Ergebnis ausgegeben werden soll, -1 = unbegrenzt
            dezimalstellenIntern:int Anzahl der Dezimalstellen, mit denen intern gerechnet werden soll, -1 = unbegrenzt
        Return:
            Ergebnis:str (String einer Float-Zahl)
        """
        for moeglicheOperationsGruppe in self.moeglicheOperationen:
            moeglicheOperationInFormel = True
            while moeglicheOperationInFormel:
                operationszaehler = 0
                for operation in self.operationen:
                    if operation in moeglicheOperationsGruppe:
                        tempOperand1 = float(self.operanden[operationszaehler])
                        tempOperand2 = float(self.operanden[operationszaehler + 1])
                        tempErgebnis = 0
                        if operation == "^":
                            tempErgebnis = pow(tempOperand1, tempOperand2)
                        elif operation == "*":
                            tempErgebnis = tempOperand1 * tempOperand2
                        elif operation == "/":
                            if tempOperand2 != 0:
                                tempErgebnis = tempOperand1 / tempOperand2
                            else:
                                raise RechenoperationException("Division durch null: " + str(tempOperand1).replace(".", ",") + " / " + str(tempOperand2).replace(".", ","))
                        elif operation == "+":
                            tempErgebnis = tempOperand1 + tempOperand2
                        elif operation == "-":
                            tempErgebnis = tempOperand1 - tempOperand2
                        ersetzungStartPos = 0
                        for i in range(operationszaehler):
                            ersetzungStartPos += len(self.operanden[i]) + len(self.operationen[i])
                        ersetzungLaenge = len(self.operanden[operationszaehler]) + len(self.operationen[operationszaehler]) + len(self.operanden[operationszaehler + 1])
                        if dezimalstellenIntern == -1:
                            tempErgebnisString = str(tempErgebnis)
                            if tempErgebnis == 0 and tempErgebnisString.startswith("-"):
                                tempErgebnisString = tempErgebnisString[1:]
                            formel = formel[:ersetzungStartPos] + tempErgebnisString + formel[ersetzungStartPos + ersetzungLaenge:]
                        else:
                            tempErgebnisString = ergebnisformatierung.format(tempErgebnis)
                            if tempErgebnis == 0 and tempErgebnisString.startswith("-"):
                                tempErgebnisString = tempErgebnisString[1:]
                            ergebnisformatierung = "{:." + str(dezimalstellenIntern) + "f}"
                            formel = formel[:ersetzungStartPos] + tempErgebnisString + formel[ersetzungStartPos + ersetzungLaenge:]
                        break
                    operationszaehler += 1   
                formel = self.__aktualisiereFormel(formel, dezimalstellenIntern) 
                moeglicheOperationInFormel = False
                for moeglicheOperation in moeglicheOperationsGruppe:
                    if moeglicheOperation in formel[1:]:
                        moeglicheOperationInFormel = True
                        break
        if dezimalstellenErgebnis != -1:
            ergebnisformatierung = "{:." + str(dezimalstellenErgebnis) + "f}"
            return ergebnisformatierung.format(float(formel))
        return formel
    
    def __call__(self, dezimalstellenErgebnis:int, dezimalstellenIntern:int):
        while "(" in self.tempFormel:
            for innerstenKlammerinhalt in self.getInnersteKlammerninhalte(self.tempFormel):
                ergebnis = self.__getErgebnis(innerstenKlammerinhalt, dezimalstellenIntern, dezimalstellenIntern)
                self.tempFormel = self.tempFormel.replace("(" + innerstenKlammerinhalt + ")", str(ergebnis))
        self.tempFormel = self.__aktualisiereFormel(self.tempFormel, dezimalstellenIntern)
        return self.__getErgebnis(self.tempFormel, dezimalstellenErgebnis, dezimalstellenIntern)
