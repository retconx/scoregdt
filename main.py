import sys, configparser, os, datetime, shutil, logger, re
from enum import Enum
import xml.etree.ElementTree as ElementTree
## Nur mit Lizenz
import gdttoolsL
## /## Nur mit Lizenz
import gdt, gdtzeile, class_part, class_widgets
import dialogUeberScoreGdt, dialogEinstellungenAllgemein, dialogEinstellungenGdt, dialogEinstellungenBenutzer, dialogEinstellungenLanrLizenzschluessel, dialogEula, dialogEinstellungenImportExport, class_enums,dialogScoreAuswahl
from PySide6.QtCore import Qt, QTranslator, QLibraryInfo, QDate, QTime
from PySide6.QtGui import QFont, QAction, QIcon, QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QGroupBox,
    QFrame,
    QHBoxLayout,
    QGridLayout,
    QWidget,
    QLabel, 
    QLineEdit,
    QDateEdit,
    QMessageBox,
    QPushButton,
    QComboBox
)

@staticmethod
def getAktuellesAlterInJahren(gebdat:datetime.date):
    heute = datetime.date.today()
    gebdatDesesJahr = datetime.date(heute.year, gebdat.month, gebdat.day)
    alterInJahren = heute.year - gebdat.year
    if (heute - gebdatDesesJahr).days < 0:
        alterInJahren -= 1
    return alterInJahren

class ScoreGdtException(Exception):
    def __init__(self, meldung):
        self.meldung = meldung
    def __str__(self):
        return "ScoreGDT-Fehler: " + self.meldung

