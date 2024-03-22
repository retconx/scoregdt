import configparser, os
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QCheckBox
)

class EinstellungenAllgemein(QDialog):
    def __init__(self, configPath):
        super().__init__()

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
        # Groupbox Wochentagsübertragung
        groupBoxAutomatischePruefungLayoutG = QGridLayout()
        groupBoxAutomatischePruefung = QGroupBox("Score-Berechnung")
        groupBoxAutomatischePruefung.setStyleSheet("font-weight:bold")
        self.checkBoxZahlengrenzenpruefung = QCheckBox("Bereichsgrenzen erzwingen")
        self.checkBoxZahlengrenzenpruefung.setStyleSheet("font-weight:normal")
        self.checkBoxZahlengrenzenpruefung.setChecked(self.bereichsgrenzenerzwingen)

        groupBoxAutomatischePruefungLayoutG.addWidget(self.checkBoxZahlengrenzenpruefung, 0, 0)
        groupBoxAutomatischePruefung.setLayout(groupBoxAutomatischePruefungLayoutG)

        dialogLayoutV.addWidget(groupBoxAutomatischePruefung)
        dialogLayoutV.addWidget(self.buttonBox)

        self.setLayout(dialogLayoutV)
    
    def accept(self):
        self.done(1)