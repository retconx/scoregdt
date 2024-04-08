import configparser, os
from xml.etree import ElementTree
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QRadioButton,
    QButtonGroup, 
    QFrame
)

class ScoreAuswahl(QDialog):
    def __init__(self, root:ElementTree.Element, standardScore:str):
        super().__init__()
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        
        self.setWindowTitle("ScoreGDT - Score auswählen")
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        self.aktuellGewaehlterScore = ""

        # Scores auslesen
        scoreGruppennamen = []
        for scoreElement in root.findall("score"):
            gruppe = str(scoreElement.get("gruppe"))
            if not gruppe in scoreGruppennamen:
                scoreGruppennamen.append(gruppe)
        scoreGruppennamen.sort()
        scoreGruppen = {}
        scoreNamenUndInfos = []
        for scoreGruppenname in scoreGruppennamen:
            scoreNamenUndInfos.clear()
            for scoreElement in root.findall("score"):
                gruppe = str(scoreElement.get("gruppe"))
                name = str(scoreElement.get("name"))
                information = str(scoreElement.find("information").text) # type: ignore
                if gruppe == scoreGruppenname:
                    scoreNamenUndInfos.append((name, information))
                    scoreNamenUndInfos = sorted(scoreNamenUndInfos, key=lambda name: name[0].casefold())
            scoreGruppen[scoreGruppenname] = scoreNamenUndInfos.copy()
        # Formular aufbauen    
        dialogLayoutV = QVBoxLayout()
        buttonGroup = QButtonGroup()
        buttonGroup.setParent(self)
        self.radioButtonsScore = []
        radioButtonNr = 0
        for scoreGruppe in scoreGruppen:
            groupBoxScoreGruppe = QGroupBox(scoreGruppe)
            groupBoxScoreGruppe.setFont(self.fontBold)
            groupBoxScoreGruppeLayoutG = QGridLayout()
            i = 0
            for score in scoreGruppen[scoreGruppe]:
                tempRadioButtonScore = QRadioButton(score[0])
                tempRadioButtonScore.setFont(self.fontNormal)
                if score[0] == standardScore:
                    tempRadioButtonScore.setChecked(True)
                    self.aktuellGewaehlterScore = score[0]
                tempRadioButtonScore.clicked.connect(lambda checked=False, rn = radioButtonNr: self.radioButtonClicked(checked, rn))
                buttonGroup.addButton(tempRadioButtonScore)
                self.radioButtonsScore.append(tempRadioButtonScore)
                groupBoxScoreGruppeLayoutG.addWidget(tempRadioButtonScore, i, 0)
                tempLabelInfo = QLabel(score[1])
                tempLabelInfo.setFont(self.fontNormal)
                groupBoxScoreGruppeLayoutG.addWidget(tempLabelInfo, i, 1, alignment=Qt.AlignmentFlag.AlignLeft)
                i += 1
                radioButtonNr += 1
            groupBoxScoreGruppe.setLayout(groupBoxScoreGruppeLayoutG)
            dialogLayoutV.addWidget(groupBoxScoreGruppe)
        dialogLayoutV.addWidget(self.buttonBox)
        self.setLayout(dialogLayoutV)

        for rb in self.radioButtonsScore:
            rb.setFixedWidth(240)
        
        # Ggf ersten RadioButton aktivieren
        if self.aktuellGewaehlterScore == "":
            self.radioButtonsScore[0].setChecked(True)
            self.aktuellGewaehlterScore = self.radioButtonsScore[0].text()
    
    def radioButtonClicked(self, checked, radioButtoNr):
        self.aktuellGewaehlterScore = self.radioButtonsScore[radioButtoNr].text()
    
    def accept(self):
        self.done(1)