import requests

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

    # Mainwindow zentrieren
    def resizeEvent(self, e):
        mainwindowBreite = e.size().width()
        mainwindowHoehe = e.size().height()
        ag = self.screen().availableGeometry()
        screenBreite = ag.size().width()
        screenHoehe = ag.size().height()
        left = screenBreite / 2 - mainwindowBreite / 2
        top = screenHoehe / 2 - mainwindowHoehe / 2
        self.setGeometry(left, top, mainwindowBreite, mainwindowHoehe)

    def __init__(self):
        super().__init__()

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
        self.eulagelesen = self.configIni["Allgemein"]["eulagelesen"]
        self.bereichsgrenzenerzwingen = self.configIni["Allgemein"]["bereichsgrenzenerzwingen"] == "True"
        self.gdtImportVerzeichnis = self.configIni["GDT"]["gdtimportverzeichnis"]
        self.gdtExportVerzeichnis = self.configIni["GDT"]["gdtexportverzeichnis"]
        self.kuerzelscoregdt = self.configIni["GDT"]["kuerzelscoregdt"]
        self.kuerzelpraxisedv = self.configIni["GDT"]["kuerzelpraxisedv"]
        self.benutzernamenListe = self.configIni["Benutzer"]["namen"].split("::")
        self.benutzerkuerzelListe = self.configIni["Benutzer"]["kuerzel"].split("::")
        self.aktuelleBenuztzernummer = int(self.configIni["Benutzer"]["letzter"])

        ## Nachträglich hinzufefügte Options
        # 1.1.1
        self.standardscore = ""
        if self.configIni.has_option("Allgemein", "standardscore"):
            self.standardscore = self.configIni["Allgemein"]["standardscore"]
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

        # scores.xml auslesen
        try:
            tree = ElementTree.parse(os.path.join(basedir, "scores", "scores.xml"))
            self.root = tree.getroot()
        except Exception as e:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Fehler beim Laden von \"scores.xml\".\nScoreGDT wird beendet.", QMessageBox.StandardButton.Ok)
            mb.exec()
            logger.logger.warning("Fehler beim Laden von scores.xml: " + str(e))
            sys.exit()

        # Grundeinstellungen bei erstem Start
        if ersterStart:
            logger.logger.info("Erster Start")
            mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von ScoreGDT", "Vermutlich starten Sie ScoreGDT das erste Mal auf diesem PC.\nMöchten Sie jetzt die Grundeinstellungen vornehmen?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.setDefaultButton(QMessageBox.StandardButton.Yes)
            if mb.exec() == QMessageBox.StandardButton.Yes:
                ## Nur mit Lizenz
                self.einstellungenLanrLizenzschluessel(False)
                ## /Nur mit Lizenz
                self.einstellungenGdt(False)
                self.einstellungenBenutzer(False)
                self.einstellungenAllgmein(False, True)

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
                ## /config.ini aktualisieren

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
                self.patid = self.pseudoLizenzId
                logger.logger.info("PatId wegen Pseudolizenz auf " + self.pseudoLizenzId + " gesetzt")
            ## /Nur mit Lizenz
            self.geburtsdatum = str(gd.getInhalt("3103"))[0:2] + "." + str(gd.getInhalt("3103"))[2:4] + "." + str(gd.getInhalt("3103"))[4:8]
            self.geschlecht = str(gd.getInhalt("3110")) # 1=männlich, 2=weiblich
            logger.logger.info("Geschlecht aus PVS-GDT (3110): " + self.geschlecht)
        except (IOError, gdtzeile.GdtFehlerException) as e:
            logger.logger.warning("Fehler beim Laden der GDT-Datei: " + str(e))
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von ScoreGDT", "Fehler beim Laden der GDT-Datei:\n" + str(e) + "\n\nSoll ScoreGDT dennoch geöffnet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
            mb.button(QMessageBox.StandardButton.No).setText("Nein")
            mb.setDefaultButton(QMessageBox.StandardButton.No)
            mbErg = mb.exec()
        if mbErg == QMessageBox.StandardButton.Yes:
            self.widget = QWidget()
            self.widget.installEventFilter(self)
            logger.logger.warning("ScoreGDT öffnen trotz GDT-Ladefehler")

            # Updateprüfung auf Github
            try:
                self.updatePruefung(meldungNurWennUpdateVerfuegbar=True)
            except Exception as e:
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Updateprüfung nicht möglich.\nBitte überprüfen Sie Ihre Internetverbindung.", QMessageBox.StandardButton.Ok)
                mb.exec()
                logger.logger.warning("Updateprüfung nicht möglich: " + str(e))

            if self.root != None:
                self.scoreRoot = self.root.find("score")
                ds = dialogScoreAuswahl.ScoreAuswahl(self.root, self.standardscore)
                if ds.exec() == 1:
                    self.scoreRoot = self.getScoreXml(ds.aktuellGewaehlterScore)
                    logger.logger.info("Score " + ds.aktuellGewaehlterScore + " ausgewählt")
                else:
                    logger.logger.info("Kein Score ausgewählt")
                    sys.exit()
                if self.scoreRoot != None:
                    self.parts = []
                    self.widgets = []
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
                            widgetErklaerung = ""
                            if widgetElement.find("erklaerung") != None:
                                widgetErklaerung = str(widgetElement.find("erklaerung").text) # type: ignore
                            widgetEinheit = ""
                            if widgetElement.find("einheit") != None:
                                widgetEinheit = str(widgetElement.find("einheit").text) # type: ignore
                            if widgetTyp == class_widgets.WidgetTyp.COMBOBOX.value:
                                itemsElement = widgetElement.find("items")
                                itemsUndWerte.clear()
                                for itemElement in itemsElement.findall("item"): # type: ignore
                                    itemWert = str(itemElement.get("wert"))
                                    itemText = str(itemElement.text)
                                    itemsUndWerte.append((itemText, itemWert))
                                self.widgets.append(class_widgets.ComboBox(widgetId, partId, widgetTitel, widgetErklaerung, widgetEinheit, itemsUndWerte.copy(), alterspruefung))
                                logger.logger.info("Combobox angelegt (Part-ID: " + partId + ", Widget-ID: " + widgetId + ") angelegt")
                            elif widgetTyp == class_widgets.WidgetTyp.CHECKBOX.value:
                                checked = str(widgetElement.get("checked")) == "True"
                                altersregel = ""
                                if widgetElement.get("altersregel") != None:
                                    altersregel = str(widgetElement.get("altersregel"))
                                geschlechtpruefung = str(widgetElement.get("geschlechtpruefung")) == "True"
                                wertElement = widgetElement.find("wert")
                                wert = str(wertElement.text) # type: ignore
                                self.widgets.append(class_widgets.CheckBox(widgetId, partId, widgetTitel, widgetErklaerung, widgetEinheit, wert, checked, alterspruefung, altersregel, geschlechtpruefung))
                                logger.logger.info("Checkbox angelegt (Part-ID: " + partId + ", Widget-ID: " + widgetId + ") angelegt")
                            elif widgetTyp == class_widgets.WidgetTyp.LINEEDIT.value:
                                regexPattern = str(widgetElement.find("regex").text) # type: ignore
                                self.widgets.append(class_widgets.LineEdit(widgetId, partId, widgetTitel, widgetErklaerung, widgetEinheit, regexPattern, alterspruefung))
                                logger.logger.info("Lineedit angelegt (Part-ID: " + partId + ", Widget-ID: " + widgetId + ") angelegt")
                                # Zahlengrenzen festlegen
                                for zahlengrenzeElement in widgetElement.findall("zahlengrenze"):
                                    zahlengrenze = float(str(zahlengrenzeElement.text))
                                    regelart = str(zahlengrenzeElement.get("regelart"))
                                    self.widgets[len(self.widgets) - 1].addZahlengrenze(zahlengrenze, class_enums.Regelarten(regelart))
                                # Faktor festlegen
                                if widgetElement.find("faktor") != None:
                                    self.widgets[len(self.widgets) - 1].setFaktor(float(str(widgetElement.find("faktor").text))) # type: ignore
                            elif widgetTyp == class_widgets.WidgetTyp.RADIOBUTTON.value:
                                checked = str(widgetElement.get("checked")) == "True" and partElement.get("geschlechtpruefung") == None
                                altersregel = str(widgetElement.get("altersregel"))
                                wertElement = widgetElement.find("wert")
                                wert = str(wertElement.text) # type: ignore
                                self.widgets.append(class_widgets.RadioButton(widgetId, partId, widgetTitel, widgetErklaerung, widgetEinheit, wert, checked, alterspruefung, altersregel))
                                logger.logger.info("Radiobutton angelegt (Part-ID: " + partId + ", Widget-ID: " + widgetId + ") angelegt")
                            # Prüfen, ob Titelbreite festgelegt
                            if widgetElement.get("titelbreite") != None:
                                self.widgets[len(self.widgets) - 1].setTitelbreite(int(str(widgetElement.get("titelbreite"))))

            # Formularaufbau
            mainLayoutV = QVBoxLayout()
            mainLayoutG = QGridLayout()
            # Patientendaten
            patient = "Patient"
            if self.geschlecht == "2":
                patient = "Patientin"
            groupboxPatientendaten = QGroupBox(patient)
            groupboxPatientendatenLayoutG = QGridLayout()
            self.labelPseudolizenz = QLabel("+++ Pseudolizenz für Test-/ Präsentationszwecke +++")
            self.labelPseudolizenz.setStyleSheet("color:rgb(200,0,0);font-style:italic")
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
            labelScoreName.setStyleSheet("color:rgb(0,0,200)")
            if self.scoreRoot.find("information") != None: #type: ignore
                labelScoreInformation = QLabel(str(self.scoreRoot.find("information").text)) #type: ignore
                labelScoreInformation.setFont(self.fontNormal)
                labelScoreInformation.setStyleSheet("color:rgb(0,0,200)")

            # Score
            for part in self.parts:
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
                        partLayout.addWidget(widgetWidget, partGridZeile, 1, alignment=Qt.AlignmentFlag.AlignTop)
                        einheitUndErklärung = ""
                        if widget.getEinheit() != "":
                            einheitUndErklärung = widget.getEinheit() + " "
                        if widget.getErklaerung() != "":
                            einheitUndErklärung += "(" + widget.getErklaerung() + ")"
                        labelEinheitUndErklaerung = QLabel(einheitUndErklärung)
                        labelEinheitUndErklaerung.setFont(self.fontNormal)
                        partLayout.addWidget(labelEinheitUndErklaerung, partGridZeile, 2, alignment=Qt.AlignmentFlag.AlignTop)
                        # Prüfen, ob Alterstextfeld
                        if widget.getTyp() == class_widgets.WidgetTyp.LINEEDIT and widget.alterspruefungAktiv():
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
                        elif widget.getTyp() == (class_widgets.WidgetTyp.CHECKBOX or widget.getTyp() == class_widgets.WidgetTyp.RADIOBUTTON) and widget.alterspruefungAktiv():
                            regelnErfuellt = True
                            for regel in widget.getAltersregeln():
                                tempRegel = str(getAktuellesAlterInJahren(self.geburtsdatumAlsDate)) + regel
                                if not self.regelIstErfuellt(tempRegel):
                                    regelnErfuellt = False
                                    break
                            widget.getQt().setChecked(regelnErfuellt)
                        # Prüfen, ob Geschlechtpart (Groupbox mit 2 Radiobuttons)
                        if part.geschlechtpruefungAktiv() and widget.getTyp() == class_widgets.WidgetTyp.RADIOBUTTON:
                            if ("männlich" in widget.getTitel().lower() or "männlich" in widget.getErklaerung().lower()) and self.geschlecht == "1":
                                widget.getQt().setChecked(True)
                                logger.logger.info("Radiobutton " + widget.getId() + "als männlich aktiviert")
                            elif ("weiblich" in widget.getTitel().lower() or "weiblich" in widget.getErklaerung().lower()) and self.geschlecht == "2":
                                widget.getQt().setChecked(True)
                                logger.logger.info("Radiobutton " + widget.getId() + "als weiblich aktiviert")
                        # Prüfen, ob Geschlechtwidget (Checkbox)
                        if widget.getTyp() == class_widgets.WidgetTyp.CHECKBOX and widget.geschlechtpruefungAktiv():
                            if ("männlich" in widget.getTitel().lower() or "männlich" in widget.getErklaerung().lower()) and self.geschlecht == "1":
                                widget.getQt().setChecked(True)
                                logger.logger.info("Checkbox " + widget.getId() + "als männlich aktiviert")
                            elif ("weiblich" in widget.getTitel().lower() or "weiblich" in widget.getErklaerung().lower()) and self.geschlecht == "2":
                                widget.getQt().setChecked(True)
                                logger.logger.info("Checkbox " + widget.getId() + "als weiblich aktiviert")

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
            self.pushButtonBerechnen.setStyleSheet("color:rgb(0,0,200)")
            self.pushButtonBerechnen.setFixedHeight(40)
            self.pushButtonBerechnen.setFont(self.fontBold)
            self.pushButtonBerechnen.clicked.connect(self.pushButtonBerechnenClicked)

            ergebnisLayoutH = QHBoxLayout()
            labelScoreErgebnis = QLabel("Ergebnis:")
            labelScoreErgebnis.setFont(self.fontBold)
            self.lineEditScoreErgebnis = QLineEdit()
            self.lineEditScoreErgebnis.setReadOnly(True)
            self.lineEditScoreErgebnis.setFont(self.fontBoldGross)
            ergebnisEinheit = ""
            if self.scoreRoot.find("berechnung").find("ergebniseinheit").text != None: # type: ignore
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
                    tempLabelErgebnis.setStyleSheet("color:rgb(0,0,100)")
                    tempLabelErgebnis.setFont(self.fontNormal)
                    tempLabelBeschreibung= QLabel(beschreibungen[i])
                    tempLabelBeschreibung.setStyleSheet("color:rgb(0,0,100)")
                    tempLabelBeschreibung.setFont(self.fontNormal)
                    self.labelErgebnisbereiche.append(tempLabelErgebnis)
                    self.labelBeschreibungen.append(tempLabelBeschreibung)
                    groupBoxAuswertungLayoutG.addWidget(tempLabelErgebnis, i, 0)
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
            self.pushButtonSenden = QPushButton("Daten senden")
            self.pushButtonSenden.setFont(self.fontBold)
            self.pushButtonSenden.setFixedHeight(60)
            self.pushButtonSenden.setEnabled(self.addOnsFreigeschaltet)
            self.pushButtonSenden.clicked.connect(self.pushButtonSendenClicked)
            datumBenutzerLayoutG.addWidget(labelDokumentiertAm, 0, 0)
            datumBenutzerLayoutG.addWidget(labelDokumentiertVon, 0, 1)
            datumBenutzerLayoutG.addWidget(self.dateEditUntersuchungsdatum, 1, 0)
            datumBenutzerLayoutG.addWidget(self.comboBoxBenutzer, 1, 1)
                        
            ## Nur mit Lizenz
            if self.addOnsFreigeschaltet and gdttoolsL.GdtToolsLizenzschluessel.getSoftwareId(self.lizenzschluessel) == gdttoolsL.SoftwareId.SCOREGDTPSEUDO:
                mainLayoutV.addWidget(self.labelPseudolizenz, alignment=Qt.AlignmentFlag.AlignCenter)
            ## /Nur mit Lizenz
            mainLayoutV.addWidget(groupboxPatientendaten)
            mainLayoutV.addWidget(labelScoreName, alignment=Qt.AlignmentFlag.AlignCenter)
            mainLayoutV.addWidget(labelScoreInformation, alignment=Qt.AlignmentFlag.AlignCenter)
            mainLayoutV.addLayout(mainLayoutG)
            mainLayoutV.addWidget(self.pushButtonBerechnen)
            ergebnisLayoutH.addWidget(labelScoreErgebnis)
            ergebnisLayoutH.addWidget(self.lineEditScoreErgebnis)
            ergebnisLayoutH.addWidget(self.labelScoreErgebnisEinheit)
            mainLayoutV.addLayout(ergebnisLayoutH)
            mainLayoutV.addSpacing(20)
            if auswertungElement != None:
                mainLayoutV.addWidget(groupBoxAuswertung)
            mainLayoutV.addLayout(datumBenutzerLayoutG)
            mainLayoutV.addWidget(self.pushButtonSenden)
            ## Nur mit Lizenz
            if self.addOnsFreigeschaltet:
                gueltigeLizenztage = gdttoolsL.GdtToolsLizenzschluessel.nochTageGueltig(self.lizenzschluessel)
                if gdttoolsL.GdtToolsLizenzschluessel.getGueltigkeitsdauer(self.lizenzschluessel) == gdttoolsL.Gueltigkeit.EINJAHR and gueltigeLizenztage  > 0 and gueltigeLizenztage <= 30:
                    labelLizenzLaeuftAus = QLabel("Die genutzte Lizenz ist noch " + str(gueltigeLizenztage) + " Tage gültig.")
                    labelLizenzLaeuftAus.setStyleSheet("color:rgb(200,0,0)")
                    mainLayoutV.addWidget(labelLizenzLaeuftAus, alignment=Qt.AlignmentFlag.AlignCenter)
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
            scoreMenuAuswaehlenAction.triggered.connect(lambda checked=False, neustartfrage=True: self.scoreAuswaehlen(checked, True))
            einstellungenMenu = menubar.addMenu("Einstellungen")
            einstellungenAllgemeinAction = QAction("Allgemeine Einstellungen", self)
            einstellungenAllgemeinAction.triggered.connect(lambda checked=False, neustartfrage=True: self.einstellungenAllgmein(checked, True))
            einstellungenGdtAction = QAction("GDT-Einstellungen", self)
            einstellungenGdtAction.triggered.connect(lambda checked=False, neustartfrage=True: self.einstellungenGdt(checked, True))
            einstellungenBenutzerAction = QAction("BenutzerInnen verwalten", self)
            einstellungenBenutzerAction.triggered.connect(lambda checked=False, neustartfrage=True: self.einstellungenBenutzer(checked, True)) 

            ## Nur mit Lizenz
            einstellungenErweiterungenAction = QAction("LANR/Lizenzschlüssel", self)
            einstellungenErweiterungenAction.triggered.connect(lambda checked=False, neustartfrage=True: self.einstellungenLanrLizenzschluessel(checked, True)) 
            einstellungenImportExportAction = QAction("Im- /Exportieren", self)
            einstellungenImportExportAction.triggered.connect(self.einstellungenImportExport) 
            einstellungenImportExportAction.setMenuRole(QAction.MenuRole.NoRole)
            ## /Nur mit Lizenz
            hilfeMenu = menubar.addMenu("Hilfe")
            hilfeWikiAction = QAction("ScoreGDT Wiki", self)
            hilfeWikiAction.triggered.connect(self.scoregdtWiki)
            hilfeUpdateAction = QAction("Auf Update prüfen", self)
            hilfeUpdateAction.triggered.connect(self.updatePruefung)
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
            hilfeMenu.addSeparator()
            hilfeMenu.addAction(hilfeUeberAction)
            hilfeMenu.addAction(hilfeEulaAction)
            hilfeMenu.addSeparator()
            hilfeMenu.addAction(hilfeLogExportieren)
        else:
            sys.exit()

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
    
    def berechnung(self, formel:str):
        """
        Berechnet das Ergebnis einer Formel im Format xPLUSy, xMINUSy...
        Parameter:
            formel:str
        Return:
            Ergebnis der Berechnung: int oder float
        """
        regexZahl = r"^\d+([.,]\d)?$"
        formel = formel.replace(" ", "")
        ergebnis = formel
        for rechenart in class_enums.Rechenarten._member_names_:
            if rechenart in formel:
                operanden = formel.split(rechenart)
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
                    if rechenart == class_enums.Rechenarten.PLUS.value:
                        ergebnis = operandenAlsZahl[0] + operandenAlsZahl[1]
                    elif rechenart == class_enums.Rechenarten.MINUS.value:
                        ergebnis = operandenAlsZahl[0] - operandenAlsZahl[1]
                    elif rechenart == class_enums.Rechenarten.MAL.value:
                        ergebnis = operandenAlsZahl[0] * operandenAlsZahl[1]
                    elif rechenart == class_enums.Rechenarten.DURCH.value:
                        ergebnis = operandenAlsZahl[0] / operandenAlsZahl[1]
                    elif rechenart == class_enums.Rechenarten.HOCH.value:
                        ergebnis = operandenAlsZahl[0] ** operandenAlsZahl[1]
                    break
                else:
                    logger.logger.error("Fehler bei Berechung der Formel " + formel + ": nicht beide Operanden sind Zahlen")
                    mb = QMessageBox(QMessageBox.Icon.Critical, "Hinweis von ScoreGDT", "Fehler bei Berechung der Formel " + formel + ": nicht beide Operanden sind Zahlen", QMessageBox.StandardButton.Ok)
                    mb.exec()
                    break
        return ergebnis
    
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
        Ersetzt Variablen im Format $id{xxx} mit dem aktuellen Wert des Widgets mit der id xxx
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
            ersetzt = ersetzt.replace(idVariable, self.getWertAusWidgetId(id))
        return ersetzt
    
    def ersetzeVariablen(self, variablen:dict, string:str):
        """
        Ersetzt Variablen im Format $var{xxx} durch deen Wert
        Parameter:
            variablen: dict mit key: Variablenname, value: Variablenwert
            strint:. str
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
                        widget.getQt().setText(str(widget.getGrenzzahl(zahl)).replace(".", ",").replace(",0", ""))
       
        if formularOk :
            try:
                # $var{...}-Werte auslesen
                berechnungElement = self.scoreRoot.find("berechnung") # type: ignore
                formelElement = berechnungElement.find("formel") # type: ignore
                self.erfuellteAuswertungsregel = -1
                if str(formelElement.get("typ")) != "script": # type: ignore        
                    operationen = []
                    for operationElement in formelElement.findall("operation"): # type: ignore
                        operationen.append(str(operationElement.text))
                    variablenElement = berechnungElement.find("variablen") # type: ignore
                    variablen = {}
                    for variableElement in variablenElement.findall("variable"): # type: ignore
                        variablenname = str(variableElement.get("name"))
                        # Ohne Bedingung
                        if variableElement.find("bedingung") == None:
                            text = str(variableElement.text)
                            textMitIdWertErsetzt = self.ersetzeIdVariablen(text)
                            textMitVarWertErsezt = self.ersetzeVariablen(variablen, textMitIdWertErsetzt)
                            variablen[variablenname] = str(self.berechnung(textMitVarWertErsezt))
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
                    # $var{...}-Variablen durch Werte ersetzen
                    patternVar = r"\$var{[^{}]+}"
                    variablenMitNichtErfuelltenRegeln = []
                    ersteOperation = True
                    tempErgebnis = 0
                    for operation in operationen:
                        operationMitZahl = operation
                        if not ersteOperation:
                            operationMitZahl = str(tempErgebnis) + " " + operationMitZahl
                            ersteOperation = False
                        varVariablen = re.findall(patternVar, operation)
                        for varVariable in varVariablen:
                            varName = varVariable[5:-1]
                            if varName in variablen:
                                operationMitZahl = operationMitZahl.replace(varVariable, variablen[varName])
                            else:
                                logger.logger.warning("Variablenname " + varName + " nicht ausgelesen")
                                variablenMitNichtErfuelltenRegeln.append(varName)
                        operationMitZahl = self.ersetzeIdVariablen(operationMitZahl)
                        tempErgebnis = self.berechnung(operationMitZahl)
                        ersteOperation = False
                        logger.logger.info("Teilergebnis: " + str(self.berechnung(operationMitZahl)))
                    if len(variablenMitNichtErfuelltenRegeln) == 0:
                        self.lineEditScoreErgebnis.setText(str(tempErgebnis).replace(".", ","))
                        logger.logger.info("Endergebnis: " + str(tempErgebnis).replace(".", ","))
                        # Auswertung
                        auswertungElement = self.scoreRoot.find("auswertung") # type: ignore
                        if auswertungElement != None:
                            ergebnis = str(tempErgebnis)
                            beurteilungNr = 0
                            for beurteilungElement in auswertungElement.findall("beurteilung"):
                                regelErfuellt = True
                                for regelElement in beurteilungElement.findall("regel"):
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
                                        self.labelErgebnisbereiche[i].setStyleSheet("color:rgb(0,150,0)")
                                        self.labelBeschreibungen[i].setStyleSheet("color:rgb(0,150,0)")
                                    else:
                                        self.labelErgebnisbereiche[i].setStyleSheet("color:rgb(0,0,100)")
                                        self.labelBeschreibungen[i].setStyleSheet("color:rgb(0,0,100)")
                    else:
                        mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Der Score kann nicht berechnet werden, da für die folgenden Variablen keine Regel zutrifft:\n- " + str.join("\n- ", variablenMitNichtErfuelltenRegeln), QMessageBox.StandardButton.Ok)
                        mb.exec()
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
            except Exception as e:
                logger.logger.error("Fehler bei der Score-Berechung: " + str(e))
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Fehler bei der Score-Berechung: " + str(e), QMessageBox.StandardButton.Ok)
                mb.exec()

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
            "\u2082": "2",
            "\u00b2": "2",
            "\u2264": "<=",
            "\u2265": ">="
        }
        for zuErsetzen in zuErsetzendeStrings:
            ersetzt = ersetzt.replace(zuErsetzen, zuErsetzendeStrings[zuErsetzen])
        return ersetzt
            
    def pushButtonSendenClicked(self):
        if self.lineEditScoreErgebnis.text() != "":
            logger.logger.info("Daten senden geklickt")
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
            # Tests
            if str(self.scoreRoot.get("keineTestuebermittlung")) != "True": # type: ignore
                for widget in self.widgets:
                    test = None
                    if widget.getTyp() == class_widgets.WidgetTyp.LINEEDIT:
                        test = gdt.GdtTest("ScoreGDT" + "_" + widget.getId(), widget.getTitel(), widget.getWertOhneFaktor().replace(".", ",").replace(",0", ""), widget.getEinheit()) # type: ignore
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
                        test = gdt.GdtTest("ScoreGDT" + "_" + widget.getId(), self.fuerGdtBereinigen(widget.getTitel()), wert, self.fuerGdtBereinigen(widget.getEinheit())) # type: ignore
                    else:
                        test = gdt.GdtTest("ScoreGDT" + "_" + widget.getId(), self.fuerGdtBereinigen(widget.getTitel()), widget.getWert().replace(".", ",").replace(",0", ""), self.fuerGdtBereinigen(widget.getEinheit())) # type: ignore
                    if test != None:
                        gd.addTest(test)
            gdtname = str(self.scoreRoot.get("name")) # type: ignore
            if self.scoreRoot.get("gdtname") != None: # type: ignore
                gdtname = str(self.scoreRoot.get("gdtname")) # type: ignore
            leerzeichenVorEinheit = " "
            if self.labelScoreErgebnisEinheit.text() == "%":
                leerzeichenVorEinheit = ""
            befund = gdtname + ": " +  self.lineEditScoreErgebnis.text() + leerzeichenVorEinheit + self.labelScoreErgebnisEinheit.text() # type: ignore
            gd.addZeile("6220", befund)
            if self.erfuellteAuswertungsregel != -1:
                auswertung = "Beurteilung: " + self.labelBeschreibungen[self.erfuellteAuswertungsregel].text()
                gd.addZeile("6220", auswertung)
            gd.addZeile("6227", "Dokumentiert von: " + self.benutzerkuerzelListe[self.aktuelleBenuztzernummer])
            # GDT-Datei exportieren
            if not gd.speichern(os.path.join(self.gdtExportVerzeichnis, self.kuerzelpraxisedv + self.kuerzelscoregdt + ".gdt"), self.zeichensatz):
                logger.logger.error("Fehler bei GDT-Dateiexport nach " + self.gdtExportVerzeichnis + "/" + self.kuerzelpraxisedv + self.kuerzelscoregdt + ".gdt")
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "GDT-Export nicht möglich.\nBitte überprüfen Sie die Angabe des Exportverzeichnisses.", QMessageBox.StandardButton.Ok)
                mb.exec()
            else: 
                self.configIni["Benutzer"]["letzter"] = str(self.aktuelleBenuztzernummer)
                try:
                    with open(os.path.join(self.configPath, "config.ini"), "w", encoding="utf-8") as configfile:
                        self.configIni.write(configfile)
                except:
                    logger.logger.warning("Problem beim Speichern von Benutzer/letzter")
                sys.exit()
        else:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Vor dem Senden der Daten muss ein Score berechnet werden.", QMessageBox.StandardButton.Ok)
            mb.exec()

    def updatePruefung(self, meldungNurWennUpdateVerfuegbar = False):
        response = requests.get("https://api.github.com/repos/retconx/scoregdt/releases/latest")
        githubRelaseTag = response.json()["tag_name"]
        latestVersion = githubRelaseTag[1:] # ohne v
        if versionVeraltet(self.version, latestVersion):
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Die aktuellere ScoreGDT-Version " + latestVersion + " ist auf <a href='https://www.github.com/retconx/scoregdt/releases'>Github</a> verfügbar.", QMessageBox.StandardButton.Ok)
            mb.setTextFormat(Qt.TextFormat.RichText)
            mb.exec()
        elif not meldungNurWennUpdateVerfuegbar:
            mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Sie nutzen die aktuelle ScoreGDT-Version.", QMessageBox.StandardButton.Ok)
            mb.exec()

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

    def scoreAuswaehlen(self, checked, neustartfrage=False):
        os.execl(sys.executable, __file__, *sys.argv)

    def einstellungenAllgmein(self, checked, neustartfrage=False):
        de = dialogEinstellungenAllgemein.EinstellungenAllgemein(self.configPath, self.root, self.standardscore)
        if de.exec() == 1:
            self.configIni["Allgemein"]["bereichsgrenzenerzwingen"] = str(de.checkBoxZahlengrenzenpruefung.isChecked())
            self.configIni["Allgemein"]["standardscore"] = de.comboBoxScoreAuswahl.currentText()
            with open(os.path.join(self.configPath, "config.ini"), "w", encoding="utf-8") as configfile:
                self.configIni.write(configfile)
            if neustartfrage:
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von ScoreGDT", "Damit die Einstellungsänderungen wirksam werden, sollte ScoreGDT neu gestartet werden.\nSoll ScoreGDT jetzt neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)

    def einstellungenGdt(self, checked, neustartfrage=False):
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

    def einstellungenBenutzer(self, checked, neustartfrage = False):
        de = dialogEinstellungenBenutzer.EinstellungenBenutzer(self.configPath)
        if de.exec() == 1:
            namen = []
            kuerzel = []
            for i in range(10):
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
    def einstellungenLanrLizenzschluessel(self, checked, neustartfrage = False):
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
app.setWindowIcon(QIcon(os.path.join(basedir, "icons/program.png")))
window = MainWindow()
window.show()
app.exec()