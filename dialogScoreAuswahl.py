import os, configparser, sys
import class_trends
from xml.etree import ElementTree
from PySide6.QtGui import QFont, QPalette, QColor
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
    QScrollArea,
    QFrame,
    QPushButton,
    QCheckBox,
    QHBoxLayout, 
    QMessageBox
)

class ScoreAuswahl(QDialog):
    # Mainwindow zentrieren
    def resizeEvent(self, e):
        ag = self.screen().availableGeometry()
        screenHoehe = ag.size().height()
        self.setMinimumHeight(screenHoehe - 100)

    def __init__(self, root:ElementTree.Element, standardScore:str, configPath:str):
        super().__init__()
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)

        self.configPath = configPath

        # config.ini lesen
        configIni = configparser.ConfigParser()
        configIni.read(os.path.join(configPath, "config.ini"))
        self.trendverzeichnis = configIni["Allgemein"]["trendverzeichnis"]
        
        self.setWindowTitle("ScoreGDT - Score auswählen")
        minimumWidth = 1100
        self.setMinimumWidth(minimumWidth)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.aktuellGewaehlterScore = ""
        self.aktuellGewaehlteScoreNummer = 0

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
        trendLayout = QGridLayout()
        self.buttonTrendAusdruck = QPushButton("Scoreauswahl für Trendberechnung")
        self.buttonTrendAusdruck.setFont(self.fontBold)
        self.buttonTrendAusdruck.setFixedWidth(300)
        self.buttonTrendAusdruck.setCheckable(True)
        self.buttonTrendAusdruck.setEnabled(os.path.exists(os.path.join(self.trendverzeichnis, "trends.xml")))
        if not os.path.exists(os.path.join(self.trendverzeichnis, "trends.xml")):
            self.buttonTrendAusdruck.setToolTip("Bisher wurde kein Score für die Trendberechnung gespeichert.")
        self.buttonTrendAusdruck.clicked.connect(self.buttonTrendAusdruckClicked)
        self.groupBoxGeriGDT = QGroupBox("Geriatrisches Basisassessment")
        self.groupBoxGeriGDT.setFont(self.fontBold)
        self.groupBoxGeriGDT.setVisible(False)
        groupBoxGeriGDTLayoutH = QHBoxLayout()
        self.checkBoxGeriGDT = QCheckBox("Barthel-Index und Timed \"Up and Go\"-Test in Trendberechnung einbeziehen (Daten von GeriGDT)")
        self.checkBoxGeriGDT.setFont(self.fontNormal)
        self.checkBoxGeriGDT.clicked.connect(self.checkBoxGeriGDTClicked)
        groupBoxGeriGDTLayoutH.addWidget(self.checkBoxGeriGDT)
        self.groupBoxGeriGDT.setLayout(groupBoxGeriGDTLayoutH)
        trendLayout.addWidget(self.buttonTrendAusdruck, 0, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        trendLayout.addWidget(self.groupBoxGeriGDT, 1, 0, alignment=Qt.AlignmentFlag.AlignLeft)
    
        frame = QFrame()
        frameLayoutV = QVBoxLayout()
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)

        dialogLayoutV = QVBoxLayout()
        self.buttonGroup = QButtonGroup()
        self.buttonGroup.setParent(self)
        self.radioButtonsScore = []
        radioButtonNr = 0
        for scoreGruppe in scoreGruppen:
            groupBoxScoreGruppe = QGroupBox(scoreGruppe)
            paletteGroupBox = groupBoxScoreGruppe.palette()
            groupBoxWindowColor = paletteGroupBox.window().color()
            paletteGroupBox.setColor(QPalette.Window, groupBoxWindowColor) # type: ignore
            groupBoxScoreGruppe.setFont(self.fontBold)
            groupBoxScoreGruppeLayoutG = QGridLayout()
            i = 0
            for score in scoreGruppen[scoreGruppe]:
                tempRadioButtonScore = QRadioButton(score[0])
                tempRadioButtonScore.setFont(self.fontNormal)
                tempRadioButtonScore.setPalette(paletteGroupBox)
                if score[0] == standardScore:
                    tempRadioButtonScore.setChecked(True)
                    self.aktuellGewaehlterScore = score[0]
                    self.aktuellGewaehlteScoreNummer = radioButtonNr
                tempRadioButtonScore.clicked.connect(lambda checked=False, rn = radioButtonNr: self.radioButtonClicked(checked, rn))
                self.buttonGroup.addButton(tempRadioButtonScore)
                self.radioButtonsScore.append(tempRadioButtonScore)
                groupBoxScoreGruppeLayoutG.addWidget(tempRadioButtonScore, i, 0)
                tempLabelInfo = QLabel(score[1])
                tempLabelInfo.setFont(self.fontNormal)
                groupBoxScoreGruppeLayoutG.addWidget(tempLabelInfo, i, 1, alignment=Qt.AlignmentFlag.AlignLeft)
                i += 1
                radioButtonNr += 1
            groupBoxScoreGruppe.setLayout(groupBoxScoreGruppeLayoutG)
            dialogLayoutV.addWidget(groupBoxScoreGruppe)

        frame.setLayout(dialogLayoutV)
        scrollArea.setWidget(frame)
        
        frameLayoutV.addLayout(trendLayout)
        frameLayoutV.addWidget(scrollArea)
        frameLayoutV.addWidget(self.buttonBox)
        self.setLayout(frameLayoutV)
        
        for rb in self.radioButtonsScore:
            rb.setFixedWidth(280)
        
        # Ggf ersten RadioButton aktivieren
        if self.aktuellGewaehlterScore == "":
            self.radioButtonsScore[0].setChecked(True)
            self.aktuellGewaehlterScore = self.radioButtonsScore[0].text()
            self.aktuellGewaehlteScoreNummer = 0

    def buttonTrendAusdruckClicked(self, checked):
        self.buttonGroup.setExclusive(not checked)
        self.groupBoxGeriGDT.setVisible(checked)
        for rb in self.radioButtonsScore:
            rb.setChecked(False)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(not checked)
        if checked:
            palette = QPalette()
            colorWindow = palette.window().color()
            palette.setColor(QPalette.Active, QPalette.Window, colorWindow) # type: ignore
            try:
                tests = class_trends.getTrends(self.trendverzeichnis)
                testNamen = [str(test.get("name")) for test in tests.findall("test")]
                testTools = [str(test.get("tool")) for test in tests.findall("test")]
                for rb in self.radioButtonsScore:
                    rb.setEnabled(rb.text() in testNamen)
                    if not rb.text() in testNamen:
                        rb.setPalette(palette)
                self.checkBoxGeriGDT.setEnabled(class_trends.GdtTool.GERIGDT.value in testTools)
            except class_trends.XmlPfadExistiertNichtError as e:
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Problem beim Laden der Trenddaten: " + str(e), QMessageBox.StandardButton.Ok)
                mb.exec()
        else:
            for rb in self.radioButtonsScore:
                rb.setEnabled(True)
            self.radioButtonsScore[self.aktuellGewaehlteScoreNummer].setChecked(True)

    def radioButtonClicked(self, checked, radioButtoNr):
        if not self.buttonTrendAusdruck.isChecked():
            self.aktuellGewaehlteScoreNummer = radioButtoNr
            self.aktuellGewaehlterScore = self.radioButtonsScore[radioButtoNr].text()
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            if not self.checkBoxGeriGDT.isChecked():
                self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(self.getAnzahlCheckedRadiobuttons() > 0)
    
    def checkBoxGeriGDTClicked(self, checked):
        if self.getAnzahlCheckedRadiobuttons() == 0:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(checked)
    
    def getAnzahlCheckedRadiobuttons(self):
        anzahlCheckedRadioButtons = 0
        for rb in self.radioButtonsScore:
            anzahlCheckedRadioButtons += int(rb.isChecked())
        return anzahlCheckedRadioButtons
    
    def accept(self):
        self.done(1)