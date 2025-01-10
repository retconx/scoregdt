import xml.etree.ElementTree as ElementTree
import os

class Score:
    @staticmethod
    def namenEindeutig(scoreverzeichnispfad:str):
        """
        Prüft, ob die Score-IDs eindeutig sind
        Parameter:
            Score-Verzeichnispfad:str
        Return:
            True oder False
        """
        eindeutig = True
        namen = []
        xmlDateien = os.listdir(scoreverzeichnispfad)
        for xmlDatei in xmlDateien:
            tree = ElementTree.parse(os.path.join(scoreverzeichnispfad, xmlDatei))
            root = tree.getroot()
            for scoreElement in root.findall("score"):
                name = str(scoreElement.get("name"))
                if name in namen:
                    eindeutig = False
                    break
                else:
                    namen.append(name)
            if not eindeutig:
                break
        return eindeutig

    @staticmethod
    def getFavoritenNamen(configPath:str):
        """
        Gibt die Favoriten-Scores zurück
        Parameter:
            Pfad der config.ini:str
        Return:
            Liste der Favoriten-Scores: list
        """
        favoritennamen = []
        tree = ElementTree.parse(os.path.join(configPath, "favoriten.xml"))
        favoritenElement = tree.getroot()
        for favoritElement in favoritenElement.findall("favorit"):
            favoritennamen.append(str(favoritElement.text))
        return favoritennamen
    
    @staticmethod
    def getScoreFavoritenRoot(configPath:str, scoreverzeichnispfad:str):
        """
        Gibt ein Root-Element der Favoriten-Scores zurück
        Parameter:
            Pfad der config.ini:str
            Score-Verzeichnispfad:str
        Return:
            Root-Element: ElementTree.Element
        """
        favoritenNamen = Score.getFavoritenNamen(configPath)
        rootElement = ElementTree.Element("root")
        xmlDateien = os.listdir(scoreverzeichnispfad)
        for xmlDatei in xmlDateien:
            tree = ElementTree.parse(os.path.join(scoreverzeichnispfad, xmlDatei))
            root = tree.getroot()
            for scoreElement in root.findall("score"):
                name = str(scoreElement.get("name"))
                if name in favoritenNamen:
                    rootElement.append(scoreElement)
        return rootElement
    
    @staticmethod
    def getGesamtRoot(scoreverzeichnispfad:str):
        """
        Gibt ein Root-Element aller Scores zurück
        Parameter:
            Score-Verzeichnispfad:str
        Return:
            Root-Element: ElementTree.Element
        """         
        rootElement = ElementTree.Element("root")
        xmlDateien = os.listdir(scoreverzeichnispfad)
        for xmlDatei in xmlDateien:
            tree = ElementTree.parse(os.path.join(scoreverzeichnispfad, xmlDatei))
            root = tree.getroot()
            for scoreElement in root.findall("score"):
                    rootElement.append(scoreElement)
        return rootElement
    
    @staticmethod
    def getScoreAnzahl(scoreverzeichnispfad:str):
        """
        Gibt die Anzahl der Scores zurück
        Parameter:
            Pfad der config.ini:str
        Return:
            Anzahl: int
        """
        return len(Score.getGesamtRoot(scoreverzeichnispfad).findall("score"))
    
    @staticmethod
    def getScoreXml(scoreverzeichnispfad:str, scoreName:str):
        """
        Gibt ein Score-Element zurück
        Parameter:
            Score-Verzeichnispfad:str
            Score-Name:str
        Return:
            Score-Element:ElementTree.Element oder None, falls Name nicht gefunden
        """
        scoreElement = None
        root = Score.getGesamtRoot(scoreverzeichnispfad)
        for tempScoreElement in root.findall("score"):
            name = str(tempScoreElement.get("name"))
            if name == scoreName:
                scoreElement = tempScoreElement
                break
        return scoreElement
    
    @staticmethod
    def getScoreNameAusGdtName(scoreverzeichnispfad:str, gdtName:str):
        """ 
        Gibt den Score-Namen zu einem passenden GDT-Namen zurück, falls dieser existiert
        Parameter: 
            scoreverzeichnispfad:str
            gdtName:str, zu suchender GDT-Name
        Return:
            Score-Name, falls für den Score ein GDT-Name existiert, andernfalls None
        """
        tempName = None
        root = Score.getGesamtRoot(scoreverzeichnispfad)
        for tempScoreElement in root.findall("score"):
            tempGdtName = ""
            if tempScoreElement.get("gdtname") != None:
                tempGdtName = str(tempScoreElement.get("gdtname"))
            if tempGdtName == gdtName:
                tempName = str(tempScoreElement.get("name"))
                break
        return tempName            

