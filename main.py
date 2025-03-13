import sys, configparser, os, datetime, shutil, logger, re, atexit, subprocess
import xml.etree.ElementTree as ElementTree
import requests
## Nur mit Lizenz
import gdttoolsL
## /Nur mit Lizenz
import gdt, gdtzeile, class_part, class_widgets, class_score, farbe
import dialogUeberScoreGdt, dialogEinstellungenAllgemein, dialogEinstellungenGdt, dialogEinstellungenBenutzer, dialogEinstellungenLanrLizenzschluessel, dialogEula, dialogEinstellungenImportExport, dialogScoreAuswahl, dialogEinstellungenFavoriten
import class_trends, dialogTrendanzeige
import class_enums, class_score, class_Rechenoperation, scorepdf, molGrammConvert
from PySide6.QtCore import Qt, QTranslator, QLibraryInfo, QDate, QTime
from PySide6.QtGui import QFont, QAction, QIcon, QDesktopServices, QPixmap, QPalette, QClipboard
from PySide6.QtWidgets import (
    QApplication,
    QSizePolicy,
    QMainWindow,
    QVBoxLayout,
    QGroupBox,
    QFrame,
    QCheckBox,
    QHBoxLayout,
    QGridLayout,
    QWidget,
    QLabel, 
    QLineEdit,
    QDateEdit,
    QMessageBox,
    QPushButton,
    QComboBox,
    QButtonGroup,
    QScrollArea
)

@staticmethod
def getAktuellesAlterInJahren(gebdat:datetime.date):
    heute = datetime.date.today()
    gebdatDesesJahr = datetime.date(heute.year, gebdat.month, gebdat.day)
    alterInJahren = heute.year - gebdat.year
    if (heute - gebdatDesesJahr).days < 0:
        alterInJahren -= 1
    return alterInJahren

# Atomgewichte
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

class ScoreGdtException(Exception):
    def __init__(self, meldung):
        self.meldung = meldung
    def __str__(self):
        return "ScoreGDT-Fehler: " + self.meldung

basedir = os.path.dirname(__file__)

def versionVeraltet(versionAktuell:str, versionVergleich:str):
    """
    Vergleicht zwei Versionen im Format x.x.x
    Parameter:
        versionAktuell:str
        versionVergleich:str
    Rückgabe:
        True, wenn versionAktuell veraltet
    """
    versionVeraltet= False
    hunderterBase = int(versionVergleich.split(".")[0])
    zehnerBase = int(versionVergleich.split(".")[1])
    einserBase = int(versionVergleich.split(".")[2])
    hunderter = int(versionAktuell.split(".")[0])
    zehner = int(versionAktuell.split(".")[1])
    einser = int(versionAktuell.split(".")[2])
    if hunderterBase > hunderter:
        versionVeraltet = True
    elif hunderterBase == hunderter:
        if zehnerBase >zehner:
            versionVeraltet = True
        elif zehnerBase == zehner:
            if einserBase > einser:
                versionVeraltet = True
    return versionVeraltet

# Sicherstellen, dass Icon in Windows angezeigt wird
try:
    from ctypes import windll # type: ignore
    mayappid = "gdttools.scoregdt"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(mayappid)
except ImportError:
    pass

