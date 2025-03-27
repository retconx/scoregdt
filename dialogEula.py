import os, requests
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QLabel,
    QCheckBox,
    QTextEdit
)
from PySide6.QtCore import Qt

basedir = os.path.dirname(__file__)

class Eula(QDialog):
    def __init__(self, neueVersion=""):
        super().__init__()

        self.setWindowTitle("Endnutzer-Lizenzvereinbarung (EULA)")
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.accepted.connect(self.accept)

        dialogLayoutV = QVBoxLayout()
        labelAktualisiert = QLabel("ScoreGDT wurde erfolgreich auf Version " + neueVersion + " aktualisiert.")
        labelAktualisiert.setStyleSheet("font-weight:bold")
        response = requests.get("https://api.github.com/repos/retconx/scoregdt/releases/latest")
        body = response.json()["body"]
        aenderungen = str.split(body, "###")[1]
        aenderungenListe = str.split(aenderungen, "\r\n- ")
        datum = aenderungenListe[0].strip()
        aenderungenText = ""
        for i in range(len(aenderungenListe)):
            if i > 0:
                aenderungenText += "\u00b7 " + aenderungenListe[i]
                if i < len(aenderungenListe) - 1:
                    aenderungenText += "\n"
        labelAenderungen = QLabel("Änderungen vom " + datum + ":")
        labelAenderungen.setStyleSheet("font-weight:bold")
        self.labelAenderungenListe = QLabel(aenderungenText)
        labelBestaetigung = QLabel("Bitte bestätigen Sie, dass Sie die folgende Lizenzvereinbarung gelesen haben und dieser zustimmen.")
        text = ""
        self.textEditEula = QTextEdit()
        self.textEditEula.setReadOnly(True)
        with open(os.path.join(basedir, "eula.txt"), "r", encoding="utf_8") as f:  
            for zeile in f:
                text += zeile
        self.textEditEula.setText(text)
        self.textEditEula.setFixedHeight(300)

        self.checkBoxZustimmung = QCheckBox("Gelesen und zugestimmt")
        if neueVersion != "":
            dialogLayoutV.addWidget(labelAktualisiert)
            dialogLayoutV.addSpacing(10)
            dialogLayoutV.addWidget(labelAenderungen)
            dialogLayoutV.addWidget(self.labelAenderungenListe)
        dialogLayoutV.addWidget(labelBestaetigung, alignment=Qt.AlignmentFlag.AlignCenter)
        dialogLayoutV.addSpacing(10)
        dialogLayoutV.addWidget(self.textEditEula)
        dialogLayoutV.addSpacing(10)
        dialogLayoutV.addWidget(self.checkBoxZustimmung, alignment=Qt.AlignmentFlag.AlignCenter)
        dialogLayoutV.addSpacing(10)
        dialogLayoutV.addWidget(self.buttonBox, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(dialogLayoutV)
