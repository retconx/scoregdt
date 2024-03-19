import xml.etree.ElementTree as ElementTree
werte = [
    [10, 10, 11, 12, 15, 16, 17, 18, 14, 15, 17, 18, 20, 22, 23, 25],
    [8, 9, 9, 9, 13, 13, 14, 15, 12, 13, 14, 15, 17, 18, 20, 21],
    [7, 7, 7, 8, 10, 11, 12, 12, 10, 11, 12, 13, 14, 15, 17, 18],
    [5, 6, 6, 6, 9, 9, 9, 10, 8, 9, 10, 10, 12, 13, 14, 15],

    [7, 8, 8, 9, 12, 13, 14, 15, 11, 12, 13, 15, 17, 18, 20, 22],
    [6, 6, 7, 7, 10, 11, 11, 12, 9, 10, 11, 12, 14, 15, 17, 18],
    [5, 5, 5, 6, 8, 8, 9, 10, 7, 8, 9, 10, 11, 13, 14, 15],
    [4, 4, 4, 5, 6, 7, 7, 8, 6, 7, 7, 8, 9, 10, 11, 12],

    [5, 6, 6, 7, 10, 11, 11, 12, 9, 10, 11, 12, 14, 16, 17, 20],
    [4, 4, 5, 5, 8, 8, 9, 10, 7, 8, 9, 10, 11, 13, 14, 16],
    [3, 3, 4, 4, 6, 7, 7, 8, 5, 6, 7, 8, 9, 10, 11, 13],
    [3, 3, 3, 3, 5, 5, 6, 6, 4, 5, 6, 6, 7, 8, 9, 10],

    [4, 4, 5, 5, 8, 8, 9, 10, 7, 8, 9, 10, 11, 13, 15, 17],
    [3, 3, 4, 4, 6, 6, 7, 8, 5, 6, 7, 8, 9, 10, 12, 14],
    [2, 2, 3, 3, 5, 5, 6, 6, 4, 5, 5, 6, 7, 8, 9, 11],
    [2, 2, 2, 2, 3, 4, 4, 5, 3, 4, 4, 5, 5, 6, 7, 8],

    [3, 3, 3, 4, 6, 7, 8, 9, 5, 6, 7, 8, 9, 11, 13, 15],
    [2, 2, 3, 3, 5, 5, 6, 6, 4, 5, 5, 6, 7, 8, 10, 12],
    [2, 2, 2, 2, 3, 4, 4, 5, 3, 4, 4, 5, 5, 7, 8, 9],
    [1, 1, 1, 2, 3, 3, 3, 4, 2, 3, 3, 4, 4, 5, 6, 7],

    [2, 2, 3, 3, 5, 5, 6, 7, 4, 5, 6, 7, 8, 9, 11, 13],
    [1, 2, 2, 2, 3, 4, 5, 5, 3, 4, 4, 5, 6, 7, 8, 10],
    [1, 1, 1, 2, 3, 3, 3, 4, 2, 3, 3, 4, 4, 5, 6, 8],
    [1, 1, 1, 1, 2, 2, 2, 3, 2, 2, 2, 3, 3, 4, 5, 6]
]

werteOp = [
    [37, 39, 40, 42, 41, 43, 44, 46, 37, 45, 53, 62, 37, 45, 53, 61], 
    [35, 36, 38, 39, 39, 40, 42, 43, 36, 43, 51, 59, 35, 43, 51, 59], 
    [32, 34, 35, 37, 36, 38, 39, 41, 34, 41, 49, 57, 34, 41, 48, 57], 
    [30, 32, 33, 34, 34, 35, 37, 38, 32, 39, 47, 55, 32, 39, 46, 55], 

    [27, 28, 30, 31, 34, 35, 37, 39, 30, 35, 41, 47, 34, 40, 46, 53], 
    [24, 25, 27, 28, 30, 32, 33, 35, 27, 32, 37, 43, 31, 36, 42, 48], 
    [21, 22, 24, 25, 27, 28, 30, 31, 25, 29, 34, 40, 28, 33, 38, 44], 
    [19, 20, 21, 22, 24, 25, 27, 28, 22, 26, 31, 36, 25, 30, 35, 40], 

    [19, 20, 21, 23, 27, 29, 30, 32, 24, 27, 31, 35, 31, 35, 39, 44], 
    [16, 17, 18, 19, 24, 25, 26, 28, 21, 23, 27, 30, 27, 30, 34, 38], 
    [14, 15, 15, 16, 20, 21, 22, 24, 17, 20, 23, 26, 23, 26, 29, 33], 
    [12, 12, 13, 14, 17, 18, 19, 20, 15, 17, 19, 22, 19, 22, 25, 29], 

    [13, 14, 15, 16, 22, 23, 25, 26, 19, 21, 23, 25, 28, 31, 34, 36], 
    [11, 11, 12, 13, 18, 19, 20, 22, 15, 17, 18, 20, 23, 25, 28, 30], 
    [9, 9, 10, 11, 15, 16, 17, 18, 12, 13, 15, 16, 19, 20, 22, 24], 
    [7, 7, 8, 8, 12, 13, 13, 14, 10, 11, 12, 13, 15, 16, 18, 20]

]
smokingspalten = [4, 5, 6, 7, 12, 13, 14, 15]
ages = [(65, 69), (60, 64), (55, 59), (50, 54), (45, 49), (40, 44)]
pressures = [(160, 179), (140, 159), (120, 139), (100, 119)]
nonHdls = [(3, 4), (4, 5), (5, 6), (6, 7)]

