import configparser, os, sys
from xml.etree import ElementTree
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QCheckBox, 
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton, 
    QFileDialog
)

from PySide6.QtGui import QFont

class EinstellungenAllgemein(QDialog):
    def __init__(self, configPath, scoresRoot:ElementTree.Element, standardScore:str):
        super().__init__()
        self.scoresRoot = scoresRoot
        self.standardScore = standardScore

        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)

        #config.ini lesen
        configIni = configparser.ConfigParser()
        configIni.read(os.path.join(configPath, "config.ini"))
        self.einrichtungsname = configIni["Allgemein"]["einrichtungsname"]
        self.einrichtunguebernehmen = configIni["Allgemein"]["einrichtunguebernehmen"] == "True"
        self.bereichsgrenzenerzwingen = configIni["Allgemein"]["bereichsgrenzenerzwingen"] == "True"
        self.updaterpfad = configIni["Allgemein"]["updaterpfad"]
        self.autoupdate = configIni["Allgemein"]["autoupdate"] == "True"
        self.archivierungspfad = configIni["Allgemein"]["archivierungspfad"]

        self.setWindowTitle("Allgemeine Einstellungen")
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        # Groupbox Einrichtung
        groupBoxEinrichtungLayoutG = QGridLayout()
        groupBoxEinrichtung = QGroupBox("Einrichtung/Praxis")
        groupBoxEinrichtung.setFont(self.fontBold)
        labelEinrichtungsname = QLabel("Name")
        labelEinrichtungsname.setFont(self.fontNormal)
        self.lineEditEinrichtungsname = QLineEdit(self.einrichtungsname)
        self.lineEditEinrichtungsname.setFont(self.fontNormal)
        self.lineEditEinrichtungsname.setPlaceholderText("Hausarztpraxis XY")
        self.checkBoxEinrichtungUebernehmen = QCheckBox("Auf PDF übernehmen")
        self.checkBoxEinrichtungUebernehmen.setFont(self.fontNormal)
        self.checkBoxEinrichtungUebernehmen.setChecked(self.einrichtunguebernehmen)
        groupBoxEinrichtungLayoutG.addWidget(labelEinrichtungsname, 0, 0)
        groupBoxEinrichtungLayoutG.addWidget(self.lineEditEinrichtungsname, 0, 1)
        groupBoxEinrichtungLayoutG.addWidget(self.checkBoxEinrichtungUebernehmen, 1, 0, 1, 2)
        groupBoxEinrichtung.setLayout(groupBoxEinrichtungLayoutG)

        # Groupbox Scores
        groupBoxScoresLayoutG = QGridLayout()
        groupBoxScores = QGroupBox("Scores")
        groupBoxScores.setFont(self.fontBold)
        self.scoreNameListe = []
        self.comboBoxScoreAuswahl = QComboBox()
        self.comboBoxScoreAuswahl.setFont(self.fontNormal)
        for scoreElement in self.scoresRoot.findall("score"):
           self.scoreNameListe.append(str(scoreElement.get("name")))
        self.scoreNameListe.sort()
        self.comboBoxScoreAuswahl.addItems(self.scoreNameListe)
        self.comboBoxScoreAuswahl.setCurrentText(self.standardScore)
        self.checkBoxZahlengrenzenpruefung = QCheckBox("Bereichsgrenzen erzwingen")
        self.checkBoxZahlengrenzenpruefung.setFont(self.fontNormal)
        self.checkBoxZahlengrenzenpruefung.setChecked(self.bereichsgrenzenerzwingen)
        labelStandardAuswahl = QLabel("Standard-Score")
        labelStandardAuswahl.setFont(self.fontNormal)
        groupBoxScoresLayoutG.addWidget(labelStandardAuswahl, 0, 0)
        groupBoxScoresLayoutG.addWidget(self.comboBoxScoreAuswahl, 0, 1)
        groupBoxScoresLayoutG.addWidget(self.checkBoxZahlengrenzenpruefung, 1, 0)
        groupBoxScores.setLayout(groupBoxScoresLayoutG)

        # Groupbox Archivierung
        groupBoxArchivierungLayoutG = QGridLayout()
        groupBoxArchivierung = QGroupBox("Archivierung")
        groupBoxArchivierung.setFont(self.fontBold)
        labelArchivierungsverzeichnis = QLabel("Archivierungsverzeichnis:")
        labelArchivierungsverzeichnis.setFont(self.fontNormal)
        self.lineEditArchivierungsverzeichnis = QLineEdit(self.archivierungspfad)
        self.lineEditArchivierungsverzeichnis.setFont(self.fontNormal)
        self.lineEditArchivierungsverzeichnis.setToolTip(self.archivierungspfad)
        buttonDurchsuchenArchivierungsverzeichnis = QPushButton("...")
        buttonDurchsuchenArchivierungsverzeichnis.setFont(self.fontNormal)
        buttonDurchsuchenArchivierungsverzeichnis.clicked.connect(self.durchsuchenArchivierungsverzeichnis)
        groupBoxArchivierungLayoutG.addWidget(labelArchivierungsverzeichnis, 0, 0, 1, 2)
        groupBoxArchivierungLayoutG.addWidget(self.lineEditArchivierungsverzeichnis, 1, 0)
        groupBoxArchivierungLayoutG.addWidget(buttonDurchsuchenArchivierungsverzeichnis, 1, 1)
        groupBoxArchivierung.setLayout(groupBoxArchivierungLayoutG)

        # GroupBox Updates
        groupBoxUpdatesLayoutG = QGridLayout()
        groupBoxUpdates = QGroupBox("Updates")
        groupBoxUpdates.setFont(self.fontBold)
        labelUpdaterPfad = QLabel("Updater-Pfad")
        labelUpdaterPfad.setFont(self.fontNormal)
        self.lineEditUpdaterPfad= QLineEdit(self.updaterpfad)
        self.lineEditUpdaterPfad.setFont(self.fontNormal)
        self.lineEditUpdaterPfad.setToolTip(self.updaterpfad)
        if not os.path.exists(self.updaterpfad):
            self.lineEditUpdaterPfad.setStyleSheet("background:rgb(255,200,200)")
        self.pushButtonUpdaterPfad = QPushButton("...")
        self.pushButtonUpdaterPfad.setFont(self.fontNormal)
        self.pushButtonUpdaterPfad.setToolTip("Pfad zum GDT-Tools Updater auswählen")
        self.pushButtonUpdaterPfad.clicked.connect(self.pushButtonUpdaterPfadClicked)
        self.checkBoxAutoUpdate = QCheckBox("Automatisch auf Update prüfen")
        self.checkBoxAutoUpdate.setFont(self.fontNormal)
        self.checkBoxAutoUpdate.setChecked(self.autoupdate)
        groupBoxUpdatesLayoutG.addWidget(labelUpdaterPfad, 0, 0)
        groupBoxUpdatesLayoutG.addWidget(self.lineEditUpdaterPfad, 0, 1)
        groupBoxUpdatesLayoutG.addWidget(self.pushButtonUpdaterPfad, 0, 2)
        groupBoxUpdatesLayoutG.addWidget(self.checkBoxAutoUpdate, 1, 0)
        groupBoxUpdates.setLayout(groupBoxUpdatesLayoutG)

        groupBoxUpdatesLayoutG.addWidget(labelUpdaterPfad, 0, 0)
        groupBoxUpdatesLayoutG.addWidget(self.lineEditUpdaterPfad, 0, 1)
        groupBoxUpdatesLayoutG.addWidget(self.pushButtonUpdaterPfad, 0, 2)
        groupBoxUpdates.setLayout(groupBoxUpdatesLayoutG)
    
        dialogLayoutV.addWidget(groupBoxEinrichtung)
        dialogLayoutV.addWidget(groupBoxScores)
        dialogLayoutV.addWidget(groupBoxArchivierung)
        dialogLayoutV.addWidget(groupBoxUpdates)
        dialogLayoutV.addWidget(self.buttonBox)

        self.setLayout(dialogLayoutV)

    def durchsuchenArchivierungsverzeichnis(self):
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.FileMode.Directory)
        fd.setWindowTitle("Archivierungsverzeichnis")
        fd.setDirectory(self.archivierungspfad)
        fd.setModal(True)
        fd.setLabelText(QFileDialog.DialogLabel.Accept, "Ok")
        fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
        if fd.exec() == 1:
            self.archivierungspfad = fd.directory()
            self.lineEditArchivierungsverzeichnis.setText(os.path.abspath(fd.directory().path()))
            self.lineEditArchivierungsverzeichnis.setToolTip(os.path.abspath(fd.directory().path()))

    def pushButtonUpdaterPfadClicked(self):
        fd = QFileDialog(self)
        fd.setFileMode(QFileDialog.FileMode.ExistingFile)
        if os.path.exists(self.lineEditUpdaterPfad.text()):
            fd.setDirectory(os.path.dirname(self.lineEditUpdaterPfad.text()))
        fd.setWindowTitle("Updater-Pfad auswählen")
        fd.setModal(True)
        if "win32" in sys.platform:
            fd.setNameFilters(["exe-Dateien (*.exe)"])
        elif "darwin" in sys.platform:
            fd.setNameFilters(["app-Bundles (*.app)"])
        fd.setLabelText(QFileDialog.DialogLabel.Accept, "Auswählen")
        fd.setLabelText(QFileDialog.DialogLabel.Reject, "Abbrechen")
        if fd.exec() == 1:
            self.lineEditUpdaterPfad.setText(os.path.abspath(fd.selectedFiles()[0]))
            self.lineEditUpdaterPfad.setToolTip(os.path.abspath(fd.selectedFiles()[0]))
            self.lineEditUpdaterPfad.setStyleSheet("background:rgb(255,255,255)")
            
    def accept(self):
        self.done(1)