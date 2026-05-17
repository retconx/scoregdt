import os, configparser
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox
)

class StartargumentGenerieren(QDialog):
    def __init__(self, configPath:str, scorename:str):
        super().__init__()

        self.configPath = configPath
        self.scorename = scorename

        # config.ini lesen
        configIni = configparser.ConfigParser()
        configIni.read(os.path.join(configPath, "config.ini"), encoding="utf-8")
        self.hauptId = configIni["GDT"]["idscoregdt"]

        self.setWindowTitle("Startargument für Programmstart mit Score generieren")
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText("In Zwischenablage kopieren")
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type: ignore
        self.buttonBox.rejected.connect(self.reject) # type: ignor

        dialogLayoutV = QVBoxLayout()
        dialogLayoutH = QHBoxLayout()
        labelBeschreibung = QLabel("Um ScoreGDT direkt mit dem aktuell ausgewählten Score \"" + scorename + "\" zu starten (Umgehung der Scoreauswahl),\nkann ScoreGDT mit einem Startargument ausgeführt werden, das hiermit gerniert werden kann.\nUm GDT-Konflikte des Praxisverwaltungssystems zu vermeiden, ist die Vergabe einer alternativen GDT-ID zu empfehlen.")
        labelAlternativeGdtId = QLabel("Alternative GDT-ID (altuelle Haupt ID: " + self.hauptId + ")")
        self.lineEditAlternativeGdtId = QLineEdit()

        dialogLayoutV.addWidget(labelBeschreibung)
        dialogLayoutH.addWidget(labelAlternativeGdtId)
        dialogLayoutH.addWidget(self.lineEditAlternativeGdtId)
        dialogLayoutV.addLayout(dialogLayoutH)
        dialogLayoutV.addWidget(self.buttonBox)
        self.setLayout(dialogLayoutV)

    def accept(self):
        if len(self.lineEditAlternativeGdtId.text()) != 8 and len(self.lineEditAlternativeGdtId.text()) != 0:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis", "Die alternative GDT-ID muss aus acht Zeichen bestehen.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditAlternativeGdtId.setFocus()
            self.lineEditAlternativeGdtId.selectAll()
        elif self.lineEditAlternativeGdtId.text() == self.hauptId:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis", "Die alternative GDT-ID muss sich von der Haupt-ID unterscheiden.", QMessageBox.StandardButton.Ok)
            mb.exec()
            self.lineEditAlternativeGdtId.setFocus()
            self.lineEditAlternativeGdtId.selectAll()
        else:
            self.done(1)