class MainWindow(QMainWindow):

    resizeVollzogen = False

    # Mainwindow zentrieren
    def resizeEvent(self, e):
        if not self.resizeVollzogen:
            ag = self.screen().availableGeometry()
            screenBreite = ag.size().width()
            screenHoehe = ag.size().height()
            mainwindowBreite = e.size().width()
            mainwindowHoehe = e.size().height()
            left = int(screenBreite / 2 - mainwindowBreite / 2)
            top = int(screenHoehe / 2 - mainwindowHoehe / 2)
            self.setGeometry(left, top, mainwindowBreite, mainwindowHoehe)
            self.resizeVollzogen = True

    def __init__(self):
        super().__init__()
        self.maxBenutzeranzahl = 20

        # config.ini lesen
        ersterStart = False
        updateSafePath = ""
        if sys.platform == "win32":
            logger.logger.info("Plattform: win32")
            updateSafePath = os.path.expanduser("~\\appdata\\local\\scoregdt")
        else:
            logger.logger.info("Plattform: nicht win32")
            updateSafePath = os.path.expanduser("~/.config/scoregdt")
        self.configPath = updateSafePath
        self.configIni = configparser.ConfigParser()
        if os.path.exists(os.path.join(updateSafePath, "config.ini")):
            logger.logger.info("config.ini in " + updateSafePath + " exisitert")
            self.configPath = updateSafePath
        elif os.path.exists(os.path.join(basedir, "config.ini")):
            logger.logger.info("config.ini in " + updateSafePath + " exisitert nicht")
            try:
                if (not os.path.exists(updateSafePath)):
                    logger.logger.info(updateSafePath + " exisitert nicht")
                    os.makedirs(updateSafePath, 0o777)
                    logger.logger.info(updateSafePath + "erzeugt")
                shutil.copy(os.path.join(basedir, "config.ini"), updateSafePath)
                logger.logger.info("config.ini von " + basedir + " nach " + updateSafePath + " kopiert")
                self.configPath = updateSafePath
                ersterStart = True
            except:
                logger.logger.error("Problem beim Kopieren der config.ini von " + basedir + " nach " + updateSafePath)
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Problem beim Kopieren der Konfigurationsdatei. ScoreGDT wird mit Standardeinstellungen gestartet.", QMessageBox.StandardButton.Ok)
                mb.exec()
                self.configPath = basedir
        else:
            logger.logger.critical("config.ini fehlt")
            mb = QMessageBox(QMessageBox.Icon.Critical, "Hinweis von ScoreGDT", "Die Konfigurationsdatei config.ini fehlt. ScoreGDT kann nicht gestartet werden.", QMessageBox.StandardButton.Ok)
            mb.exec()
            sys.exit()
        self.configIni.read(os.path.join(self.configPath, "config.ini"), encoding="utf-8")
        self.version = self.configIni["Allgemein"]["version"]
        self.eulagelesen = self.configIni["Allgemein"]["eulagelesen"] == "True"
        self.bereichsgrenzenerzwingen = self.configIni["Allgemein"]["bereichsgrenzenerzwingen"] == "True"
        self.gdtImportVerzeichnis = self.configIni["GDT"]["gdtimportverzeichnis"]
        self.gdtExportVerzeichnis = self.configIni["GDT"]["gdtexportverzeichnis"]
        self.kuerzelscoregdt = self.configIni["GDT"]["kuerzelscoregdt"]
        self.kuerzelpraxisedv = self.configIni["GDT"]["kuerzelpraxisedv"]
        self.benutzernamenListe = self.configIni["Benutzer"]["namen"].split("::")
        self.benutzerkuerzelListe = self.configIni["Benutzer"]["kuerzel"].split("::")
        self.aktuelleBenuztzernummer = int(self.configIni["Benutzer"]["letzter"])
        self.scoresPfad = os.path.join(basedir, "scores")

        ## Nachträglich hinzufefügte Options
        # 1.1.1
        self.standardscore = ""
        if self.configIni.has_option("Allgemein", "standardscore"):
            self.standardscore = self.configIni["Allgemein"]["standardscore"]
        # 1.11.1
        self.neueScores = False
        self.scoreanzahl = 0
        if self.configIni.has_option("Allgemein", "scoreanzahl"):
            self.scoreanzahl = int(self.configIni["Allgemein"]["scoreanzahl"])
        # 1.12.0
        self.autoupdate = True
        if self.configIni.has_option("Allgemein", "autoupdate"):
            self.autoupdate = self.configIni["Allgemein"]["autoupdate"] == "True"
        # 1.14.1
        self.updaterpfad = ""
        if self.configIni.has_option("Allgemein", "updaterpfad"):
            self.updaterpfad = self.configIni["Allgemein"]["updaterpfad"]
        # 1.16.0
        self.pdferzeugen = False
        if self.configIni.has_option("Allgemein", "pdferzeugen"):
            self.pdferzeugen = self.configIni["Allgemein"]["pdferzeugen"] == "True"
        self.einrichtunguebernehmen = False
        if self.configIni.has_option("Allgemein", "einrichtunguebernehmen"):
            self.einrichtunguebernehmen = self.configIni["Allgemein"]["einrichtunguebernehmen"] == "True"
        self.einrichtungsname = ""
        if self.configIni.has_option("Allgemein", "einrichtungsname"):
            self.einrichtungsname = self.configIni["Allgemein"]["einrichtungsname"]
        # 1.22.0 -> wieder entfernt -> 1.21.3
        # self.archivierungspfad = ""
        # if self.configIni.has_option("Allgemein", "archivierungspfad"):
            # self.updaterpfad = self.configIni["Allgemein"]["archivierungspfad"]
        # 1.21.3
        if self.configIni.has_option("Allgemein", "archivierungspfad"):
            self.configIni.remove_option("Allgemein", "archivierungspfad")
        # 1.22.0
        self.trendverzeichnis = ""
        if self.configIni.has_option("Allgemein", "trendverzeichnis"):
            self.trendverzeichnis = self.configIni["Allgemein"]["trendverzeichnis"]
        ## /Nachträglich hinzufefügte Options

        z = self.configIni["GDT"]["zeichensatz"]
        self.zeichensatz = gdt.GdtZeichensatz.IBM_CP437
        if z == "1":
            self.zeichensatz = gdt.GdtZeichensatz.BIT_7
        elif z == "3":
            self.zeichensatz = gdt.GdtZeichensatz.ANSI_CP1252
        self.lanr = self.configIni["Erweiterungen"]["lanr"]
        self.lizenzschluessel = self.configIni["Erweiterungen"]["lizenzschluessel"]

        ## Nur mit Lizenz
        # Prüfen, ob Lizenzschlüssel unverschlüsselt
        if len(self.lizenzschluessel) == 29:
            logger.logger.info("Lizenzschlüssel unverschlüsselt")
            self.configIni["Erweiterungen"]["lizenzschluessel"] = gdttoolsL.GdtToolsLizenzschluessel.krypt(self.lizenzschluessel)
            with open(os.path.join(self.configPath, "config.ini"), "w", encoding="utf-8") as configfile:
                    self.configIni.write(configfile)
        else:
            self.lizenzschluessel = gdttoolsL.GdtToolsLizenzschluessel.dekrypt(self.lizenzschluessel)
        ## /Nur mit Lizenz

        # Prüfen, ob EULA gelesen
        if not self.eulagelesen:
            de = dialogEula.Eula()
            de.exec()
            if de.checkBoxZustimmung.isChecked():
                self.eulagelesen = True
                self.configIni["Allgemein"]["eulagelesen"] = "True"
                with open(os.path.join(self.configPath, "config.ini"), "w", encoding="utf-8") as configfile:
                    self.configIni.write(configfile)
                logger.logger.info("EULA zugestimmt")
            else:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von ScoreGDT", "Ohne Zustimmung der Lizenzvereinbarung kann ScoreGDT nicht gestartet werden.", QMessageBox.StandardButton.Ok)
                mb.exec()
                sys.exit()

        ## favoriten.xml anlegen (ab 1.8.0)
        try:
            if not os.path.exists(os.path.join(self.configPath, "favoriten.xml")):
                favoritenElement = ElementTree.Element("favoriten")
                tree = ElementTree.ElementTree(favoritenElement)
                gesamtRoot = class_score.Score.getGesamtRoot(self.scoresPfad)
                for scoreElement in gesamtRoot.findall("score"):
                    favoritElement = ElementTree.Element("favorit")
                    favoritElement.text = str(scoreElement.get("name"))
                    favoritenElement.append(favoritElement)
                ElementTree.indent(tree)
                tree.write(os.path.join(self.configPath, "favoriten.xml"), "utf-8", True)
                logger.logger.info(os.path.join(self.configPath, "favoriten.xml") + " erstellt")
        except:
            pass
        ## /favoriten.xml anlegen

        # Score-Favoriten auslesen
        if not class_score.Score.namenEindeutig(self.scoresPfad):
            logger.logger.warning("Score-Namen nicht eindeutig")
            logger.logger.error("Fehler beim Vergeben eindeutiger Score-IDs (Scores-Pfad: " + self.scoresPfad + ")")
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Die Score-Namen sind nicht eindeutig.", QMessageBox.StandardButton.Ok)
            mb.exec()
        try:
            self.root = class_score.Score.getScoreFavoritenRoot(self.configPath, self.scoresPfad)
            bisherigeScoreAnzahl = self.scoreanzahl
            self.scoreanzahl = class_score.Score.getScoreAnzahl(self.scoresPfad)
            if bisherigeScoreAnzahl < self.scoreanzahl:
                self.neueScores = True
                self.configIni["Allgemein"]["scoreanzahl"] = str(self.scoreanzahl)
                with open(os.path.join(self.configPath, "config.ini"), "w", encoding="utf-8") as configfile:
                    self.configIni.write(configfile)
        except Exception as e:
            logger.logger.error("Fehler beim Laden der Scores (Scorepfad: " + self.scoresPfad + ")")
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Fehler beim Laden der Scores.\nScoreGDT wird beendet.", QMessageBox.StandardButton.Ok)
            mb.exec()
            sys.exit()
        
        # Grundeinstellungen bei erstem Start
        if ersterStart:
            logger.logger.info("Erster Start")
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von ScoreGDT", "Vermutlich starten Sie ScoreGDT das erste Mal auf diesem PC.\nMöchten Sie jetzt die Grundeinstellungen vornehmen?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.Yes)
            if mb.exec() == QMessageBox.StandardButton.Yes:
                ## Nur mit Lizenz
                self.einstellungenLanrLizenzschluessel(False, False)
                ## /Nur mit Lizenz
                self.einstellungenGdt(False, False)
                self.einstellungenBenutzer(False, False)
                self.einstellungenAllgemein(False, False)
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Die Ersteinrichtung ist abgeschlossen. ScoreGDT wird beendet.", QMessageBox.StandardButton.Ok)
                mb.exec()
                sys.exit()

        # Version vergleichen und gegebenenfalls aktualisieren
        configIniBase = configparser.ConfigParser()
        try:
            configIniBase.read(os.path.join(basedir, "config.ini"), encoding="utf-8")
            if versionVeraltet(self.version, configIniBase["Allgemein"]["version"]):
                # Version aktualisieren
                self.configIni["Allgemein"]["version"] = configIniBase["Allgemein"]["version"]
                self.configIni["Allgemein"]["releasedatum"] = configIniBase["Allgemein"]["releasedatum"] 
                ## config.ini aktualisieren
                # 1.0.4 -> 1.0.5: ["Allgemein"]["standardscore"] hinzufügen
                if not self.configIni.has_option("Allgemein", "standardscore"):
                    self.configIni["Allgemein"]["standardscore"] = ""
                # 1.11.0 -> 1.11.1
                if not self.configIni.has_option("Allgemein", "scoreanzahl"):
                    self.configIni["Allgemein"]["scoreanzahl"] = str(self.scoreanzahl)
                # 1.11.0 -> 1.12.0
                if not self.configIni.has_option("Allgemein", "autoupdate"):
                    self.configIni["Allgemein"]["autoupdate"] = "True"
                # 1.14.0 -> 1.14.1
                if not self.configIni.has_option("Allgemein", "updaterpfad"):
                    self.configIni["Allgemein"]["updaterpfad"] = ""
                # 1.15.2 -> 1.16.0
                if not self.configIni.has_option("Allgemein", "pdferzeugen"):
                    self.configIni["Allgemein"]["pdferzeugen"] = "False"
                if not self.configIni.has_option("Allgemein", "einrichtungsname"):
                    self.configIni["Allgemein"]["einrichtungsname"] = ""
                if not self.configIni.has_option("Allgemein", "einrichtunguebernehmen"):
                    self.configIni["Allgemein"]["einrichtunguebernehmen"] = "False"
                # 1.21.0 -> 1.22.0 -> wieder entfernt -> 1.21.3
                # if not self.configIni.has_option("Allgemein", "archivierungspfad"):
                #     self.configIni["Allgemein"]["archivierungspfad"] = ""
                # 1.21.4 -> 1.22.0
                if not self.configIni.has_option("Allgemein", "trendverzeichnis"):
                    self.configIni["Allgemein"]["trendverzeichnis"] = ""
                ## /config.ini aktualisieren
                ## scores.xml löschen (ab 1.8.0)
                try:
                    os.unlink(os.path.join(self.scoresPfad, "scores.xml"))
                    logger.logger.info(os.path.join(self.scoresPfad, "scores.xml") + " gelöscht")
                except:
                    pass
                ## /scores.xml löschen

                with open(os.path.join(self.configPath, "config.ini"), "w", encoding="utf-8") as configfile:
                    self.configIni.write(configfile)
                self.version = self.configIni["Allgemein"]["version"]
                logger.logger.info("Version auf " + self.version + " aktualisiert")
                # Prüfen, ob EULA gelesen
                de = dialogEula.Eula(self.version)
                de.exec()
                self.eulagelesen = de.checkBoxZustimmung.isChecked()
                self.configIni["Allgemein"]["eulagelesen"] = str(self.eulagelesen)
                with open(os.path.join(self.configPath, "config.ini"), "w", encoding="utf-8") as configfile:
                    self.configIni.write(configfile)
                if self.eulagelesen:
                    logger.logger.info("EULA zugestimmt")
                else:
                    logger.logger.info("EULA nicht zugestimmt")
                    mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von ScoreGDT", "Ohne  Zustimmung zur Lizenzvereinbarung kann ScoreGDT nicht gestartet werden.", QMessageBox.StandardButton.Ok)
                    mb.exec()
                    sys.exit()
        except SystemExit:
            sys.exit()
        except:
            logger.logger.error("Problem beim Aktualisieren auf Version " + configIniBase["Allgemein"]["version"])
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Problem beim Aktualisieren auf Version " + configIniBase["Allgemein"]["version"], QMessageBox.StandardButton.Ok)
            mb.exec()

        self.addOnsFreigeschaltet = True

        ## Nur mit Lizenz
        # Pseudo-Lizenz?
        self.pseudoLizenzId = ""
        rePatId = r"^patid\d+$"
        for arg in sys.argv:
            if re.match(rePatId, arg) != None:
                logger.logger.info("Pseudo-Lizenz mit id " + arg[5:])
                self.pseudoLizenzId = arg[5:]

        # Add-Ons freigeschaltet?
        self.addOnsFreigeschaltet = gdttoolsL.GdtToolsLizenzschluessel.lizenzErteilt(self.lizenzschluessel, self.lanr, gdttoolsL.SoftwareId.SCOREGDT) or gdttoolsL.GdtToolsLizenzschluessel.lizenzErteilt(self.lizenzschluessel, self.lanr, gdttoolsL.SoftwareId.SCOREGDTPSEUDO) and self.pseudoLizenzId != ""
        if self.lizenzschluessel != "" and gdttoolsL.GdtToolsLizenzschluessel.getSoftwareId(self.lizenzschluessel) == gdttoolsL.SoftwareId.SCOREGDTPSEUDO and self.pseudoLizenzId == "":
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Bei Verwendung einer Pseudolizenz muss ScoreGDT mit einer Patienten-Id als Startargument im Format \"patid<Pat.-Id>\" ausgeführt werden.", QMessageBox.StandardButton.Ok)
            mb.exec() 
        ## /Nur mit Lizenz
        
        jahr = datetime.datetime.now().year
        copyrightJahre = "2024"
        if jahr > 2024:
            copyrightJahre = "2024-" + str(jahr)
        self.setWindowTitle("ScoreGDT V" + self.version + " (\u00a9 Fabian Treusch - GDT-Tools " + copyrightJahre + ")")
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.fontBoldGross = QFont()
        self.fontBoldGross.setBold(True)
        self.fontBoldGross.setPixelSize(16)
        self.fontGross = QFont()
        self.fontGross.setPixelSize(16)
                
        # GDT-Datei laden
        gd = gdt.GdtDatei()
        self.patId = "-"
        self.name = "-"
        self.geburtsdatum =  datetime.date.today().strftime("%d.%m.%Y")
        self.geschlecht = "1"
        mbErg = QMessageBox.StandardButton.Yes
        gdtLadeFehler = False
        try:
            # Prüfen, ob PVS-GDT-ID eingetragen
            senderId = self.configIni["GDT"]["idpraxisedv"]
            if senderId == "":
                senderId = None
            gd.laden(os.path.join(self.gdtImportVerzeichnis, self.kuerzelscoregdt + self.kuerzelpraxisedv + ".gdt"), self.zeichensatz, senderId)
            self.patId = str(gd.getInhalt("3000"))
            self.name = str(gd.getInhalt("3102")) + " " + str(gd.getInhalt("3101"))
            logger.logger.info("PatientIn " + self.name + " (ID: " + self.patId + ") geladen")
            ## Nur mit Lizenz
            if self.pseudoLizenzId != "":
                self.patId = self.pseudoLizenzId
                logger.logger.info("PatId wegen Pseudolizenz auf " + self.pseudoLizenzId + " gesetzt")
            ## /Nur mit Lizenz
            self.geburtsdatum = str(gd.getInhalt("3103"))[0:2] + "." + str(gd.getInhalt("3103"))[2:4] + "." + str(gd.getInhalt("3103"))[4:8]
            self.geschlecht = str(gd.getInhalt("3110")) # 1=männlich, 2=weiblich
            logger.logger.info("Geschlecht aus PVS-GDT (3110): " + self.geschlecht)
        except (IOError, gdtzeile.GdtFehlerException) as e:
            logger.logger.warning("Fehler beim Laden der GDT-Datei: " + str(e))
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von ScoreGDT", "Fehler beim Laden der GDT-Datei:\n" + str(e) + "\n\nDieser Fehler hat in der Regel eine der folgenden Ursachen:\n- Die im PVS und in ScoreGDT konfigurierten GDT-Austauschverzeichnisse stimmen nicht überein.\n- ScoreGDT wurde nicht aus dem PVS heraus gestartet, so dass keine vom PVS erzeugte GDT-Datei gefunden werden konnte.\n\nSoll ScoreGDT dennoch geöffnet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            mb.setDefaultButton(QMessageBox.StandardButton.No)
            gdtLadeFehler = True
            mbErg = mb.exec()
        if mbErg == QMessageBox.StandardButton.Yes:
            self.widget = QWidget()

            # Updateprüfung auf Github
            if self.autoupdate:
                try:
                    self.updatePruefung(meldungNurWennUpdateVerfuegbar=True)
                except Exception as e:
                    mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Updateprüfung nicht möglich.\nBitte überprüfen Sie Ihre Internetverbindung." + str(e), QMessageBox.StandardButton.Ok)
                    mb.exec()
                    logger.logger.warning("Updateprüfung nicht möglich: " + str(e))

            # Mitteilung, dass neue Scores
            if self.neueScores:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von ScoreGDT", "Neue Scores stehen zur Verfügung. Zur Nutzung müssen diese Aktiviert werden.\nSoll die Score-Verwaltung angezeigt werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    self.scoreFavoritenVerwalten(False)

            if self.root != None:
                reStartScore = r"^stsc:.+$"
                self.scoreRoot = self.root.find("score")
                if not gdtLadeFehler:
                    scoreAlsStartargument = False
                    for arg in sys.argv:
                        if re.match(reStartScore, arg) != None: # Score als Startargument
                            scoreName = class_score.Score.getScoreNameAusGdtName(self.scoresPfad, str(arg[5:]).replace("_", " ").replace("{", "(").replace("}", ")"))
                            if scoreName == None:
                                scoreName = str(arg[5:].replace("_", " ").replace("{", "(").replace("}", ")"))
                            self.scoreRoot = class_score.Score.getScoreXml(self.scoresPfad, scoreName)
                            if self.scoreRoot != None:
                                scoreAlsStartargument = True
                    auswahlOk = False
                    if not scoreAlsStartargument:
                        ds = dialogScoreAuswahl.ScoreAuswahl(self.root, self.standardscore, self.configPath, self.patId)
                        auswahlOk = ds.exec() == 1
                    if scoreAlsStartargument or auswahlOk:
                        if scoreAlsStartargument:
                            logger.logger.info("Score " + sys.argv[1] + " als Startargument")
                        elif not ds.buttonTrendAusdruck.isChecked(): # Scoreberechung
                            if not scoreAlsStartargument:
                                self.scoreRoot = class_score.Score.getScoreXml(self.scoresPfad, ds.aktuellGewaehlterScore)
                                logger.logger.info("Score " + ds.aktuellGewaehlterScore + " ausgewählt")
                        else: # Trendanzeige
                            ausgewaehlteTrendScores = [rb.text() for rb in ds.radioButtonsScore if rb.isChecked()]
                            try:
                                xmlTree = class_trends.getTrends(os.path.join(self.trendverzeichnis, self.patId))
                                ausgewaehlteTestXmls = [t for t in xmlTree.findall("test") if str(t.get("name")) in ausgewaehlteTrendScores or (ds.checkBoxGeriGDT.isChecked() and str(t.get("tool")) == class_trends.GdtTool.GERIGDT.value)]
                                ausgewaehlteTests = [class_trends.getTestAusXml(t) for t in ausgewaehlteTestXmls]
                                ausgewaehlteTests = sorted(ausgewaehlteTests, key=lambda t:t.getName())
                                dt = dialogTrendanzeige.Trendanzeige(ausgewaehlteTests)
                                if dt.exec() == 1:
                                    heute = datetime.datetime.now()
                                    # GDT-Datei erzeugen
                                    sh = gdt.SatzHeader(gdt.Satzart.DATEN_EINER_UNTERSUCHUNG_UEBERMITTELN_6310, self.configIni["GDT"]["idpraxisedv"], self.configIni["GDT"]["idscoregdt"], self.zeichensatz, "2.10", "Fabian Treusch - GDT-Tools", "ScoreGDT", self.version, self.patId)
                                    gd = gdt.GdtDatei()
                                    logger.logger.info("GdtDatei-Instanz für Trendausdruck erzeugt")
                                    gd.erzeugeGdtDatei(sh.getSatzheader())
                                    logger.logger.info("Satzheader 6310 erzeugt")
                                    gd.addZeile("6200", heute.strftime("%d%m%Y"))
                                    gd.addZeile("6201", heute.strftime("%H%M%S"))
                                    gd.addZeile("8402", "ALLG00")
                                    gd.addZeile("6302", "trendpdf")
                                    gd.addZeile("6303", "pdf")
                                    gd.addZeile("6304", "Score-Trend")
                                    gd.addZeile("6305", os.path.join(basedir, "pdf/trend_temp.pdf"))
                                    # PDF erzeugen
                                    # Kopf
                                    if len(ausgewaehlteTests) > 1:
                                        trendPdf = scorepdf.scorepdf("P", "mm", "A4", "Medizinische Score-Trends")
                                    else:
                                        trendPdf = scorepdf.scorepdf("P", "mm", "A4", "Medizinischer Score-Trend")
                                    logger.logger.info("FPDF-Instanz erzeugt")
                                    trendPdf.set_fill_color(240,240,240)
                                    trendPdf.add_page()
                                    trendPdf.set_font("dejavu", "", 14)
                                    trendPdf.cell(0, 10, "von " + self.name + " (* " + self.geburtsdatum + ")", align="C", new_x="LMARGIN", new_y="NEXT")
                                    trendPdf.set_font("dejavu", "", 10)
                                    einrichtung = ""
                                    if self.einrichtunguebernehmen:
                                        einrichtung = " von " + self.einrichtungsname
                                    trendPdf.cell(0, 10, "Erstellt am " + heute.strftime("%d.%m.%Y") + einrichtung, align="C", new_x="LMARGIN", new_y="NEXT")
                                    # Trends
                                    trendPdf.set_font_size(12)
                                    gruppen = []
                                    for test in ausgewaehlteTests:
                                        if test.getGruppe() not in gruppen:
                                            gruppen.append(test.getGruppe())
                                    gruppen.sort()
                                    for gruppe in gruppen:
                                        trendPdf.set_font("dejavu", "B", 12)
                                        trendPdf.cell(0, 10, gruppe, fill=True, new_x="LMARGIN", new_y="NEXT")
                                        for test in ausgewaehlteTests:
                                            if test.getGruppe() == gruppe:
                                                trendPdf.set_font("dejavu", "B", 11)
                                                trendPdf.cell(0, 10, test.getName(), new_x="LMARGIN", new_y="NEXT", border="B")
                                                trendPdf.set_font("dejavu", "", 11)
                                                for trend in test.getLetzteTrends():
                                                    trendPdf.multi_cell(30, 10, trend.getTrend()["datum"].strftime("%d.%m.%Y"), new_y="LAST")
                                                    trendPdf.multi_cell(45, 10, trend.getTrend()["ergebnis"], new_y="LAST")
                                                    trendPdf.multi_cell(0, 10, trend.getTrend()["interpretation"], new_x="LMARGIN", new_y="NEXT")
                                                trendPdf.cell(0, 4, "", new_x="LMARGIN", new_y="NEXT")
                                    trendPdf.set_y(-30)
                                    trendPdf.set_font("dejavu", "I", 10)
                                    trendPdf.cell(0, 10, "Generiert von ScoreGDT V" + self.version + " (\u00a9 GDT-Tools " + str(datetime.date.today().year) + ")", align="R")
                                    trendPdf.output(os.path.join(basedir, "pdf/trend_temp.pdf"))
                                    # GDT-Datei exportieren
                                    if not gd.speichern(os.path.join(self.gdtExportVerzeichnis, self.kuerzelpraxisedv + self.kuerzelscoregdt + ".gdt"), self.zeichensatz):
                                        logger.logger.error("Fehler bei GDT-Dateiexport nach " + self.gdtExportVerzeichnis + "/" + self.kuerzelpraxisedv + self.kuerzelscoregdt + ".gdt")
                                        mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "GDT-Export nicht möglich.\nBitte überprüfen Sie die Angabe des Exportverzeichnisses.\nScoreGDT wird beendet.", QMessageBox.StandardButton.Ok)
                                        mb.exec()
                            except class_trends.XmlPfadExistiertNichtError as e:
                                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Problem beim Laden der Trenddaten: " + str(e), QMessageBox.StandardButton.Ok)
                                mb.exec()
                            sys.exit()
                    else:
                        logger.logger.info("Kein Score ausgewählt")
                        sys.exit()
                if self.scoreRoot != None:
                    self.parts = []
                    self.widgets = []
                    self.einheitToggles = {}
                    itemsUndWerte = []
                    for partElement in self.scoreRoot.findall("part"):
                        partId = str(partElement.get("id"))
                        partTyp = class_part.PartTyp(str(partElement.get("typ")))
                        partTitel = str(partElement.get("titel"))
                        partErklaerung =str(partElement.get("erklaerung"))
                        partZeile = int(str(partElement.get("zeile")))
                        partSpalte = int(str(partElement.get("spalte")))
                        geschlechtpruefung = partElement.get("geschlechtpruefung") != None and str(partElement.get("geschlechtpruefung")) == "True"
                        hintergrundbild = ""
                        if partElement.get("hintergrundbild") != None:
                            hintergrundbild = str(partElement.get("hintergrundbild"))
                        self.parts.append(class_part.Part(partId, partTyp, partTitel, partErklaerung, partZeile, partSpalte, geschlechtpruefung, hintergrundbild, self.scoreRoot))
                        for widgetElement in partElement.findall("widget"):
                            widgetId = str(widgetElement.get("id"))
                            widgetTyp = str(widgetElement.get("typ"))
                            widgetTitel = str(widgetElement.get("titel"))
                            alterspruefung = False
                            if widgetElement.get("alterspruefung") != None:
                                alterspruefung = str(widgetElement.get("alterspruefung")) == "True"
                            groessepruefung = False
                            if widgetElement.get("groessepruefung") != None:
                                groessepruefung = str(widgetElement.get("groessepruefung")) == "True"
                            gewichtpruefung = False
                            if widgetElement.get("gewichtpruefung") != None:
                                gewichtpruefung = str(widgetElement.get("gewichtpruefung")) == "True"
                            widgetErklaerung = ""
                            if widgetElement.find("erklaerung") != None:
                                widgetErklaerung = str(widgetElement.find("erklaerung").text) # type: ignore
                            widgetEinheit = ""
                            if widgetElement.find("einheit") != None:
                                widgetEinheit = str(widgetElement.find("einheit").text) # type: ignore
                            if widgetTyp == class_widgets.WidgetTyp.COMBOBOX.value:
                                itemsElement = widgetElement.find("items")
                                itemsUndWerte.clear()
                                i = 0
                                for itemElement in itemsElement.findall("item"): # type: ignore
                                    itemWert = str(itemElement.get("wert"))
                                    itemText = str(itemElement.text)
                                    itemsUndWerte.append((itemText, itemWert))
                                    defaultindex = 0
                                    if itemElement.get("defaultindex") != None:
                                        if str(itemElement.get("defaultindex")) == "True":
                                            defaultindex = i
                                    i += 1
                                self.widgets.append(class_widgets.ComboBox(widgetId, partId, widgetTitel, widgetErklaerung, widgetEinheit, itemsUndWerte.copy(), defaultindex, alterspruefung, groessepruefung, gewichtpruefung))
                                logger.logger.info("Combobox angelegt (Part-ID: " + partId + ", Widget-ID: " + widgetId + ") angelegt")
                            elif widgetTyp == class_widgets.WidgetTyp.CHECKBOX.value:
                                buttongroup = ""
                                if widgetElement.get("buttongroup") != None:
                                    buttongroup = str(widgetElement.get("buttongroup"))
                                checked = str(widgetElement.get("checked")) == "True"
                                altersregel = ""
                                if widgetElement.get("altersregel") != None:
                                    altersregel = str(widgetElement.get("altersregel"))
                                geschlechtpruefung = str(widgetElement.get("geschlechtpruefung")) == "True"
                                wertElement = widgetElement.find("wert")
                                wert = str(wertElement.text) # type: ignore
                                self.widgets.append(class_widgets.CheckBox(widgetId, partId, buttongroup, widgetTitel, widgetErklaerung, widgetEinheit, wert, checked, alterspruefung, altersregel, geschlechtpruefung, groessepruefung, gewichtpruefung))
                                logger.logger.info("Checkbox angelegt (Part-ID: " + partId + ", Widget-ID: " + widgetId + ") angelegt")
                            elif widgetTyp == class_widgets.WidgetTyp.LINEEDIT.value:
                                regexPattern = str(widgetElement.find("regex").text) # type: ignore
                                defaultWert = ""
                                if widgetElement.get("defaultwert") != None:
                                    defaultWert = str(widgetElement.get("defaultwert"))
                                self.widgets.append(class_widgets.LineEdit(widgetId, partId, widgetTitel, widgetErklaerung, widgetEinheit, regexPattern, alterspruefung, defaultWert, groessepruefung, gewichtpruefung))
                                logger.logger.info("Lineedit angelegt (Part-ID: " + partId + ", Widget-ID: " + widgetId + ") angelegt")
                                # Zahlengrenzen festlegen
                                zahlengrenzen = []
                                for zahlengrenzeElement in widgetElement.findall("zahlengrenze"):
                                    zahlengrenze = float(str(zahlengrenzeElement.text))
                                    zahlengrenzen.append(zahlengrenze)
                                    regelart = str(zahlengrenzeElement.get("regelart"))
                                    self.widgets[len(self.widgets) - 1].addZahlengrenze(zahlengrenze, class_enums.Regelarten(regelart))
                                # Relativgrenzen festlegen
                                for relativgrenzeElement in widgetElement.findall("relativgrenze"):
                                    id = str(relativgrenzeElement.text)
                                    regelart = str(relativgrenzeElement.get("regelart"))
                                    self.widgets[len(self.widgets) - 1].addRelativgrenze(id, class_enums.Regelarten(regelart))
                                if widgetElement.find("konvert") != None:
                                    konvertElement = widgetElement.find("konvert")
                                    konvertgruppe = str(konvertElement.get("gruppe")) # type: ignore
                                    konvertIstBerechnungseinheit = str(konvertElement.get("berechnungseinheit")) == "True" # type: ignore
                                    mitButton = str(konvertElement.get("button")) == "True" # type: ignore
                                    konvertEinheit = str(konvertElement.find("einheit").text) # type: ignore
                                    konvertStrukturformel = str(konvertElement.find("strukturformel").text) # type: ignore
                                    self.einheitToggles[self.widgets[len(self.widgets) - 1].getId()] = class_widgets.EinheitToggle(self.widgets[len(self.widgets) - 1], konvertgruppe, [widgetEinheit, konvertEinheit], konvertStrukturformel, zahlengrenzen, konvertIstBerechnungseinheit, mitButton)
                            elif widgetTyp == class_widgets.WidgetTyp.RADIOBUTTON.value:
                                checked = str(widgetElement.get("checked")) == "True" and partElement.get("geschlechtpruefung") == None
                                altersregel = str(widgetElement.get("altersregel"))
                                wertElement = widgetElement.find("wert")
                                wert = str(wertElement.text) # type: ignore
                                self.widgets.append(class_widgets.RadioButton(widgetId, partId, widgetTitel, widgetErklaerung, widgetEinheit, wert, checked, alterspruefung, altersregel, groessepruefung, gewichtpruefung))
                                logger.logger.info("Radiobutton angelegt (Part-ID: " + partId + ", Widget-ID: " + widgetId + ") angelegt")
                            # Prüfen, ob Titelbreite festgelegt
                            if widgetElement.get("titelbreite") != None:
                                self.widgets[len(self.widgets) - 1].setTitelbreite(int(str(widgetElement.get("titelbreite"))))
                else:
                    mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Problem beim Laden der Score-Daten.\nScoreGDT wird beendet.", QMessageBox.StandardButton.Ok)
                    mb.exec()
                    logger.logger.error("Problem beim Laden der Score-Daten. self.root: " + str(self.scoreRoot))
                    sys.exit()

            # Formularaufbau
            mainLayoutV = QVBoxLayout()
            scrollArea = QScrollArea()
            scrollWidget = QWidget()
            mainLayoutG = QGridLayout()
            groupBoxBegriffsdefinitionenLayoutG = QGridLayout()
            # Patientendaten
            patient = "Patient"
            if self.geschlecht == "2":
                patient = "Patientin"
            groupboxPatientendaten = QGroupBox(patient)
            groupboxPatientendatenLayoutG = QGridLayout()
            self.labelPseudolizenz = QLabel("+++ Pseudolizenz für Test-/ Präsentationszwecke +++")
            self.labelPseudolizenz.setStyleSheet("font-style:italic")
            self.labelPseudolizenz.setPalette(farbe.getTextPalette(farbe.farben.ROT, self.palette()))
            labelName = QLabel("Name: " + self.name)
            labelPatId = QLabel("ID: " + self.patId)
            self.geburtsdatumAlsDate = datetime.date(int(self.geburtsdatum[6:]), int(self.geburtsdatum[3:5]), int(self.geburtsdatum[:2]))
            labelAlter = QLabel("Alter: " + str(getAktuellesAlterInJahren(self.geburtsdatumAlsDate)) + " Jahre")
            labelGeburtsdatum = QLabel("Geburtsdatum: " + self.geburtsdatum)
            groupboxPatientendatenLayoutG.addWidget(labelName, 0, 0)
            groupboxPatientendatenLayoutG.addWidget(labelAlter, 0, 1)
            groupboxPatientendatenLayoutG.addWidget(labelPatId, 1, 0)
            groupboxPatientendatenLayoutG.addWidget(labelGeburtsdatum, 1, 1)
            groupboxPatientendaten.setLayout(groupboxPatientendatenLayoutG)
            # Titel
            labelScoreName = QLabel(str(self.scoreRoot.get("name"))) # type: ignore
            labelScoreName.setFont(self.fontBoldGross)
            labelScoreName.setPalette(farbe.getTextPalette(farbe.farben.BLAU, self.palette()))
            if self.scoreRoot.find("information") != None: #type: ignore
                labelScoreInformation = QLabel(str(self.scoreRoot.find("information").text)) #type: ignore
                labelScoreInformation.setFont(self.fontNormal)
                labelScoreInformation.setPalette(farbe.getTextPalette(farbe.farben.BLAU, self.palette()))
            if self.scoreRoot.find("quelle") != None: # type: ignore
                autor = str(self.scoreRoot.find("quelle").get("autor")) # type: ignore
                quelle = "Quelle: " + str(self.scoreRoot.find("quelle").text) + " (" + autor + ")" # type: ignore
                maxQuellenLaenge = 100
                if len(quelle) > maxQuellenLaenge:
                    pos = int(maxQuellenLaenge / 2)
                    while pos < len(quelle):
                        while pos < len(quelle) and quelle[pos] != " ":
                            pos += 1
                        quelle = quelle[:pos] + os.linesep + quelle[pos + 1:]
                        pos += int(maxQuellenLaenge / 2)
                labelScoreName.setToolTip(quelle)
                labelScoreName.setCursor(Qt.CursorShape.WhatsThisCursor)
            # Definitionen
            if self.scoreRoot.find("begriffsdefinitionen") != None: # type: ignore
                groupBoxBegriffsdefinitionen = QGroupBox("Begriffsdefinitionen")
                groupBoxBegriffsdefinitionen.setFont(self.fontBold)
                begriffsdefinitionenElement = self.scoreRoot.find("begriffsdefinitionen") # type: ignore
                zeile = 0
                for definitionElement in begriffsdefinitionenElement.findall("definition"): # type: ignore
                    bezeichnungLabel = QLabel(str(definitionElement.get("bezeichnung")) + ":")
                    bezeichnungLabel.setFont(self.fontNormal)
                    groupBoxBegriffsdefinitionenLayoutG.addWidget(bezeichnungLabel, zeile, 0, alignment=Qt.AlignmentFlag.AlignLeft) # type: ignore
                    definitionLabel = QLabel(definitionElement.text)
                    definitionLabel.setFont(self.fontNormal)
                    groupBoxBegriffsdefinitionenLayoutG.addWidget(definitionLabel, zeile, 1, alignment=Qt.AlignmentFlag.AlignLeft)
                    zeile += 1
                groupBoxBegriffsdefinitionen.setLayout(groupBoxBegriffsdefinitionenLayoutG)
            # Score
            if self.scoreRoot.get("altersregel") != None: # type: ignore
                alter = getAktuellesAlterInJahren(self.geburtsdatumAlsDate)
                altersregeln = str(self.scoreRoot.get("altersregel")).split("_") # type: ignore
                altersregelErfuellt = True
                for altersregel in altersregeln:
                    if not self.regelIstErfuellt(str(alter) + altersregel):
                        altersregelErfuellt = False
                        break
                if not altersregelErfuellt: # type: ignore
                    mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von ScoreGDT", "Das Alter von " + str(alter) + " Jahren liegt außerhalb der für \"" + str(self.scoreRoot.get("name")) + "\" zulässigen Grenzen.\nSoll ScoreGDT neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) # type: ignore
                    mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                    mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                    mb.button(QMessageBox.StandardButton.No).setText("Nein")
                    if mb.exec() == QMessageBox.StandardButton.Yes:
                        os.execl(sys.executable, __file__, *sys.argv)
            buttonGroups = {}
            palette = QPalette()
            colorWindow = palette.window().color()
            palette.setColor(QPalette.Active, QPalette.Window, colorWindow) # type: ignore
            for part in self.parts:
                buttonGroups.clear()
                for widget in self.widgets:
                    if widget.getTyp() == class_widgets.WidgetTyp.CHECKBOX and widget.getButtongroup() != "":
                        buttonGroups[widget.getButtongroup()] = QButtonGroup(self)
                partLayout = QGridLayout()
                partGridZeile = 0
                if part.getErklaerung() != "None":
                    labelErklaerung = QLabel(part.getErklaerung())
                    labelErklaerung.setFont(self.fontNormal)
                    partLayout.addWidget(labelErklaerung, 0, 0, 1, 3, alignment=Qt.AlignmentFlag.AlignTop)
                    partGridZeile = 1
                for widget in self.widgets:
                    if part.getId() == widget.getPartId():
                        labelTitel = QLabel(widget.getTitel())
                        labelTitel.setFont(self.fontNormal)
                        if widget.getTitelbreite() != -1:
                            labelTitel.setFixedWidth(widget.getTitelbreite())
                        partLayout.addWidget(labelTitel, partGridZeile, 0, alignment=Qt.AlignmentFlag.AlignTop)
                        widgetWidget = widget.getQt()
                        widgetWidget.setFont(self.fontNormal)
                        if widget.getTyp() == class_widgets.WidgetTyp.CHECKBOX or widget.getTyp() == class_widgets.WidgetTyp.RADIOBUTTON:
                            widgetWidget.clicked.connect(self.widgetChanged)
                            widgetWidget.setPalette(palette)
                        elif widget.getTyp() == class_widgets.WidgetTyp.LINEEDIT:
                            widgetWidget.textEdited.connect(self.widgetChanged)
                        elif widget.getTyp() == class_widgets.WidgetTyp.COMBOBOX:
                            widgetWidget.currentIndexChanged.connect(self.widgetChanged)
                        partLayout.addWidget(widgetWidget, partGridZeile, 1, alignment=Qt.AlignmentFlag.AlignTop)
                        einheitUndErklärung = ""
                        if widget.getEinheit() != "":
                            einheitUndErklärung = widget.getEinheit() + " "
                        if widget.getTyp() == class_widgets.WidgetTyp.LINEEDIT and widget.zahlengrenzeGesetzt():
                            einheitUndErklärung +="("
                            zahlengrenzenDict = widget.getZahlengrenzen()
                            zahlengrenzenList = list(zahlengrenzenDict)
                            if len(zahlengrenzenList) == 1:
                                if zahlengrenzenDict[zahlengrenzenList[0]] == class_enums.Regelarten.KLEINERALS:
                                    einheitUndErklärung += "\u003c"
                                elif zahlengrenzenDict[zahlengrenzenList[0]] == class_enums.Regelarten.KLEINERGLEICHALS:
                                    einheitUndErklärung += "\u2264"
                                elif zahlengrenzenDict[zahlengrenzenList[0]] == class_enums.Regelarten.GROESSERALS:
                                    einheitUndErklärung += "\u003e"
                                elif zahlengrenzenDict[zahlengrenzenList[0]] == class_enums.Regelarten.GROESSERGLEICHALS:
                                    einheitUndErklärung += "\u2265"
                                einheitUndErklärung += str(zahlengrenzenList[0]).replace(".", ",").replace(",0", "") + " " + widget.getEinheit()
                            else:
                                einheitUndErklärung += str(zahlengrenzenList[0]).replace(".", ",").replace(",0", "") + "-" + str(zahlengrenzenList[1]).replace(".", ",").replace(",0", "") + " " + widget.getEinheit()
                            einheitUndErklärung += ")"
                        elif widget.getErklaerung() != "":
                            einheitUndErklärung += "(" + widget.getErklaerung() + ")"
                        labelEinheitUndErklaerung = QLabel(einheitUndErklärung)
                        labelEinheitUndErklaerung.setFont(self.fontNormal)
                        partLayout.addWidget(labelEinheitUndErklaerung, partGridZeile, 2, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
                        # Einheitenkonvertierung
                        if widget.getTyp() == class_widgets.WidgetTyp.LINEEDIT and widget.getId() in self.einheitToggles:
                            self.einheitToggles[widget.getId()].setEinheitenLabel(labelEinheitUndErklaerung)
                            if self.einheitToggles[widget.getId()].getQt() != None:
                                partLayout.addWidget(self.einheitToggles[widget.getId()].getQt(), partGridZeile, 3, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
                                self.einheitToggles[widget.getId()].getQt().clicked.connect(lambda checked = False, lineEditId = widget.getId(): self.konvertButtonClicked(checked, lineEditId))
                        # Prüfen, ob CheckBox ButtonGroup zugehörig
                        if widget.getTyp() == class_widgets.WidgetTyp.CHECKBOX and widget.getButtongroup() in buttonGroups:
                            buttonGroups[widget.getButtongroup()].addButton(widget.getQt())
                            widget.getQt().pressed.connect(lambda cb = widget.getQt(): self.buttonGroupCheckBoxPressed(cb))
                            widget.getQt().clicked.connect(lambda checked = False, cb = widget.getQt(): self.buttonGroupCheckBoxClicked(checked, cb))
                        # Prüfen, ob Alterstextfeld
                        elif widget.getTyp() == class_widgets.WidgetTyp.LINEEDIT and widget.alterspruefungAktiv():
                            widget.getQt().setText(str(getAktuellesAlterInJahren(self.geburtsdatumAlsDate)))
                            logger.logger.info("Alter aus GDT-Datei in Lineedit " + widget.getId() + " eingetragen")
                            if widget.zahlengrenzeGesetzt() and not widget.zahlengrenzregelnErfuellt():
                                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von ScoreGDT", "Das Alter liegt außerhalb der zulässigen Grenzen.\nSoll ScoreGDT neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                                if mb.exec() == QMessageBox.StandardButton.Yes:
                                    os.execl(sys.executable, __file__, *sys.argv)
                                else:
                                    widget.getQt().setFocus()
                                widget.getQt().selectAll()
                        # Prüfen, ob Gewichtstextfeld
                        elif widget.getTyp() == class_widgets.WidgetTyp.LINEEDIT and widget.gewichtpruefungAktiv():
                            if gd.getInhalt("3623") != None:
                                widget.getQt().setText(gd.getInhalt("3623"))
                                logger.logger.info("Gewicht aus GDT-Datei in Lineedit " + widget.getId() + " eingetragen")
                                if widget.zahlengrenzeGesetzt() and not widget.zahlengrenzregelnErfuellt():
                                    mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von ScoreGDT", "Das Körpergewicht liegt außerhalb der zulässigen Grenzen.\nSoll ScoreGDT neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                                    mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                                    mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                                    mb.button(QMessageBox.StandardButton.No).setText("Nein")
                                    if mb.exec() == QMessageBox.StandardButton.Yes:
                                        os.execl(sys.executable, __file__, *sys.argv)
                                    else:
                                        widget.getQt().setFocus()
                                    widget.getQt().selectAll()
                        # Prüfen, ob Größetextfeld
                        elif widget.getTyp() == class_widgets.WidgetTyp.LINEEDIT and widget.groessepruefungAktiv():
                            if gd.getInhalt("3622") != None:
                                widget.getQt().setText(gd.getInhalt("3622"))
                                logger.logger.info("Größe aus GDT-Datei in Lineedit " + widget.getId() + " eingetragen")
                                if widget.zahlengrenzeGesetzt() and not widget.zahlengrenzregelnErfuellt():
                                    mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von ScoreGDT", "Die Körpergröße liegt außerhalb der zulässigen Grenzen.\nSoll ScoreGDT neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                                    mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                                    mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                                    mb.button(QMessageBox.StandardButton.No).setText("Nein")
                                    if mb.exec() == QMessageBox.StandardButton.Yes:
                                        os.execl(sys.executable, __file__, *sys.argv)
                                    else:
                                        widget.getQt().setFocus()
                                    widget.getQt().selectAll()
                        elif (widget.getTyp() == class_widgets.WidgetTyp.CHECKBOX or widget.getTyp() == class_widgets.WidgetTyp.RADIOBUTTON) and widget.alterspruefungAktiv():
                            regelnErfuellt = True
                            for regel in widget.getAltersregeln():
                                # Prüfen, ob geschlechtsabhängige Regel (Format z.B.: M:GROESSERALS50_W:GROESSERALS60)
                                regelnMW = regel.split("_")
                                tempRegel = str(getAktuellesAlterInJahren(self.geburtsdatumAlsDate)) + regel
                                if "_" in regel:
                                    regelM = regelnMW[0][2:]
                                    regelW = regelnMW[1][2:]
                                    if self.geschlecht == "1":
                                        tempRegel = str(getAktuellesAlterInJahren(self.geburtsdatumAlsDate)) + regelM
                                    else:
                                        tempRegel = str(getAktuellesAlterInJahren(self.geburtsdatumAlsDate)) + regelW
                                if not self.regelIstErfuellt(tempRegel):
                                    regelnErfuellt = False
                                    break
                            widget.getQt().setChecked(regelnErfuellt)
                            # Wenn RadioButton, andere Buttons unchecken
                            for w in self.widgets:
                                if widget.getTyp() == class_widgets.WidgetTyp.RADIOBUTTON and w.getId() != widget.getId() and w.getPartId() == widget.getPartId():
                                    w.getQt().setChecked(not regelnErfuellt)
                        # Prüfen, ob Geschlechtpart (Groupbox mit 2 Radiobuttons)
                        if part.geschlechtpruefungAktiv() and widget.getTyp() == class_widgets.WidgetTyp.RADIOBUTTON:
                            if ("männlich" in widget.getTitel().lower() or "männlich" in widget.getErklaerung().lower()) and self.geschlecht == "1":
                                widget.getQt().setChecked(True)
                                logger.logger.info("Radiobutton " + widget.getId() + " als männlich aktiviert")
                            elif ("weiblich" in widget.getTitel().lower() or "weiblich" in widget.getErklaerung().lower()) and self.geschlecht == "2":
                                widget.getQt().setChecked(True)
                                logger.logger.info("Radiobutton " + widget.getId() + " als weiblich aktiviert")
                        # Prüfen, ob Geschlechtwidget (Checkbox)
                        if widget.getTyp() == class_widgets.WidgetTyp.CHECKBOX and widget.geschlechtpruefungAktiv():
                            if ("männlich" in widget.getTitel().lower() or "männlich" in widget.getErklaerung().lower()) and self.geschlecht == "1":
                                widget.getQt().setChecked(True)
                                logger.logger.info("Checkbox " + widget.getId() + " als männlich aktiviert")
                            elif ("weiblich" in widget.getTitel().lower() or "weiblich" in widget.getErklaerung().lower()) and self.geschlecht == "2":
                                widget.getQt().setChecked(True)
                                logger.logger.info("Checkbox " + widget.getId() + " als weiblich aktiviert")
                        partGridZeile += 1
                if part.getTyp() == class_part.PartTyp.FRAME:
                    frame = QFrame()
                    if part.getHintergrundbild() != "":
                        hintergrundbild = QPixmap(os.path.join(basedir, "bilder", part.getHintergrundbild()))
                        labelHintergrundbild = QLabel()
                        labelHintergrundbild.setPixmap(hintergrundbild)
                        partLayout.addWidget(labelHintergrundbild, 0, 0, alignment=Qt.AlignmentFlag.AlignCenter)
                    frame.setLayout(partLayout)
                    mainLayoutG.addWidget(frame, part.getZeile(), part.getSpalte())
                elif part.getTyp() == class_part.PartTyp.GROUPBOX:
                    groupBox = QGroupBox(part.getTitel())
                    groupBox.setFont(self.fontBold)
                    groupBox.setLayout(partLayout)
                    mainLayoutG.addWidget(groupBox, part.getZeile(), part.getSpalte())

            self.pushButtonBerechnen = QPushButton("Score berechnen")
            self.pushButtonBerechnen.setFixedHeight(40)
            self.pushButtonBerechnen.setFont(self.fontBold)
            self.pushButtonBerechnen.clicked.connect(self.pushButtonBerechnenClicked)

            ergebnisLayoutH = QHBoxLayout()
            labelScoreErgebnis = QLabel("Ergebnis:")
            labelScoreErgebnis.setFont(self.fontBold)
            self.lineEditScoreErgebnis = QLineEdit()
            self.lineEditScoreErgebnis.setReadOnly(True)
            self.lineEditScoreErgebnis.setFont(self.fontBoldGross)
            self.lineEditScoreErgebnis.textChanged.connect(self.lineEditScoreErgebnisTextChanged)
            ergebnisEinheit = ""
            if self.scoreRoot.find("berechnung").find("ergebniseinheit") != None: # type: ignore
                ergebnisEinheit = str(self.scoreRoot.find("berechnung").find("ergebniseinheit").text) # type: ignore
            self.labelScoreErgebnisEinheit = QLabel(ergebnisEinheit) # type: ignore
            self.labelScoreErgebnisEinheit.setFont(self.fontBold)
            auswertungElement = self.scoreRoot.find("auswertung") # type: ignore
            if auswertungElement != None:
                ergebnisbereiche = []
                beschreibungen = []
                for beurteilungElement in auswertungElement.findall("beurteilung"):
                    ergebnisbereiche.append(str(beurteilungElement.find("ergebnisbereich").text)) # type: ignore
                    beschreibungen.append(str(beurteilungElement.find("beschreibung").text)) # type: ignore
                groupBoxAuswertungLayoutG = QGridLayout()
                groupBoxAuswertung = QGroupBox("Auswertung")
                groupBoxAuswertung.setFont(self.fontBold)
                groupBoxAuswertung.setLayout(groupBoxAuswertungLayoutG)
                self.labelErgebnisbereiche = []
                self.labelBeschreibungen = []
                i = 0
                for ergebnisbereich in ergebnisbereiche:
                    tempLabelErgebnis = QLabel(ergebnisbereich)
                    tempLabelErgebnis.setFont(self.fontNormal)
                    tempLabelBeschreibung= QLabel(beschreibungen[i])
                    tempLabelBeschreibung.setFont(self.fontNormal)
                    self.labelErgebnisbereiche.append(tempLabelErgebnis)
                    self.labelBeschreibungen.append(tempLabelBeschreibung)
                    groupBoxAuswertungLayoutG.addWidget(tempLabelErgebnis, i, 0)
                    groupBoxAuswertungLayoutG.setHorizontalSpacing(20)
                    groupBoxAuswertungLayoutG.addWidget(tempLabelBeschreibung, i, 1)
                    i += 1

            datumBenutzerLayoutG = QGridLayout()
            labelDokumentiertAm = QLabel("Dokumentiert am:")
            labelDokumentiertAm.setFont(self.fontNormal)
            self.untersuchungsdatum = QDate().currentDate()
            self.dateEditUntersuchungsdatum = QDateEdit()
            self.dateEditUntersuchungsdatum.setDate(self.untersuchungsdatum)
            self.dateEditUntersuchungsdatum.setDisplayFormat("dd.MM.yyyy")
            self.dateEditUntersuchungsdatum.setCalendarPopup(True)
            self.dateEditUntersuchungsdatum.userDateChanged.connect(self.dateEditUntersuchungsdatumChanged)
            labelDokumentiertVon = QLabel("Dokumentiert von:")
            labelDokumentiertVon.setFont(self.fontNormal)
            self.comboBoxBenutzer = QComboBox()
            self.comboBoxBenutzer.addItems(self.benutzernamenListe)
            self.comboBoxBenutzer.currentIndexChanged.connect(self.comboBoxBenutzerIndexChanged)
            aktBenNum = 0
            if self.aktuelleBenuztzernummer < len(self.benutzernamenListe):
                aktBenNum = self.aktuelleBenuztzernummer
            self.comboBoxBenutzer.setCurrentIndex(aktBenNum)
            layoutPdfErstellenDatenSendenH = QHBoxLayout()
            self.checkBoxPdfErzeugen = QCheckBox("PDF erzeugen")
            self.checkBoxPdfErzeugen.setChecked(self.pdferzeugen)
            self.checkBoxPdfErzeugen.setFixedWidth(150)
            self.pushButtonSenden = QPushButton("Daten senden")
            self.pushButtonSenden.setFont(self.fontBold)
            self.pushButtonSenden.setFixedHeight(40)
            self.pushButtonSenden.clicked.connect(self.pushButtonSendenClicked)
            datumBenutzerLayoutG.addWidget(labelDokumentiertAm, 0, 0)
            datumBenutzerLayoutG.addWidget(labelDokumentiertVon, 0, 1)
            datumBenutzerLayoutG.addWidget(self.dateEditUntersuchungsdatum, 1, 0)
            datumBenutzerLayoutG.addWidget(self.comboBoxBenutzer, 1, 1)
            layoutPdfErstellenDatenSendenH.addWidget(self.checkBoxPdfErzeugen)
            layoutPdfErstellenDatenSendenH.addWidget(self.pushButtonSenden)
                        
            ## Nur mit Lizenz
            if self.addOnsFreigeschaltet and gdttoolsL.GdtToolsLizenzschluessel.getSoftwareId(self.lizenzschluessel) == gdttoolsL.SoftwareId.SCOREGDTPSEUDO:
                mainLayoutV.addWidget(self.labelPseudolizenz, alignment=Qt.AlignmentFlag.AlignCenter)
            ## /Nur mit Lizenz
            mainLayoutV.addWidget(groupboxPatientendaten)
            mainLayoutV.addWidget(labelScoreName, alignment=Qt.AlignmentFlag.AlignCenter)
            if self.scoreRoot.find("information") != None: #type: ignore
                mainLayoutV.addWidget(labelScoreInformation, alignment=Qt.AlignmentFlag.AlignCenter)
            if self.scoreRoot.find("begriffsdefinitionen") != None: # type: ignore
                mainLayoutG.addWidget(groupBoxBegriffsdefinitionen, mainLayoutG.rowCount(), 0, 1, mainLayoutG.columnCount(), alignment=Qt.AlignmentFlag.AlignCenter)
            scrollWidget.setLayout(mainLayoutG)
            mainLayoutGBreite = mainLayoutG.sizeHint().width()
            screenBreite = self.screen().availableGeometry().width()
            if mainLayoutGBreite > screenBreite * 0.95:
                mainLayoutGBreite = int(screenBreite * 0.95)
            scrollArea.setFixedWidth(mainLayoutGBreite + 20)
            mainLayoutGHoehe = mainLayoutG.sizeHint().height()
            screenHoehe = self.screen().availableGeometry().height()
            if mainLayoutGHoehe + self.height() < screenHoehe * 0.95:
                scrollArea.setFixedHeight(mainLayoutGHoehe + 20)
            scrollArea.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.MinimumExpanding)
            scrollArea.setWidget(scrollWidget)
            scrollArea.setWidgetResizable(True)
            mainLayoutV.addWidget(scrollArea)
            mainLayoutV.addWidget(self.pushButtonBerechnen) 
            ergebnisLayoutH.addWidget(labelScoreErgebnis)
            ergebnisLayoutH.addWidget(self.lineEditScoreErgebnis)
            ergebnisLayoutH.addWidget(self.labelScoreErgebnisEinheit)
            mainLayoutV.addLayout(ergebnisLayoutH)
            mainLayoutV.addSpacing(20)
            if auswertungElement != None:
                mainLayoutV.addWidget(groupBoxAuswertung, alignment=Qt.AlignmentFlag.AlignCenter)
            mainLayoutV.addLayout(datumBenutzerLayoutG)
            mainLayoutV.addLayout(layoutPdfErstellenDatenSendenH)
            ## Nur mit Lizenz
            if self.addOnsFreigeschaltet:
                gueltigeLizenztage = gdttoolsL.GdtToolsLizenzschluessel.nochTageGueltig(self.lizenzschluessel)
                if gueltigeLizenztage  > 0 and gueltigeLizenztage <= 30:
                    labelLizenzLaeuftAus = QLabel("Die genutzte Lizenz ist noch " + str(gueltigeLizenztage) + " Tage gültig.")
                    labelLizenzLaeuftAus.setPalette(farbe.getTextPalette(farbe.farben.ROT, self.palette()))
                    mainLayoutV.addWidget(labelLizenzLaeuftAus, alignment=Qt.AlignmentFlag.AlignCenter)
            else:
                self.pushButtonSenden.setEnabled(False)
                self.pushButtonSenden.setText("Keine gültige Lizenz")
            ## /Nur mit Lizenz
            self.widget.setLayout(mainLayoutV)
            self.setCentralWidget(self.widget)

            # Menü
            menubar = self.menuBar()
            anwendungMenu = menubar.addMenu("")
            aboutAction = QAction(self)
            aboutAction.setMenuRole(QAction.MenuRole.AboutRole)
            aboutAction.triggered.connect(self.ueberScoreGdt) 
            updateAction = QAction("Auf Update prüfen", self)
            updateAction.setMenuRole(QAction.MenuRole.ApplicationSpecificRole)
            updateAction.triggered.connect(self.updatePruefung) 
            scoreMenu = menubar.addMenu("Score")
            scoreMenuAuswaehlenAction = QAction("Score auswählen (Neustart)", self)
            scoreMenuAuswaehlenAction.triggered.connect(self.scoreAuswaehlen)
            scoreMenuFavoritenVerwaltenAction = QAction("Favoriten verwalten", self)
            scoreMenuFavoritenVerwaltenAction.triggered.connect(self.scoreFavoritenVerwalten)
            scoreGdtNameInClipboardAction = QAction("Scorename als Startargument in die Zwischenablage kopieren", self)
            scoreGdtNameInClipboardAction.triggered.connect(self.scoreGdtNameInClipboard)

            einstellungenMenu = menubar.addMenu("Einstellungen")
            einstellungenAllgemeinAction = QAction("Allgemeine Einstellungen", self)
            einstellungenAllgemeinAction.triggered.connect(lambda checked = False, neustartfrage = True: self.einstellungenAllgemein(checked, neustartfrage))
            einstellungenGdtAction = QAction("GDT-Einstellungen", self)
            einstellungenGdtAction.triggered.connect(lambda checked = False, neustartfrage = True: self.einstellungenGdt(checked, neustartfrage))
            einstellungenBenutzerAction = QAction("BenutzerInnen verwalten", self)
            einstellungenBenutzerAction.triggered.connect(lambda checked = False, neustartfrage = True: self.einstellungenBenutzer(checked, neustartfrage)) 
            ## Nur mit Lizenz
            einstellungenErweiterungenAction = QAction("LANR/Lizenzschlüssel", self)
            einstellungenErweiterungenAction.triggered.connect(lambda checked = False, neustartfrage = True: self.einstellungenLanrLizenzschluessel(checked, neustartfrage)) 
            einstellungenImportExportAction = QAction("Im- /Exportieren", self)
            einstellungenImportExportAction.triggered.connect(self.einstellungenImportExport) 
            einstellungenImportExportAction.setMenuRole(QAction.MenuRole.NoRole)
            ## /Nur mit Lizenz
            hilfeMenu = menubar.addMenu("Hilfe")
            hilfeWikiAction = QAction("ScoreGDT Wiki", self)
            hilfeWikiAction.triggered.connect(self.scoregdtWiki)
            hilfeUpdateAction = QAction("Auf Update prüfen", self)
            hilfeUpdateAction.triggered.connect(self.updatePruefung)
            hilfeAutoUpdateAction = QAction("Automatisch auf Update prüfen", self)
            hilfeAutoUpdateAction.setCheckable(True)
            hilfeAutoUpdateAction.setChecked(self.autoupdate)
            hilfeAutoUpdateAction.triggered.connect(self.autoUpdatePruefung)
            hilfeUeberAction = QAction("Über ScoreGDT", self)
            hilfeUeberAction.setMenuRole(QAction.MenuRole.NoRole)
            hilfeUeberAction.triggered.connect(self.ueberScoreGdt)
            hilfeEulaAction = QAction("Lizenzvereinbarung (EULA)", self)
            hilfeEulaAction.triggered.connect(self.eula) 
            hilfeLogExportieren = QAction("Log-Verzeichnis exportieren", self)
            hilfeLogExportieren.triggered.connect(self.logExportieren) 
            
            anwendungMenu.addAction(aboutAction)
            anwendungMenu.addAction(updateAction)
            scoreMenu.addAction(scoreMenuAuswaehlenAction)
            scoreMenu.addAction(scoreMenuFavoritenVerwaltenAction)
            scoreMenu.addAction(scoreGdtNameInClipboardAction)
            einstellungenMenu.addAction(einstellungenAllgemeinAction)
            einstellungenMenu.addAction(einstellungenGdtAction)
            einstellungenMenu.addAction(einstellungenBenutzerAction)
            ## Nur mit Lizenz
            einstellungenMenu.addAction(einstellungenErweiterungenAction)
            einstellungenMenu.addAction(einstellungenImportExportAction)
            ## /Nur mit Lizenz
            hilfeMenu.addAction(hilfeWikiAction)
            hilfeMenu.addSeparator()
            hilfeMenu.addAction(hilfeUpdateAction)
            hilfeMenu.addAction(hilfeAutoUpdateAction)
            hilfeMenu.addSeparator()
            hilfeMenu.addAction(hilfeUeberAction)
            hilfeMenu.addAction(hilfeEulaAction)
            hilfeMenu.addSeparator()
            hilfeMenu.addAction(hilfeLogExportieren)
        else:
            sys.exit()

    def konvertButtonClicked(self, checked, lineEditId):
        einheitToggle = self.einheitToggles[lineEditId]
        button = einheitToggle.getQt()
        if button != None:
            button.setText(einheitToggle.getAktuelleEinheit())
        konvertgruppe = einheitToggle.getKonvertgruppe()
        for einheitToggle in self.einheitToggles:
            el = self.einheitToggles[einheitToggle].getEinheitenLabel()
            if self.einheitToggles[einheitToggle].getKonvertgruppe() == konvertgruppe:
                einheitAlt = self.einheitToggles[einheitToggle].getAktuelleEinheit()
                zahlengrenzenAlt = self.einheitToggles[einheitToggle].getAktuelleZahlengrenzenAlsString()
                self.einheitToggles[einheitToggle].toggle()
                einheitNeu = self.einheitToggles[einheitToggle].getAktuelleEinheit()
                zahlengrenzenNeu = self.einheitToggles[einheitToggle].getAktuelleZahlengrenzenAlsString()
                el.setText(el.text().replace(einheitAlt, einheitNeu))
                labeltextMitaltenZahlengrenzen = el.text()
                for i in range(len(zahlengrenzenAlt)):
                    position = labeltextMitaltenZahlengrenzen.find(zahlengrenzenAlt[i])
                    labeltextMitaltenZahlengrenzen = labeltextMitaltenZahlengrenzen[0:position] + zahlengrenzenNeu[i] + labeltextMitaltenZahlengrenzen[position + len(zahlengrenzenAlt[i]):]
                el.setText(labeltextMitaltenZahlengrenzen)
                    

    def widgetChanged(self):
        self.lineEditScoreErgebnis.setText("")
        self.auswertung("")

    def buttonGroupCheckBoxPressed(self, checkbox):
        checkbox.group().setExclusive(not checkbox.isChecked())

    def buttonGroupCheckBoxClicked(self, checked, checkbox):
        checkbox.group().setExclusive(True)

    def getScoreXml(self, name:str):
        """
        Gibt das score-Element aus scores.xml zurück
        Parameter:
            name: Name des Scores
        Return:
            score:ElementTree.Element oder None, falls nicht gefunden
        """
        scoreElement = None
        try:
            tree = ElementTree.parse(os.path.join(basedir, "scores", "scores.xml"))
            root = tree.getroot()
            for score in root.findall("score"):
                if str(score.get("name")) == name:
                    scoreElement = score
        except Exception as e:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Fehler beim Laden von \"scores.xml\"", QMessageBox.StandardButton.Ok)
            mb.exec()
            logger.logger.warning("Fehler beim Laden von scores.xml: " + str(e))
        return scoreElement

    def getWertAusWidgetId(self, widgetId:str):
        """
        Gib tden aktuellen Wert eine Widgets zurück
        Parameter:
            widgetId:str
        Return:
            Aktueller Wert:str
            - bei Radiobutton-Groupbox Wert des aktuelle gewählten Buttons
            - bei Combobox Wert des aktuell gewählten Items
            - "", wenn widgetId nicht existiert
        """
        wert = ""
        for widget in self.widgets:
            if widget.getId() == widgetId:
                if widget.getTyp() == class_widgets.WidgetTyp.RADIOBUTTON:
                    wert = self.getRadiobuttonWertAusGroupbox(widget.getPartId())
                    break
                elif widget.getTyp() == class_widgets.WidgetTyp.COMBOBOX:
                    wert = widget.getWert(widget.getQt().currentIndex())
                    break
                elif widget.getTyp() == class_widgets.WidgetTyp.CHECKBOX:
                    wert = "0"
                    if widget.isChecked():
                        wert = widget.getWert()
                        break
                elif widget.getTyp() == class_widgets.WidgetTyp.LINEEDIT:
                    wert = widget.getWert(self.einheitToggles)
                    break
                else:
                    wert = widget.getWert()
                    break
        return wert       

    def getRadiobuttonWertAusGroupbox(self, groupboxId:str):
        """
        Gibt den Wert des aktuell gewählten Buttons einer Radiobutton-Groupbox zurück
        Parameter:
            groupboxId:str
        Return:
            Wert des aktuell gewählten Radiobuttons:str
            - "", wenn groupboxId nicht existiert oder kein Radiobutton in Groupbox
        """
        wert = ""
        for widget in self.widgets:
            if widget.getPartId() == groupboxId and widget.getTyp() == class_widgets.WidgetTyp.RADIOBUTTON:
                if widget.isChecked():
                    wert = widget.getWert()
                    break
        return wert
    
    def getPart(self, partId):
        """Gibt einen Part zurück
        Parameter:
            partId:str
        Return:
            Part:Part
        """
        gesuchterPart = None
        for part in self.parts:
            if part.getId() == partId:
                gesuchterPart = part
                break
        return gesuchterPart
    
    def berechnung(self, formel:str, dezimalstellen:int):
        """
        Berechnet das Ergebnis einer Formel
        Parameter:
            formel:str
        Return:
            Ergebnis der Berechnung: float
        """
        try:
            berechnung = class_Rechenoperation.Rechenoperation(formel)(dezimalstellen, -1)
            return berechnung
        except class_Rechenoperation.RechenoperationException as e:
            logger.logger.error("Fehler bei der Score-Berechnung: " + str(e))
            mb = QMessageBox(QMessageBox.Icon.Critical, "Hinweis von ScoreGDT", "Fehler bei der Score-Berechnung" + str(e), QMessageBox.StandardButton.Ok)
            mb.exec()
    
    def regelIstErfuellt(self, regel:str):
        """
        Prüft, ob eine Regel innerhalb einer Variablenbedingung erfüllt ist
        Parameter: 
            regel im Format z. B. xKLEINERALSy:str
        """
        regexZahl = r"^-?\d+([.,]\d)?$"
        regelErfuellt = False
        regel = regel.replace(" ", "")
        # regelMitWerten = self.ersetzeIdVariablen(regel)
        for regelart in class_enums.Regelarten._member_names_:
            if regelart in regel: # ehemals regelMitWerten
                operanden = regel.split(regelart) # ehemals regelMitWerten
                operandenAlsZahl = []
                sindZahlen = True
                for operand in operanden:
                    if re.match(regexZahl, operand) == "None":
                        sindZahlen = False
                    if "." in operand:
                        operandenAlsZahl.append(float(operand))
                    else:
                        operandenAlsZahl.append(int(operand))
                if sindZahlen:
                    if regelart == class_enums.Regelarten.KLEINERALS.value:
                        regelErfuellt = operandenAlsZahl[0] < operandenAlsZahl[1]
                    elif regelart == class_enums.Regelarten.KLEINERGLEICHALS.value:
                        regelErfuellt = operandenAlsZahl[0] <= operandenAlsZahl[1]
                    elif regelart == class_enums.Regelarten.ISTGLEICH.value:
                        regelErfuellt = operandenAlsZahl[0] == operandenAlsZahl[1]
                    elif regelart == class_enums.Regelarten.GROESSERALS.value:
                        regelErfuellt = operandenAlsZahl[0] > operandenAlsZahl[1]
                    elif regelart == class_enums.Regelarten.GROESSERGLEICHALS.value:
                        regelErfuellt = operandenAlsZahl[0] >= operandenAlsZahl[1]
                    break
                else:
                    logger.logger.error("Fehler bei Prüfung der Regel " + regel + ": nicht beide Operanden sind Zahlen")
                    mb = QMessageBox(QMessageBox.Icon.Critical, "Hinweis von ScoreGDT", "Fehler bei Prüfung der Regel " + regel + ": nicht beide Operanden sind Zahlen", QMessageBox.StandardButton.Ok)
                    mb.exec()
                    break
        return regelErfuellt


    def ersetzeIdVariablen(self, string:str):
        """
        Ersetzt Variablen im Format $id{xxx} durch den aktuellen Wert des Widgets mit der id xxx
        Parameter:
            string:str
        Return:
            string mit ersetzten Variablen
        """
        patternId = r"\$id{[^{}]+}"
        idVariablen = re.findall(patternId, string)
        ersetzt = string
        for idVariable in idVariablen:
            id = idVariable[4:-1]
            if id == "ALTER":
                ersetzt = ersetzt.replace(idVariable, str(getAktuellesAlterInJahren(self.geburtsdatumAlsDate)))
            else:
                ersetzt = ersetzt.replace(idVariable, self.getWertAusWidgetId(id))
        return ersetzt
    
    def ersetzeVariablen(self, variablen:dict, string:str):
        """
        Ersetzt Variablen im Format $var{xxx} durch den Wert
        Parameter:
            variablen: dict mit key: Variablenname, value: Variablenwert
            string: str
        Return: string mit ersetzten Variablen
        """
        patternVar = r"\$var{[^{}]+}"
        varVariablen = re.findall(patternVar, string)
        ersetzt = string
        for varVariable in varVariablen:
            varName = varVariable[5:-1]
            if varName in variablen:
                ersetzt = ersetzt.replace(varVariable, variablen[varName])
        return ersetzt
    
    def pushButtonBerechnenClicked(self):
        formularOk = True
        for widget in self.widgets:
            if widget.getTyp() == class_widgets.WidgetTyp.LINEEDIT:
                if not widget.regexOk():
                    mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von ScoreGDT", "Textfeld " + widget.getTitel() + " ungültig ausgefüllt.", QMessageBox.StandardButton.Ok)
                    mb.exec()
                    widget.getQt().setFocus()
                    widget.getQt().selectAll()
                    formularOk = False
                    break
                elif self.bereichsgrenzenerzwingen and widget.zahlengrenzeGesetzt():
                    if not widget.zahlengrenzregelnErfuellt():
                        mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von ScoreGDT", "Textfeld " + widget.getTitel() + " ungültig ausgefüllt.", QMessageBox.StandardButton.Ok)
                        mb.exec()
                        widget.getQt().setFocus()
                        widget.getQt().selectAll()
                        formularOk = False
                        break
                elif not self.bereichsgrenzenerzwingen and widget.zahlengrenzeGesetzt():
                    if not widget.zahlengrenzregelnErfuellt():
                        zahl = float(widget.getQt().text().replace(",", "."))
                        grenzzahl = "{:.1f}".format(widget.getGrenzzahl(zahl)).replace(".", ",").replace(",0", "")
                        widget.getQt().setText(grenzzahl)
                        mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von ScoreGDT", "Textfeld " + widget.getTitel() + " ungültig ausgefüllt. Der Wert wird auf " + grenzzahl + " gesetzt.", QMessageBox.StandardButton.Ok)
                        mb.exec()
                if widget.relativgrenzeGesetzt():
                    relativgrenzen = widget.getRelativgrenzen()
                    for relativgrenze in relativgrenzen:
                        id = str(relativgrenze)[4:-1] # xxx aus $id{xxx}
                        regelart = relativgrenzen[relativgrenze]
                        regel = widget.getWert(self.einheitToggles) + regelart.value + self.getWertAusWidgetId(id)
                        if not self.regelIstErfuellt(regel):
                            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von ScoreGDT", "Textfeld " + widget.getTitel() + " ungültig ausgefüllt.", QMessageBox.StandardButton.Ok)
                            mb.exec()
                            widget.getQt().setFocus()
                            widget.getQt().selectAll()
                            formularOk = False
                            break
        if formularOk :
            #try:
            # $var{...}-Werte auslesen
            berechnungElement = self.scoreRoot.find("berechnung") # type: ignore
            formelElement = berechnungElement.find("formel") # type: ignore
            dezimalstellen = 0
            if formelElement.get("dezimalstellen") != None: # type: ignore 
                dezimalstellen = int(str(formelElement.get("dezimalstellen"))) # type: ignore 
            self.erfuellteAuswertungsregel = -1
            if str(formelElement.get("typ")) != "script": # type: ignore  
                formel = str(formelElement.text) # type: ignore 
                variablenElement = berechnungElement.find("variablen") # type: ignore
                variablen = {}
                for variableElement in variablenElement.findall("variable"): # type: ignore
                    variablenname = str(variableElement.get("name"))
                    # Ohne Bedingung
                    if variableElement.find("bedingung") == None:
                        text = str(variableElement.text)
                        textMitIdWertErsetzt = self.ersetzeIdVariablen(text)
                        textMitVarWertErsezt = self.ersetzeVariablen(variablen, textMitIdWertErsetzt)
                        variablen[variablenname] = str(self.berechnung(textMitVarWertErsezt, -1))
                    # Mit Bedinung(en)
                    else: 
                        for bedingungElement in variableElement.findall("bedingung"):
                            regelErfuellt = True
                            for regelElement in bedingungElement.findall("regel"):
                                regel = str(regelElement.text)
                                regelMitIdWertErsetzt = self.ersetzeIdVariablen(regel)
                                regelMitVarWertErsetzt = self.ersetzeVariablen(variablen, regelMitIdWertErsetzt)
                                if not self.regelIstErfuellt(regelMitVarWertErsetzt):
                                    regelErfuellt = False
                            if regelErfuellt:
                                logger.logger.info("Regel " + regel + " erfüllt")
                                wert = str(bedingungElement.find("wert").text) # type: ignore
                                wertMitIdWertErsetzt = self.ersetzeIdVariablen(wert)
                                wertMitVarWertErsetzt = self.ersetzeVariablen(variablen, wertMitIdWertErsetzt)
                                variablen[variablenname] = wertMitVarWertErsetzt
                patternVar = r"\$var{[^{}]+}"
                variablenMitNichtErfuelltenRegeln = []
                ergebnis = 0
                formelMitZahlen = formel
                varVariablen = re.findall(patternVar, formel)
                for varVariable in varVariablen:
                    varName = varVariable[5:-1]
                    if varName in variablen:
                        formelMitZahlen = formelMitZahlen.replace(varVariable, variablen[varName])
                    else:
                        logger.logger.warning("Variablenname " + varName + " nicht ausgelesen")
                        variablenMitNichtErfuelltenRegeln.append(varName)
                formelMitZahlen = self.ersetzeIdVariablen(formelMitZahlen)
                ergebnis = self.berechnung(formelMitZahlen, dezimalstellen)
                logger.logger.info("Teilergebnis: " + str(self.berechnung(formelMitZahlen, dezimalstellen)))
                if len(variablenMitNichtErfuelltenRegeln) == 0:
                    self.lineEditScoreErgebnis.setText(str(ergebnis).replace(".", ","))
                    logger.logger.info("Endergebnis: " + str(ergebnis).replace(".", ","))
                    # Auswertung
                    self.auswertung(ergebnis)
                else:
                    mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Der Score kann nicht berechnet werden, da für die folgenden Variablen keine Regel zutrifft:\n- " + str.join("\n- ", variablenMitNichtErfuelltenRegeln), QMessageBox.StandardButton.Ok)
                    mb.exec()
                # PDF-Alternative
                self.pdfZeilen = []
                pdfElement = self.scoreRoot.find("pdf") # type: ignore
                if pdfElement != None: # type: ignore
                    for zeileElement in pdfElement.findall("zeile"):
                        titel = str(zeileElement.get("titel"))
                        if titel == "None":
                            titel = self.getPart(str(zeileElement.get("partid"))).getTitel() # type: ignore
                        wert = variablen[str(zeileElement.text)]
                        einheit = str(zeileElement.get("einheit"))
                        if wert == "1" and einheit == "Punkte":
                            einheit = "Punkt"
                        self.pdfZeilen.append((titel, wert, einheit))
            elif str(formelElement.text) == "dvo2023": # type: ignore
                logger.logger.info("dvo2023 gewählt")
                risikofaktorBezeichnungen = ["Wirbelfrakturen", "Andere Frakturen", "Allgemeine Risikofaktoren", "Rheumatologie und Glukokortikoide", "Sturzrisiko assoziierte Risikofaktoren/Geriatrie", "Endokrinologie", "Weitere Erkraknungen/Medikationen", "TBS"]
                indikationstabelleFrau3 = {
                    0.0: [13, 8, 6, 4, 3, 2.3, 1.8, 1.5, 1.2],
                    0.5: [9, 6, 4, 3, 2.2, 1.7, 1.3, 1.1, -3],
                    1.0: [7, 5, 3, 2.3, 1.6, 1.2, -3, -3, -5],
                    1.5: [5, 3.5, 2.4, 1.7, 1.2, -3, -3, -5, -5],
                    2.0: [4, 2.6, 1.8, 1.2, -3, -3, -5, -5, -10],
                    2.5: [3, 1.9, 1.3, -3, -3, -5, -5, -10, -10],
                    3.0: [2.1, 1.4, -3, -5, -5, -5, -10, -10, -10],
                    3.5: [1.5, -3, -5, -5, -10, -10, -10, -10, -10],
                    4.0: [-3, -5, -5, -10, -10, -10, -10, -10, -10]
                }
                indikationstabelleFrau5 = {
                    0.0: [21, 14, 10, 7, 5, 4, 3, 2.4, 2],
                    0.5: [16, 10, 7, 5, 4, 3, 2.2, 1.8, 1.4],
                    1.0: [12, 8, 5, 4, 2.7, 2.1, 1.6, 1.3, -5],
                    1.5: [9, 6, 4, 3, 2, 1.5, 1.2, -5, -5],
                    2.0: [6, 4, 3, 2.1, 1.5, 1.1, -5, -5, -10],
                    2.5: [5, 3, 2.2, 1.5, 1.1, -5, -5, -10, -10],
                    3.0: [3.5, 2.3, 1.6, -5, -5, -5, -10, -10, -10],
                    3.5: [2.5, 1.7, -5, -5, -10, -10, -10, -10, -10],
                    4.0: [2, -5, -5, -10, -10, -10, -10, -10, -10]
                }
                indikationstabelleFrau10 = {
                    0.0: [42, 28, 19, 14, 10, 8, 6, 5, 4],
                    0.5: [31, 21, 14, 10, 7, 6, 4.4, 3.6, 3],
                    1.0: [23, 16, 11, 7.5, 5.5, 4.2, 3.2, 2.6, 2.1],
                    1.5: [17, 12, 8, 6, 4.1, 3.1, 2.4, 1.9, 1.5],
                    2.0: [13, 9, 6, 4, 3, 2.2, 1.7, 1.3, -10],
                    2.5: [9, 6, 4.4, 3.1, 2.2, 1.6, 1.3, -10, -10],
                    3.0: [7, 5, 3.2, 2.3, 1.6, 1.2, -10, -10, -10],
                    3.5: [5, 3.5, 2.4, 1.7, -10, -10, -10, -10, -10],
                    4.0: [3.7, 2.5, 1.7, -10, -10, -10, -10, -10, -10]
                }
                indikationstabelleMann3 = {
                    0.0: [10, 8, 6, 5, 4, 3, 2.4, 2, 1.4],
                    0.5: [7, 5, 4, 3, 2.5, 2, 1.6, 1.3, -3],
                    1.0: [5, 3.7, 2.8, 2.2, 1.7, 1.4, 1.1, -3, -5],
                    1.5: [3.4, 2.5, 1.9, 1.5, 1.1, -3, -3, -5, -5],
                    2.0: [2.3, 1.7, 1.3, -3, -3, -5, -5, -5, -10],
                    2.5: [1.6, 1.2, -3, -5, -5, -5, -10, -10, -10],
                    3.0: [1.1, -5, -5, -5, -10, -10, -10, -10, -10],
                    3.5: [-5, -5, -10, -10, -10, -10, -10, -10, -10],
                    4.0: [-5, -10, -10, -10, -10, -10, -10, -10, -10]
                }
                indikationstabelleMann5 = {
                    0.0: [17, 13, 10, 8, 6, 4, 3, 3.3, 2.4],
                    0.5: [12, 9, 7, 5, 4, 3.4, 2.7, 2.1, 1.5],
                    1.0: [8, 6, 5, 3.6, 2.8, 2.3, 1.8, 1.4, -5],
                    1.5: [6, 4, 3.2, 2.4, 1.9, 1.5, 1.2, -5, -5],
                    2.0: [4, 2.9, 2.2, 1.6, 1.3, -5, -5, -5, -10],
                    2.5: [2.6, 2, 1.5, -5, -5, -5, -10, -10, -10],
                    3.0: [1.8, -5, -5, -5, -10, -10, -10, -10, -10],
                    3.5: [-5, -5, -10, -10, -10, -10, -10, -10, -10],
                    4.0: [-5, -10, -10, -10, -10, -10, -10, -10, -10]
                }
                indikationstabelleMann10 = {
                    0.0: [33, 26, 20, 16, 12, 10, 8, 7, 5],
                    0.5: [23, 18, 14, 11, 8, 7, 5, 4, 3],
                    1.0: [16, 12, 9, 7, 6, 4.5, 3.6, 2.8, 2],
                    1.5: [11, 8, 6, 5, 4, 3, 2.4, 1.8, 1.3],
                    2.0: [8, 6, 4, 3, 2.5, 2, 1.6, 1.2, -10],
                    2.5: [5, 4, 3, 2.2, 1.7, 1.3, -10, -10, -10],
                    3.0: [3.6, 2.6, 1.9, 1.5, -10, -10, -10, -10, -10],
                    3.5: [2.5, 1.8, -10, -10, -10, -10, -10, -10, -10],
                    4.0: [1.7, -10, -10, -10, -10, -10, -10, -10, -10]
                }
                indikationstabellenFrau = [indikationstabelleFrau10, indikationstabelleFrau5, indikationstabelleFrau3]
                indikationstabllenMann = [indikationstabelleMann10, indikationstabelleMann5, indikationstabelleMann3]
                maxJePart = {} # key: partId, value: Tupel (höchster Faktor des Parts, sgRisiko)
                for widget in self.widgets:
                    partId = int(widget.getPartId())
                    if partId < 8:
                        wert = self.getWertAusWidgetId(widget.getId()).replace(",", ".")
                        sgRisiko = ""
                        if wert[-1] == "S" or wert[-1] == "G":
                            sgRisiko = wert[-1]
                            wert = wert[:-1]
                        wertFloat = float(wert)
                        if not partId in maxJePart or maxJePart[partId][0] < wertFloat:
                            maxJePart[partId] = (wertFloat, sgRisiko)
                sortiert = sorted(maxJePart.items(), key=lambda x:x[1][0], reverse=True)
                maxJePartSortiert = dict(sortiert) # maxJePart nach höchstem Faktor sortiert (höchster zuerst)
                zweiHoechsteFaktoren = []
                sRisiko = False
                gRisiko = False
                for max in maxJePartSortiert:
                    faktor = maxJePartSortiert[max][0] 
                    sgRisiko = maxJePartSortiert[max][1]
                    if len(zweiHoechsteFaktoren) < 2:
                        if not sRisiko and not gRisiko:
                            zweiHoechsteFaktoren.append(faktor)
                        elif sgRisiko == "S" and not sRisiko:
                            zweiHoechsteFaktoren.append(faktor)
                            sRisiko = True
                        elif sgRisiko == "G" and not gRisiko:
                            zweiHoechsteFaktoren.append(faktor)
                            gRisiko = True
                    else:
                        break
                faktoren = [zweiHoechsteFaktoren[0], zweiHoechsteFaktoren[0] * zweiHoechsteFaktoren[1]]
                logger.logger.info("Zwei höchste Faktoren: " + str(zweiHoechsteFaktoren))
                tScore = float(self.getWertAusWidgetId("150").replace(",", "."))
                tScoreGerundet = round(tScore * 2) / 2
                alter = float(self.getWertAusWidgetId("151"))
                alterGerundet = round(alter / 10 * 2) / 2 * 10
                geschlecht = 2
                if self.getWertAusWidgetId("152") == "1":
                    geschlecht = 1
                risikoListe = [10, 5, 3]
                therapieindikationsschwelleProzent = 0
                for i in range(3):
                    risiko = risikoListe[i]
                    indikationstabelle = indikationstabellenFrau[i]
                    if geschlecht == 1:
                        indikationstabelle = indikationstabllenMann[i]
                    tabellenErebnis = indikationstabelle[tScoreGerundet * -1][int((alterGerundet - 50) / 5)]
                    logger.logger.info("Tabellenergebnis " + str(risiko) + "%: " + str(tabellenErebnis))
                    for faktor in faktoren:
                        logger.logger.info("Faktor: " + str(faktor))
                        if faktor >= tabellenErebnis:
                            therapieindikationsschwelleProzent = risiko
                            break
                    if therapieindikationsschwelleProzent != 0:
                        break
                logger.logger.info("Therapieindikationsschwelle: " + str(therapieindikationsschwelleProzent) + "%")
                self.lineEditScoreErgebnis.setText(str(therapieindikationsschwelleProzent))
                self.auswertung(therapieindikationsschwelleProzent)
            # except Exception as e:
            #     logger.logger.error("Fehler bei der Score-Berechung: " + str(e))
            #     mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Fehler bei der Score-Berechung: " + str(e), QMessageBox.StandardButton.Ok)
            #     mb.exec()

    def auswertung(self, ergebnis):
        """
            Wertet ein Ergebnis aus, falls möglich und färbt die Auswertungsbeschreibungen grün
            Parameter:
                ergebnis
        """
        auswertungElement = self.scoreRoot.find("auswertung") # type: ignore
        if auswertungElement != None:
            # Alle Auswertungslabel Normalfarbe
            for i in range(len(self.labelErgebnisbereiche)):
                self.labelErgebnisbereiche[i].setPalette(farbe.getTextPalette(farbe.farben.NORMAL, self.palette()))
                self.labelBeschreibungen[i].setPalette(farbe.getTextPalette(farbe.farben.NORMAL, self.palette()))
        if auswertungElement != None and ergebnis != "":
            ergebnis = str(ergebnis).replace(",", ".")
            beurteilungNr = 0
            for beurteilungElement in auswertungElement.findall("beurteilung"):
                regelErfuellt = True
                for regelElement in beurteilungElement.findall("regel"):
                    # Ggf. Altersregel prüfen
                    altersregelErfuellt = True
                    if regelElement.get("altersid") != None and regelElement.get("altersregel") != None:
                        alter = self.getWertAusWidgetId(str(regelElement.get("altersid")))
                        altersregel = str(regelElement.get("altersregel"))
                        altersregelErfuellt = self.regelIstErfuellt(alter + altersregel)
                    if altersregelErfuellt:
                        regel = ergebnis + str(regelElement.text)
                        if not self.regelIstErfuellt(regel):
                            regelErfuellt = False
                            break
                if regelErfuellt:
                    self.erfuellteAuswertungsregel = beurteilungNr
                    break
                beurteilungNr += 1
            if self.erfuellteAuswertungsregel != -1:
                for i in range(len(self.labelErgebnisbereiche)):
                    if self.erfuellteAuswertungsregel == i:
                        self.labelErgebnisbereiche[i].setPalette(farbe.getTextPalette(farbe.farben.GRUEN, self.palette()))
                        self.labelBeschreibungen[i].setPalette(farbe.getTextPalette(farbe.farben.GRUEN, self.palette()))

    def lineEditScoreErgebnisTextChanged(self):
        if self.labelScoreErgebnisEinheit.text()[:5] == "Punkt":
            if self.lineEditScoreErgebnis.text() == "1":
                self.labelScoreErgebnisEinheit.setText("Punkt")
            else:
                self.labelScoreErgebnisEinheit.setText("Punkte")
    
    def dateEditUntersuchungsdatumChanged(self, datum):
        self.untersuchungsdatum = datum

    def comboBoxBenutzerIndexChanged(self, index):
        self.aktuelleBenuztzernummer = index

    def fuerGdtBereinigen(self, string:str):
        """
        Ersetzt GDT-unlesbare Unicodezeichen
        Parameter:
            string:str
        Return:
            Ersetzter String
        """
        ersetzt = string
        zuErsetzendeStrings = {
            "\u2082" : "2",
            "\u00b2" : "2",
            "\u2264" : "<=",
            "\u2265" : ">=",
            "\r\n": " "
        }
        for zuErsetzen in zuErsetzendeStrings:
            ersetzt = ersetzt.replace(zuErsetzen, zuErsetzendeStrings[zuErsetzen])
        return ersetzt
            
    def pushButtonSendenClicked(self):
        if self.lineEditScoreErgebnis.text() != "":
            logger.logger.info("Daten senden geklickt")
            self.pdferzeugen = self.checkBoxPdfErzeugen.isChecked()
            # GDT-Datei erzeugen
            sh = gdt.SatzHeader(gdt.Satzart.DATEN_EINER_UNTERSUCHUNG_UEBERMITTELN_6310, self.configIni["GDT"]["idpraxisedv"], self.configIni["GDT"]["idscoregdt"], self.zeichensatz, "2.10", "Fabian Treusch - GDT-Tools", "ScoreGDT", self.version, self.patId)
            gd = gdt.GdtDatei()
            logger.logger.info("GdtDatei-Instanz erzeugt")
            gd.erzeugeGdtDatei(sh.getSatzheader())
            logger.logger.info("Satzheader 6310 erzeugt")
            untersuchungsdatum = "{:>02}".format(str(self.dateEditUntersuchungsdatum.date().day())) + "{:>02}".format(str(self.dateEditUntersuchungsdatum.date().month())) + str(self.dateEditUntersuchungsdatum.date().year())
            jetzt = QTime().currentTime()
            uhrzeit = "{:>02}".format(str(jetzt.hour())) + "{:>02}".format(str(jetzt.minute())) + str(jetzt.second())
            logger.logger.info("Untersuchungsdatum/ -uhrzeit festgelegt")
            gd.addZeile("6200", untersuchungsdatum)
            gd.addZeile("6201", uhrzeit)
            gd.addZeile("8402", "ALLG00")
            gdtname = str(self.scoreRoot.get("name")) # type: ignore
            if self.scoreRoot.get("gdtname") != None: # type: ignore
                gdtname = str(self.scoreRoot.get("gdtname")) # type: ignore
            # PDF erzeugen
            pdf = None
            if self.pdferzeugen:
                logger.logger.info("PDF-Erzeugung aktiviert")
                gd.addZeile("6302", "scorepdf")
                gd.addZeile("6303", "pdf")
                gd.addZeile("6304", gdtname) # type: ignore
                gd.addZeile("6305", os.path.join(basedir, "pdf/score_temp.pdf"))
                # PDF erzeugen
                pdf = scorepdf.scorepdf("P", "mm", "A4", str(self.scoreRoot.get("name"))) # type: ignore
                logger.logger.info("FPDF-Instanz erzeugt")
                pdf.add_page()
                pdf.set_font("dejavu", "", 14)
                pdf.cell(0, 10, "von " + self.name + " (* " + self.geburtsdatum + ")", align="C", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("dejavu", "", 10)
                untdat = "{:>02}".format(str(self.untersuchungsdatum.day())) + "." + "{:>02}".format(str(self.untersuchungsdatum.month())) + "." + str(self.untersuchungsdatum.year())
                einrichtung = ""
                if self.einrichtunguebernehmen:
                    einrichtung = " von " + self.einrichtungsname
                pdf.cell(0, 6, "Erstellt am " + untdat + einrichtung, align="C", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 8, new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("dejavu", "", 10)
                pdf.set_fill_color(240, 240, 240)
                
            # Tests
            if str(self.scoreRoot.get("keineTestuebermittlung")) != "True": # type: ignore
                i = 0
                for widget in self.widgets:
                    test = None
                    if widget.getTyp() == class_widgets.WidgetTyp.LINEEDIT:
                        test = gdt.GdtTest("ScoreGDT" + "_" + widget.getId(), self.fuerGdtBereinigen(widget.getTitel()), widget.getWertOhneFaktor().replace(".", ",").replace(",0", ""), widget.getEinheit(self.einheitToggles)) # type: ignore
                    elif widget.getTyp() == class_widgets.WidgetTyp.RADIOBUTTON:
                        if widget.getQt().isChecked():
                            partId = widget.getPartId()
                            part = self.getPart(partId)
                            test = gdt.GdtTest("ScoreGDT" + "_" + widget.getId(), self.fuerGdtBereinigen(part.getTitel()), self.fuerGdtBereinigen(widget.getTitel()), self.fuerGdtBereinigen(widget.getEinheit())) # type: ignore
                    elif widget.getTyp() == class_widgets.WidgetTyp.COMBOBOX:
                        test = gdt.GdtTest("ScoreGDT" + "_" + widget.getId(), self.fuerGdtBereinigen(widget.getTitel()), self.fuerGdtBereinigen(widget.getItemText(widget.getQt().currentIndex())), self.fuerGdtBereinigen(widget.getEinheit())) # type: ignore
                    elif widget.getTyp() == class_widgets.WidgetTyp.CHECKBOX:
                        wert = "0"
                        if widget.getQt().isChecked():
                            wert = widget.getWert().replace(".", ",").replace(",0", "")
                        if wert == "0":
                            wert = "Nein"
                        elif wert == "1":
                            wert = "Ja"
                        test = gdt.GdtTest("ScoreGDT" + "_" + widget.getId(), self.fuerGdtBereinigen(widget.getTitel()), wert, self.fuerGdtBereinigen(widget.getEinheit())) # type: ignore
                    else:
                        test = gdt.GdtTest("ScoreGDT" + "_" + widget.getId(), self.fuerGdtBereinigen(widget.getTitel()), widget.getWert().replace(".", ",").replace(",0", ""), self.fuerGdtBereinigen(widget.getEinheit())) # type: ignore
                    if test != None:
                        gd.addTest(test)
                        if self.pdferzeugen and pdf != None and len(self.pdfZeilen) == 0: # type: ignore
                            y1 = pdf.get_y()
                            pdf.multi_cell(140, 8, test.getTest()["8411_testBezeichnung"], fill=(i % 2 == 0))
                            y2 = pdf.get_y()
                            if y2 < y1: # Neue Seite
                                y1 = 20
                            pdf.set_xy(150, y1)
                            testergebnis = test.getTest()["8420_testErgebnis"]
                            leerzeilen = ""
                            anzahlLeerzeilen = int((y2 - y1) / 8)
                            for j in range(anzahlLeerzeilen - 1):
                                leerzeilen += "\n "
                            pdf.multi_cell(50, 8, testergebnis + " " + test.getTest()["8421_testEinheit"], align="R", new_x="LMARGIN", new_y="NEXT", fill=(i % 2 == 0))
                            y3 = pdf.get_y()
                            if y3 < y2:
                                pdf.set_x(150)
                                pdf.cell(50, y2 - y3, "", fill=(i % 2 == 0), new_x="LMARGIN", new_y="NEXT")
                                #pdf.set_y(y3 + 10 * anzahlLeerzeilen)
                            elif y3 > y2:
                                pdf.set_y(y2)
                                pdf.cell(140, y3 - y2, "", fill=(i % 2 == 0), new_x="LMARGIN", new_y="NEXT")
                            i += 1
            # PDF-Alternative
            if pdf != None and len(self.pdfZeilen) > 0:
                i = 0
                for pdfZeile in self.pdfZeilen:
                    pdf.cell(0, 10, str(pdfZeile[0]), fill=(i % 2 == 0))
                    pdf.cell(0, 10, str(pdfZeile[1]) + " " + str(pdfZeile[2]), align="R", new_x="LMARGIN", new_y="NEXT", fill=(i % 2 == 0))
                    i += 1
            leerzeichenVorEinheit = " "
            if self.labelScoreErgebnisEinheit.text() == "%":
                leerzeichenVorEinheit = ""
            auswertung = "-"
            if self.erfuellteAuswertungsregel != -1:
                auswertung = self.labelBeschreibungen[self.erfuellteAuswertungsregel].text()
            if self.pdferzeugen and pdf != None:
                pdf.set_font(style="B")
                pdf.cell(90, 8, "Ergebnis:", border="T")
                pdf.cell(0, 8, self.lineEditScoreErgebnis.text() + leerzeichenVorEinheit + self.labelScoreErgebnisEinheit.text(), border="T", align="R", new_x="LMARGIN", new_y="NEXT")
                if self.erfuellteAuswertungsregel != -1:
                    pdf.cell(0, 8, new_x="LMARGIN", new_y="NEXT")
                    pdf.cell(0, 8, "Auswertung/Interpretation:", new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font(style="")  
                    pdf.cell(0, 8, auswertung, new_x="LMARGIN", new_y="NEXT")
                pdf.set_y(-30)
                pdf.set_font("dejavu", "I", 10)
                pdf.cell(0, 8, "Generiert von ScoreGDT V" + self.version + " (\u00a9 GDT-Tools " + str(datetime.date.today().year) + ")", align="R")
                logger.logger.info("PDF-Seite aufgebaut")
                try:
                    pdf.output(os.path.join(basedir, "pdf/score_temp.pdf"))
                    logger.logger.info("PDF-Output nach " + os.path.join(basedir, "pdf/score_temp.pdf") + " erfolgreich")
                except:
                    logger.logger.error("Fehler bei PDF-Output nach " + os.path.join(basedir, "pdf/score_temp.pdf"))
            befund = gdtname + ": " +  self.lineEditScoreErgebnis.text() + leerzeichenVorEinheit + self.labelScoreErgebnisEinheit.text() # type: ignore
            gd.addZeile("6220", befund)
            if self.erfuellteAuswertungsregel != -1:
                gd.addZeile("6220", "Beurteilung: " + auswertung)
            gd.addZeile("6227", "Dokumentiert von: " + self.benutzerkuerzelListe[self.aktuelleBenuztzernummer])
            # GDT-Datei exportieren
            if not gd.speichern(os.path.join(self.gdtExportVerzeichnis, self.kuerzelpraxisedv + self.kuerzelscoregdt + ".gdt"), self.zeichensatz):
                logger.logger.error("Fehler bei GDT-Dateiexport nach " + self.gdtExportVerzeichnis + "/" + self.kuerzelpraxisedv + self.kuerzelscoregdt + ".gdt")
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "GDT-Export nicht möglich.\nBitte überprüfen Sie die Angabe des Exportverzeichnisses.", QMessageBox.StandardButton.Ok)
                mb.exec()
            else: 
                self.configIni["Allgemein"]["pdferzeugen"] = str(self.pdferzeugen)
                self.configIni["Benutzer"]["letzter"] = str(self.aktuelleBenuztzernummer)
                try:
                    with open(os.path.join(self.configPath, "config.ini"), "w", encoding="utf-8") as configfile:
                        self.configIni.write(configfile)
                except:
                    logger.logger.warning("Problem beim Speichern von Benutzer/letzter")
                # trends.xml aktualisieren
                if self.trendverzeichnis != "" and os.path.exists(self.trendverzeichnis):
                    test = class_trends.Test(str(self.scoreRoot.get("name")), str(self.scoreRoot.get("gruppe")), class_trends.GdtTool.SCOREGDT) # type: ignore
                    trend = class_trends.Trend(datetime.datetime(self.untersuchungsdatum.year(), self.untersuchungsdatum.month(), self.untersuchungsdatum.day(), datetime.datetime.now().hour, datetime.datetime.now().minute, datetime.datetime.now().second), self.lineEditScoreErgebnis.text() + leerzeichenVorEinheit + self.labelScoreErgebnisEinheit.text(), auswertung)
                    if not os.path.exists(os.path.join(self.trendverzeichnis, self.patId)):
                        os.mkdir(self.trendverzeichnis + os.path.sep + self.patId, 0o777)
                        logger.logger.info("Trendverzeichnis für PatId " + self.patId + " erstellt")
                    try:
                        class_trends.aktualisiereXmlDatei(test, trend, os.path.join(self.trendverzeichnis, self.patId, "trends.xml"))
                        logger.logger.info("trends.xml aktualisiert")
                    except class_trends.XmlPfadExistiertNichtError as e:
                        logger.logger.info(e)
                        test.addTrend(trend)
                        test.speichereAlsNeueXmlDatei(os.path.join(self.trendverzeichnis, self.patId, "trends.xml"))
                    except class_trends.TrendError as e:
                        mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Fehler beim Aktualisieren/Speichern der Trenddaten: " + e.message, QMessageBox.StandardButton.Ok)
                        mb.exec()
                elif self.trendverzeichnis != "" and not os.path.exists(self.trendverzeichnis):
                    logger.logger.warning("Trendverzeichnis " + self.trendverzeichnis + " nicht erreichbar")
                sys.exit()
        else:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Vor dem Senden der Daten muss ein Score berechnet werden.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def updatePruefung(self, meldungNurWennUpdateVerfuegbar = False):
        logger.logger.info("Updateprüfung")
        response = requests.get("https://api.github.com/repos/retconx/scoregdt/releases/latest")
        githubRelaseTag = response.json()["tag_name"]
        latestVersion = githubRelaseTag[1:] # ohne v
        if versionVeraltet(self.version, latestVersion):
            logger.logger.info("Bisher: " + self.version + ", neu: " + latestVersion)
            if os.path.exists(self.updaterpfad):
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von ScoreGDT", "Die aktuellere ScoreGDT-Version " + latestVersion + " ist auf Github verfügbar.\nSoll der GDT-Tools Updater geladen werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    logger.logger.info("Updater wird geladen")
                    atexit.register(self.updaterLaden)
                    sys.exit()
            else:
                mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von ScoreGDT", "Die aktuellere ScoreGDT-Version " + latestVersion + " ist auf <a href='https://github.com/retconx/scoregdt/releases'>Github</a> verfügbar.<br />Bitte beachten Sie auch die Möglichkeit, den Updateprozess mit dem <a href='https://github.com/retconx/gdttoolsupdater/wiki'>GDT-Tools Updater</a> zu automatisieren.", QMessageBox.StandardButton.Ok)
                mb.setTextFormat(Qt.TextFormat.RichText)
                mb.exec()
        elif not meldungNurWennUpdateVerfuegbar:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Sie nutzen die aktuelle ScoreGDT-Version.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def updaterLaden(self):
        sex = sys.executable
        programmverzeichnis = ""
        logger.logger.info("sys.executable: " + sex)
        if "win32" in sys.platform:
            programmverzeichnis = sex[:sex.rfind("scoregdt.exe")]
        elif "darwin" in sys.platform:
            programmverzeichnis = sex[:sex.find("ScoreGDT.app")]
        elif "linux" in sys.platform:
            programmverzeichnis = sex[:sex.rfind("scoregdt")]
        logger.logger.info("Programmverzeichnis: " + programmverzeichnis)
        try:
            if "win32" in sys.platform:
                subprocess.Popen([self.updaterpfad, "scoregdt", self.version, programmverzeichnis], creationflags=subprocess.DETACHED_PROCESS) # type: ignore
            elif "darwin" in sys.platform:
                subprocess.Popen(["open", "-a", self.updaterpfad, "--args", "scoregdt", self.version, programmverzeichnis])
            elif "linux" in sys.platform:
                subprocess.Popen([self.updaterpfad, "scoregdt", self.version, programmverzeichnis])
        except Exception as e:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Der GDT-Tools Updater konnte nicht gestartet werden", QMessageBox.StandardButton.Ok)
            logger.logger.error("Fehler beim Starten des GDT-Tools Updaters: " + str(e))
            mb.exec()

    def autoUpdatePruefung(self, checked):
        self.autoupdate = checked
        self.configIni["Allgemein"]["autoupdate"] = str(checked)
        with open(os.path.join(self.configPath, "config.ini"), "w") as configfile:
            self.configIni.write(configfile)

    def ueberScoreGdt(self):
        de = dialogUeberScoreGdt.UeberScoreGdt()
        de.exec()

    def eula(self):
        QDesktopServices.openUrl("https://gdttools.de/Lizenzvereinbarung_ScoreGDT.pdf")

    def logExportieren(self):
        if (os.path.exists(os.path.join(basedir, "log"))):
            downloadPath = ""
            if sys.platform == "win32":
                downloadPath = os.path.expanduser("~\\Downloads")
            else:
                downloadPath = os.path.expanduser("~/Downloads")
            try:
                if shutil.copytree(os.path.join(basedir, "log"), os.path.join(downloadPath, "Log_ScoreGDT"), dirs_exist_ok=True):
                    shutil.make_archive(os.path.join(downloadPath, "Log_ScoreGDT"), "zip", root_dir=os.path.join(downloadPath, "Log_ScoreGDT"))
                    shutil.rmtree(os.path.join(downloadPath, "Log_ScoreGDT"))
                    mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Das Log-Verzeichnis wurde in den Ordner " + downloadPath + " kopiert.", QMessageBox.StandardButton.Ok)
                    mb.exec()
            except Exception as e:
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Problem beim Download des Log-Verzeichnisses: " + str(e), QMessageBox.StandardButton.Ok)
                mb.exec()
        else:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Das Log-Verzeichnis wurde nicht gefunden.", QMessageBox.StandardButton.Ok)
            mb.exec() 

    def scoreAuswaehlen(self, checked):
        appName = sys.argv[0]
        sys.argv.clear()
        sys.argv.append(appName)
        os.execl(sys.executable, __file__, *sys.argv)

    def scoreGdtNameInClipboard(self, checked):
        gdtname = str(self.scoreRoot.get("name")) # type: ignore
        if self.scoreRoot.get("gdtname") != None: # type: ignore
            gdtname = str(self.scoreRoot.get("gdtname")) # type: ignore
        clipboard = QClipboard()
        clipboard.setText("stsc:" + gdtname.replace(" ", "_").replace("(", "{").replace(")", "}"))
        mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von ScoreGDT", "\"" + "stsc:" + gdtname.replace(" ", "_").replace("(", "{").replace(")", "}") + "\" wurde in die Zwischenablage kopiert und kann als Startargument verwendet werden.", QMessageBox.StandardButton.Ok)
        mb.exec()

    def scoreFavoritenVerwalten(self, checked):
        df = dialogEinstellungenFavoriten.EinstellungenFavoriten(self.configPath, self.scoresPfad)
        df.exec()   

    def einstellungenAllgemein(self, checked, neustartfrage):
        de = dialogEinstellungenAllgemein.EinstellungenAllgemein(self.configPath, self.root, self.standardscore)
        if de.exec() == 1:
            self.configIni["Allgemein"]["einrichtungsname"] = de.lineEditEinrichtungsname.text()
            self.configIni["Allgemein"]["einrichtunguebernehmen"] = str(de.checkBoxEinrichtungUebernehmen.isChecked())
            self.configIni["Allgemein"]["bereichsgrenzenerzwingen"] = str(de.checkBoxZahlengrenzenpruefung.isChecked())
            self.configIni["Allgemein"]["standardscore"] = de.comboBoxScoreAuswahl.currentText()
            self.configIni["Allgemein"]["trendverzeichnis"] = de.lineEditTrendverzeichnis.text()
            self.configIni["Allgemein"]["updaterpfad"] = de.lineEditUpdaterPfad.text()
            self.configIni["Allgemein"]["autoupdate"] = str(de.checkBoxAutoUpdate.isChecked())
            with open(os.path.join(self.configPath, "config.ini"), "w", encoding="utf-8") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von ScoreGDT", "Damit die Einstellungsänderungen wirksam werden, sollte ScoreGDT neu gestartet werden.\nSoll ScoreGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)

    def einstellungenGdt(self, checked, neustartfrage):
        de = dialogEinstellungenGdt.EinstellungenGdt(self.configPath)
        if de.exec() == 1:
            self.configIni["GDT"]["idscoregdt"] = de.lineEditScoreGdtId.text()
            self.configIni["GDT"]["idpraxisedv"] = de.lineEditPraxisEdvId.text()
            self.configIni["GDT"]["gdtimportverzeichnis"] = de.lineEditImport.text()
            self.configIni["GDT"]["gdtexportverzeichnis"] = de.lineEditExport.text()
            self.configIni["GDT"]["kuerzelscoregdt"] = de.lineEditScoreGdtKuerzel.text()
            self.configIni["GDT"]["kuerzelpraxisedv"] = de.lineEditPraxisEdvKuerzel.text()
            self.configIni["GDT"]["zeichensatz"] = str(de.aktuelleZeichensatznummer + 1)
            with open(os.path.join(self.configPath, "config.ini"), "w", encoding="utf-8") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von ScoreGDT", "Damit die Einstellungsänderungen wirksam werden, sollte ScoreGDT neu gestartet werden.\nSoll ScoreGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)

    def einstellungenBenutzer(self, checked, neustartfrage):
        de = dialogEinstellungenBenutzer.EinstellungenBenutzer(self.configPath)
        if de.exec() == 1:
            namen = []
            kuerzel = []
            for i in range(self.maxBenutzeranzahl):
                if de.lineEditNamen[i].text() != "":
                    namen.append(de.lineEditNamen[i].text())
                    kuerzel.append(de.lineEditKuerzel[i].text())
            self.configIni["Benutzer"]["namen"] = "::".join(namen)
            self.configIni["Benutzer"]["kuerzel"] = "::".join(kuerzel)
            with open(os.path.join(self.configPath, "config.ini"), "w", encoding="utf-8") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von ScoreGDT", "Damit die Einstellungsänderungen wirksam werden, sollte ScoreGDT neu gestartet werden.\nSoll ScoreGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)

    ## Nur mit Lizenz
    def einstellungenLanrLizenzschluessel(self, checked, neustartfrage):
        de = dialogEinstellungenLanrLizenzschluessel.EinstellungenProgrammerweiterungen(self.configPath)
        if de.exec() == 1:
            self.configIni["Erweiterungen"]["lanr"] = de.lineEditLanr.text()
            self.configIni["Erweiterungen"]["lizenzschluessel"] = gdttoolsL.GdtToolsLizenzschluessel.krypt(de.lineEditLizenzschluessel.text())
            with open(os.path.join(self.configPath, "config.ini"), "w", encoding="utf-8") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von ScoreGDT", "Damit die Einstellungsänderungen wirksam werden, sollte ScoreGDT neu gestartet werden.\nSoll ScoreGDT  jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)

    def einstellungenImportExport(self):
        de = dialogEinstellungenImportExport.EinstellungenImportExport(self.configPath)
        if de.exec() == 1:
            pass
    ## /Nur mit Lizenz
    
    def scoregdtWiki(self, link):
        QDesktopServices.openUrl("https://github.com/retconx/scoregdt/wiki")

    def gdtToolsLinkGeklickt(self, link):
        QDesktopServices.openUrl(link)
    
app = QApplication(sys.argv)
qt = QTranslator()
filename = "qtbase_de"
directory = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
qt.load(filename, directory)
app.installTranslator(qt)
app.setWindowIcon(QIcon(os.path.join(basedir, "icons", "program.png")))
window = MainWindow()
window.show()
app.exec()
