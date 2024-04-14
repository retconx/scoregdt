import os, sys
import class_score, logger
from xml.etree import ElementTree
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QMessageBox, 
    QPushButton
)

from PySide6.QtGui import QFont

class EinstellungenFavoriten(QDialog):
    def __init__(self, configPfad:str, scoresPfad:str):
        super().__init__()
        self.configPfad = configPfad
        self.scoresPfad = scoresPfad
        self.root = class_score.Score.getGesamtRoot(scoresPfad)
        self.favoritenNamen = class_score.Score.getFavoriten(configPfad)
        self.gruppen = []
        self.namenInformationen = []
        self.scoreGruppen = {} # key: Gruppe, value: Liste von Namen
        for scoreElement in self.root.findall("score"):
            gruppe = str(scoreElement.get("gruppe"))
            if not gruppe in self.gruppen:
                self.gruppen.append(gruppe)
        self.gruppen.sort()
        for gruppe in self.gruppen:
            self.namenInformationen.clear()
            for scoreElement in self.root.findall("score"):
                tempGruppe = str(scoreElement.get("gruppe"))
                name = str(scoreElement.get("name"))
                information = str(scoreElement.find("information").text) # type: ignore
                if gruppe == tempGruppe:
                    self.namenInformationen.append((name, information))
            self.namenInformationen = sorted(self.namenInformationen, key=lambda name:name[0].casefold())
            self.scoreGruppen[gruppe] = self.namenInformationen.copy()
        
        self.fontNormal = QFont()
        self.fontNormal.setBold(False)
        self.fontBold = QFont()
        self.fontBold.setBold(True)
        self.setFixedSize(600,800)

        self.setWindowTitle("Favoriten")
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        self.buttonBox.accepted.connect(self.accept) # type:ignore
        self.buttonBox.rejected.connect(self.reject) # type:ignore

        dialogLayoutV = QVBoxLayout()
        dialogAlleLayoutH = QHBoxLayout()
        self.pushButtonAlleAuswaehlen = QPushButton("Alle auswählen")
        self.pushButtonAlleAuswaehlen.setFont(self.fontNormal)
        self.pushButtonAlleAuswaehlen.clicked.connect(lambda checked = False, checkState = Qt.CheckState.Checked: self.pushButtonAlleAusAbwaehlenClicked(checked, checkState))
        self.pushButtonAlleAbwaehlen = QPushButton("Alle abwählen")
        self.pushButtonAlleAbwaehlen.setFont(self.fontNormal)
        self.pushButtonAlleAbwaehlen.clicked.connect(lambda checked = False, checkState = Qt.CheckState.Unchecked: self.pushButtonAlleAusAbwaehlenClicked(checked, checkState))
        self.treeWidget = QTreeWidget()
        self.treeWidget.itemClicked.connect(self.treeWidgetItemClicked)
        self.treeWidget.setColumnCount(1)
        self.treeWidget.setHeaderLabel("Score-Gruppen")
        for gruppe in self.scoreGruppen:
            gruppeItem = QTreeWidgetItem(self.treeWidget, [gruppe])
            gruppeItem.setExpanded(True)
            self.treeWidget.addTopLevelItem(gruppeItem)
            for nameInformation in self.scoreGruppen[gruppe]:
                nameItem = QTreeWidgetItem(gruppeItem, [nameInformation[0]])
                nameItem.setToolTip(0, nameInformation[1])
                checkState = Qt.CheckState.Unchecked
                if nameInformation[0] in self.favoritenNamen:
                    checkState = Qt.CheckState.Checked
                nameItem.setCheckState(0, checkState)
                self.treeWidget.addTopLevelItem(nameItem)

        self.aktualisiereToplevelCheckstate()
        dialogAlleLayoutH.addWidget(self.pushButtonAlleAuswaehlen)
        dialogAlleLayoutH.addWidget(self.pushButtonAlleAbwaehlen)
        dialogLayoutV.addLayout(dialogAlleLayoutH)
        dialogLayoutV.addWidget(self.treeWidget)
        dialogLayoutV.addWidget(self.buttonBox)

        self.setLayout(dialogLayoutV)

    def aktualisiereToplevelCheckstate(self):
        for i in range(self.treeWidget.topLevelItemCount()):
            if self.treeWidget.topLevelItem(i).childCount() > 0:
                for j in range(self.treeWidget.topLevelItem(i).childCount()):
                    childItem = self.treeWidget.topLevelItem(i).child(j)
                    self.treeWidgetItemClicked(childItem)

    def treeWidgetItemClicked(self, item:QTreeWidgetItem):
        if item.childCount() > 0: # Toplevel
            if item.checkState(0) == Qt.CheckState.Checked:
                for i in range(item.childCount()):
                    item.child(i).setCheckState(0, Qt.CheckState.Checked)

            else:
                for i in range(item.childCount()):
                    item.child(i).setCheckState(0, Qt.CheckState.Unchecked)
        else: # Child 
            parent = item.parent()
            checkedChildren = 0
            for i in range(item.parent().childCount()):
                if parent.child(i).checkState(0) == Qt.CheckState.Checked:
                    checkedChildren += 1
            if checkedChildren == parent.childCount():
                parent.setCheckState(0, Qt.CheckState.Checked)
            elif checkedChildren > 0:
                parent.setCheckState(0, Qt.CheckState.PartiallyChecked)
            else:
                parent.setCheckState(0, Qt.CheckState.Unchecked)
    
    def pushButtonAlleAusAbwaehlenClicked(self, checked, checkState):
        for i in range(self.treeWidget.topLevelItemCount()):
            self.treeWidget.topLevelItem(i).setCheckState(0, checkState)
            self.treeWidgetItemClicked(self.treeWidget.topLevelItem(i))

    def accept(self):
        # Prüfen, ob mindestens ein Score ausgewählt
        anzahl = 0
        for i in range(self.treeWidget.topLevelItemCount()):
            if self.treeWidget.topLevelItem(i).checkState(0) == Qt.CheckState.Checked or self.treeWidget.topLevelItem(i).checkState(0) == Qt.CheckState.PartiallyChecked:
                anzahl += 1
        if anzahl > 0:
            favoritenNamen = []
            for i in range(self.treeWidget.topLevelItemCount()):
                gruppeItem = self.treeWidget.topLevelItem(i)
                for j in range(gruppeItem.childCount()):
                    nameItem = gruppeItem.child(j)
                    if nameItem.checkState(0) == Qt.CheckState.Checked:
                        favoritenNamen.append(nameItem.text(0))
            try:
                logger.logger.info("1")
                favoritenElement = ElementTree.Element("favoriten")
                logger.logger.info("2")
                tree = ElementTree.ElementTree(favoritenElement)
                logger.logger.info("3")
                for favorit in favoritenNamen:
                    logger.logger.info("4")
                    favoritElement = ElementTree.Element("favorit")
                    logger.logger.info("5")
                    favoritElement.text = favorit
                    logger.logger.info("6")
                    favoritenElement.append(favoritElement)
                    logger.logger.info("7")
                ElementTree.indent(tree)
                logger.logger.info("8")
                tree.write(os.path.join(self.configPfad, "favoriten.xml"), "utf-8", True)
                logger.logger.info("9")
                mb = QMessageBox(QMessageBox.Icon.Question, "Hinweis von ScoreGDT", "Favoriten erfolgreich gespeichert.\n Soll ScoreGDT neu gestartet werden?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                mb.setDefaultButton(QMessageBox.StandardButton.Yes)
                mb.button(QMessageBox.StandardButton.Yes).setText("Ja")
                mb.button(QMessageBox.StandardButton.No).setText("Nein")
                if mb.exec() == QMessageBox.StandardButton.Yes:
                    os.execl(sys.executable, __file__, *sys.argv)
            except Exception as e:
                logger.logger.error("Fehler beim Speichern der Favoriten in " + os.path.join(self.configPfad, "favoriten.xml") + ": " + str(e))
                mb = QMessageBox(QMessageBox.Icon.Warning, "Hinweis von ScoreGDT", "Fehler beim Speichern der Favoriten: " + str(e), QMessageBox.StandardButton.Ok)
                mb.exec()
            self.done(1)
        else:
            mb = QMessageBox(QMessageBox.Icon.Information, "Hinweis von ScoreGDT", "Mindestens ein Score muss ausgewählt sein.", QMessageBox.StandardButton.Ok)
            mb.exec()