rootElement = ElementTree.Element("root")
pressureZaehler = 0
for zeile in range(24):
    if pressureZaehler == 4:
        pressureZaehler = 0
    nonHdlZaehler = 0
    for spalte in range(16):
        if nonHdlZaehler == 4:
            nonHdlZaehler = 0
        sex = 0
        if spalte > 7:
            sex = 1
        smoking = 0
        if spalte in smokingspalten:
            smoking = 1
        age = ages[int(zeile/4)]
        pressure = pressures[pressureZaehler]
        nonHdl = nonHdls[nonHdlZaehler]
        bedingungElement = ElementTree.Element("bedingung")
        regelElement = ElementTree.Element("regel")
        regelElement.text = "$id{104} ISTGLEICH " + str(sex)
        bedingungElement.append(regelElement)
        regelElement = ElementTree.Element("regel")
        regelElement.text = "$id{106} ISTGLEICH " + str(smoking)
        bedingungElement.append(regelElement)
        regelElement = ElementTree.Element("regel")
        regelElement.text = "$id{100} GROESSERGLEICHALS " + str(age[0])
        bedingungElement.append(regelElement)
        regelElement = ElementTree.Element("regel")
        regelElement.text = "$id{100} KLEINERGLEICHALS " + str(age[1])
        bedingungElement.append(regelElement)
        regelElement = ElementTree.Element("regel")
        regelElement.text = "$id{101} GROESSERGLEICHALS " + str(pressure[0])
        bedingungElement.append(regelElement)
        regelElement = ElementTree.Element("regel")
        regelElement.text = "$id{101} KLEINERGLEICHALS " + str(pressure[1])
        bedingungElement.append(regelElement)
        regelElement = ElementTree.Element("regel")
        regelElement.text = "$id{102} GROESSERGLEICHALS " + str(nonHdl[0])
        bedingungElement.append(regelElement)
        regelElement = ElementTree.Element("regel")
        regelElement.text = "$id{102} KLEINERALS " + str(nonHdl[1])
        bedingungElement.append(regelElement)
        wertElement = ElementTree.Element("wert")
        wertElement.text = str(werte[zeile][spalte])
        bedingungElement.append(wertElement)
        rootElement.append(bedingungElement)
        nonHdlZaehler += 1
    pressureZaehler += 1
et = ElementTree.ElementTree(rootElement)
ElementTree.indent(et)
et.write("score2B.xml", "utf-8", True)

smokingspaltenOp = [4, 5, 6, 7, 12, 13, 14, 15]
agesOp = [(85, 89), (80, 84), (75, 79), (70, 74)]
pressuresOp = [(160, 179), (140, 159), (120, 139), (100, 119)]
nonHdlsOp = [(3, 4), (4, 5), (5, 6), (6, 7)]

rootElement = ElementTree.Element("root")
pressureZaehler = 0
for zeile in range(16):
    if pressureZaehler == 4:
        pressureZaehler = 0
    nonHdlZaehler = 0
    for spalte in range(16):
        if nonHdlZaehler == 4:
            nonHdlZaehler = 0
        sex = 0
        if spalte > 7:
            sex = 1
        smoking = 0
        if spalte in smokingspaltenOp:
            smoking = 1
        age = agesOp[int(zeile/4)]
        pressure = pressuresOp[pressureZaehler]
        nonHdl = nonHdlsOp[nonHdlZaehler]
        bedingungElement = ElementTree.Element("bedingung")
        regelElement = ElementTree.Element("regel")
        regelElement.text = "$id{104} ISTGLEICH " + str(sex)
        bedingungElement.append(regelElement)
        regelElement = ElementTree.Element("regel")
        regelElement.text = "$id{106} ISTGLEICH " + str(smoking)
        bedingungElement.append(regelElement)
        regelElement = ElementTree.Element("regel")
        regelElement.text = "$id{100} GROESSERGLEICHALS " + str(age[0])
        bedingungElement.append(regelElement)
        regelElement = ElementTree.Element("regel")
        regelElement.text = "$id{100} KLEINERGLEICHALS " + str(age[1])
        bedingungElement.append(regelElement)
        regelElement = ElementTree.Element("regel")
        regelElement.text = "$id{101} GROESSERGLEICHALS " + str(pressure[0])
        bedingungElement.append(regelElement)
        regelElement = ElementTree.Element("regel")
        regelElement.text = "$id{101} KLEINERGLEICHALS " + str(pressure[1])
        bedingungElement.append(regelElement)
        regelElement = ElementTree.Element("regel")
        regelElement.text = "$id{102} GROESSERGLEICHALS " + str(nonHdl[0])
        bedingungElement.append(regelElement)
        regelElement = ElementTree.Element("regel")
        regelElement.text = "$id{102} KLEINERALS " + str(nonHdl[1])
        bedingungElement.append(regelElement)
        wertElement = ElementTree.Element("wert")
        wertElement.text = str(werteOp[zeile][spalte])
        bedingungElement.append(wertElement)
        rootElement.append(bedingungElement)
        nonHdlZaehler += 1
    pressureZaehler += 1
et = ElementTree.ElementTree(rootElement)
ElementTree.indent(et)
et.write("score2BOp.xml", "utf-8", True)