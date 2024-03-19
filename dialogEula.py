import os
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
        labelAktualisiert = QLabel("SignoGDT wurde erfolgreich auf Version " + neueVersion + " aktualisiert.")
        labelAktualisiert.setStyleSheet("font-weight:bold")
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
        dialogLayoutV.addWidget(labelBestaetigung, alignment=Qt.AlignmentFlag.AlignCenter)
        dialogLayoutV.addSpacing(10)
        dialogLayoutV.addWidget(self.textEditEula)
        dialogLayoutV.addSpacing(10)
        dialogLayoutV.addWidget(self.checkBoxZustimmung, alignment=Qt.AlignmentFlag.AlignCenter)
        dialogLayoutV.addSpacing(10)
        dialogLayoutV.addWidget(self.buttonBox, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(dialogLayoutV)
