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
        self.bereichsgrenzenerzwingen = configIni["Allgemein"]["bereichsgrenzenerzwingen"] == "True"
        self.updaterpfad = configIni["Allgemein"]["updaterpfad"]

        self.setWindowTitle("Allgemeine Einstellungen")
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
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

        groupBoxUpdatesLayoutG.addWidget(labelUpdaterPfad, 0, 0)
        groupBoxUpdatesLayoutG.addWidget(self.lineEditUpdaterPfad, 0, 1)
        groupBoxUpdatesLayoutG.addWidget(self.pushButtonUpdaterPfad, 0, 2)
        groupBoxUpdates.setLayout(groupBoxUpdatesLayoutG)
    
        dialogLayoutV.addWidget(groupBoxScores)
        dialogLayoutV.addWidget(groupBoxUpdates)
        dialogLayoutV.addWidget(self.buttonBox)

        self.setLayout(dialogLayoutV)

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
            self.lineEditUpdaterPfad.setText(fd.selectedFiles()[0])
            self.lineEditUpdaterPfad.setToolTip(fd.selectedFiles()[0])
            self.lineEditUpdaterPfad.setStyleSheet("background:rgb(255,255,255)")
            
    def accept(self):
        self.done(1)