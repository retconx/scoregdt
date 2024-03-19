from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QLabel
)
from PySide6.QtGui import Qt, QDesktopServices

class UeberScoreGdt(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Über ScoreGDT")
        self.setFixedWidth(400)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.accepted.connect(self.accept) # type: ignore

        dialogLayoutV = QVBoxLayout()
        labelBeschreibung = QLabel("<span style='color:rgb(0,0,200);font-weight:bold'>Programmbeschreibung:</span><br>ScoreGDT ist eine eigenständig plattformunabhängig lauffähige Software zur elektronischen Dokumentation von medizinischen Scores in ein beliebiges Praxisverwaltungssystem.")
        labelBeschreibung.setAlignment(Qt.AlignmentFlag.AlignJustify)
        labelBeschreibung.setWordWrap(True)
        labelBeschreibung.setTextFormat(Qt.TextFormat.RichText)
        labelEntwickelsVon = QLabel("<span style='color:rgb(0,0,200);font-weight:bold'>Entwickelt von:</span><br>Fabian Treusch<br><a href='https://gdttools.de'>gdttools.de</a>")
        labelEntwickelsVon.setTextFormat(Qt.TextFormat.RichText)
        labelEntwickelsVon.linkActivated.connect(self.gdtToolsLinkGeklickt)
        labelHilfe = QLabel("<span style='color:rgb(0,0,200);font-weight:bold'>Hilfe:</span><br><a href='https://github.com/retconx/scoregdt/wiki'>ScoreGDT Wiki</a>")
        labelHilfe.setTextFormat(Qt.TextFormat.RichText)
        labelHilfe.linkActivated.connect(self.githubWikiLinkGeklickt)

        dialogLayoutV.addWidget(labelBeschreibung)
        dialogLayoutV.addWidget(labelEntwickelsVon)
        dialogLayoutV.addWidget(labelHilfe)
        dialogLayoutV.addWidget(self.buttonBox)
        self.setLayout(dialogLayoutV)

    def gdtToolsLinkGeklickt(self, link):
        QDesktopServices.openUrl(link)

    def githubWikiLinkGeklickt(self, link):
        QDesktopServices.openUrl(link)