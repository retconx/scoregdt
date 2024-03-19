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
        self.alterspruefung = configIni["Allgemein"]["alterspruefung"] == "True"
        self.zahlengrenzenmuss = configIni["Allgemein"]["zahlengrenzenmuss"] == "True"

        self.setWindowTitle("Allgemeine Einstellungen")
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        # Groupbox Wochentagsübertragung
        groupBoxIntegritaetspruefungLayoutG = QGridLayout()
        groupBoxIntegritaetspruefung = QGroupBox("Integritätsprüfungen")
        groupBoxIntegritaetspruefung.setStyleSheet("font-weight:bold")
        self.checkBoxAlterspruefung = QCheckBox("Per GDT übermitteltes Alter")
        self.checkBoxAlterspruefung.setStyleSheet("font-weight:normal")
        self.checkBoxAlterspruefung.setChecked(self.alterspruefung)
        self.checkBoxZahlengrenzenpruefung = QCheckBox("Bereichsgrenzen erzwingen")
        self.checkBoxZahlengrenzenpruefung.setStyleSheet("font-weight:normal")
        self.checkBoxZahlengrenzenpruefung.setChecked(self.zahlengrenzenmuss)

        groupBoxIntegritaetspruefungLayoutG.addWidget(self.checkBoxAlterspruefung, 0, 0)
        groupBoxIntegritaetspruefungLayoutG.addWidget(self.checkBoxZahlengrenzenpruefung, 1, 0)
        groupBoxIntegritaetspruefung.setLayout(groupBoxIntegritaetspruefungLayoutG)

        dialogLayoutV.addWidget(groupBoxIntegritaetspruefung)
        dialogLayoutV.addWidget(self.buttonBox)

        self.setLayout(dialogLayoutV)
    
    def accept(self):
        self.done(1)