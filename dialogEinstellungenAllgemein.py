import configparser, os
from xml.etree import ElementTree
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QCheckBox, 
    QLabel,
    QComboBox
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

        self.setWindowTitle("Allgemeine Einstellungen")
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        # Groupbox Score-Berechung
        groupBoxAutomatischePruefungLayoutG = QGridLayout()
        groupBoxAutomatischePruefung = QGroupBox("Score-Berechnung")
        groupBoxAutomatischePruefung.setFont(self.fontBold)
        self.checkBoxZahlengrenzenpruefung = QCheckBox("Bereichsgrenzen erzwingen")
        self.checkBoxZahlengrenzenpruefung.setFont(self.fontNormal)
        self.checkBoxZahlengrenzenpruefung.setChecked(self.bereichsgrenzenerzwingen)
        groupBoxAutomatischePruefungLayoutG.addWidget(self.checkBoxZahlengrenzenpruefung, 0, 0)
        groupBoxAutomatischePruefung.setLayout(groupBoxAutomatischePruefungLayoutG)

        # Groupbox Standard-Score
        groupBoxStandardScoreLayoutG = QGridLayout()
        groupBoxStandardScore = QGroupBox("Standard-Score")
        groupBoxStandardScore.setFont(self.fontBold)
        labelStandardAuswahl = QLabel("Standard-Auswahl")
        labelStandardAuswahl.setFont(self.fontNormal)
        self.scoreNameListe = []
        self.comboBoxScoreAuswahl = QComboBox()
        self.comboBoxScoreAuswahl.setFont(self.fontNormal)
        for scoreElement in self.scoresRoot.findall("score"):
           self.scoreNameListe.append(str(scoreElement.get("name")))
        self.scoreNameListe.sort()
        self.comboBoxScoreAuswahl.addItems(self.scoreNameListe)
        self.comboBoxScoreAuswahl.setCurrentText(self.standardScore)
        groupBoxStandardScoreLayoutG.addWidget(labelStandardAuswahl, 0, 0)
        groupBoxStandardScoreLayoutG.addWidget(self.comboBoxScoreAuswahl, 0, 1)
        groupBoxStandardScore.setLayout(groupBoxStandardScoreLayoutG)

        dialogLayoutV.addWidget(groupBoxAutomatischePruefung)
        dialogLayoutV.addWidget(groupBoxStandardScore)
        dialogLayoutV.addWidget(self.buttonBox)

        self.setLayout(dialogLayoutV)
    
    def accept(self):
        self.done(1)