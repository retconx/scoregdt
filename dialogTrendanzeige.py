import configparser, os, sys
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
import class_trends

class Trendanzeige(QDialog):
    def __init__(self, ausgewaehlteTests:list):
        super().__init__()
        self.ausgewaehlteTests = ausgewaehlteTests

        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)

        self.setWindowTitle("Score-Trend")
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText("Senden")
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        trendLayout = QGridLayout()
        trendLayout.setHorizontalSpacing(20)
        zeile = 0
        gruppen = []
        for test in self.ausgewaehlteTests:
            if test.getGruppe() not in gruppen:
                gruppen.append(test.getGruppe())
        gruppen.sort()
        for gruppe in gruppen:
            gruppeLabel = QLabel(gruppe)
            gruppeLabel.setFont(self.fontBold)
            gruppeLabel.setStyleSheet("color:rgb(0,0,200)")
            trendLayout.addWidget(gruppeLabel, zeile, 0, 1, 3)
            zeile += 1
            for test in self.ausgewaehlteTests:
                if test.getGruppe() == gruppe:
                    testLabel = QLabel(test.getName())
                    testLabel.setFont(self.fontBold)
                    trendLayout.addWidget(testLabel, zeile, 0, 1, 3)
                    zeile += 1
                    trends = test.getLetzteTrends()
                    dLabel = QLabel("Datum")
                    dLabel.setFont(self.fontBold)
                    eLabel = QLabel("Ergebnis")
                    eLabel.setFont(self.fontBold)
                    iLabel = QLabel("Interpretation")
                    iLabel.setFont(self.fontBold)
                    trendLayout.addWidget(dLabel, zeile, 0)
                    trendLayout.addWidget(eLabel, zeile, 1)
                    trendLayout.addWidget(iLabel, zeile, 2)
                    zeile += 1
                    for trend in trends:
                        datum = trend.getTrend()["datum"].strftime("%d.%m.%Y")
                        ergebnis = trend.getTrend()["ergebnis"]
                        interpretation = trend.getTrend()["interpretation"]
                        datumLabel = QLabel(datum)
                        ergebnisLabel = QLabel(ergebnis)
                        interpretationLabel = QLabel(interpretation)
                        trendLayout.addWidget(datumLabel, zeile, 0)
                        trendLayout.addWidget(ergebnisLabel, zeile, 1)
                        trendLayout.addWidget(interpretationLabel, zeile, 2)
                        zeile += 1
                    spaceLabel = QLabel(" ")
                    trendLayout.addWidget(spaceLabel, zeile, 0, 1, 3)
                    zeile += 2
        
        dialogLayoutV.addLayout(trendLayout)
        dialogLayoutV.addWidget(self.buttonBox)

        self.setLayout(dialogLayoutV)
            
    def accept(self):
        self.done(1)