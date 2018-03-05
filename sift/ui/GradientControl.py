import pyqtgraph as pg
from PyQt4 import QtGui, QtCore
import json
import os
import math
import numpy
# from ipywidgets import *
# from tkinter import *
import ast
from colormap import rgb2hex
from vispy.color.colormap import Colormap, BaseColormap, _mix_simple, _colormaps



class GradientControl(QtGui.QDialog):
    def __init__(self, doc, parent=None, **kwargs):
        super(GradientControl, self).__init__(parent)

        l = QtGui.QGridLayout()
        l.setSpacing(0)
        self.setLayout(l)
        self.doc = doc
        self.gData = {}
        self.autoImportData = {}
        self.ALL_COLORMAPS = self.doc.colormaps
        self.USER_MAPS = self.doc.usermaps

        self.ColorBar = pg.GradientWidget(orientation='bottom')
        self.ColorBar.hide()

        self.CloneButton = QtGui.QPushButton("Clone Gradient")
        self.CloneButton.clicked.connect(self.cloneGradient)

        self.ImportButton = QtGui.QPushButton("Import Gradient")
        self.ImportButton.clicked.connect(self.importButtonClick)

        # Create Gradient List and Related Functions
        self.List = QtGui.QListWidget()
        self.List.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.List.itemSelectionChanged.connect(self.updateColorBar)

        # Create SQRT Button and Related Functions
        self.sqrt = QtGui.QCheckBox("SQRT")
        self.sqrt.stateChanged.connect(self.sqrtAction)

        self.CloseButton = QtGui.QPushButton("Close")
        self.CloseButton.clicked.connect(self.closeButtonClick)

        # Create Delete Button and Related Functions
        self.DeleteButton = QtGui.QPushButton("Delete Gradient")
        self.DeleteButton.clicked.connect(self.deleteButtonClick)
        self.DeleteButton.hide()

        # Create Export Button and Related Functions
        self.ExportButton = QtGui.QPushButton("Export Gradient")
        self.ExportButton.clicked.connect(self.exportButtonClick)
        self.ExportButton.hide()

        self.SaveButton = QtGui.QPushButton("Save Gradient")
        self.SaveButton.clicked.connect(self.saveButtonClick)

        # Create Update Map Button & Related Functions
        #self.UpdateMapButton = QtGui.QPushButton("Clone Gradient")
        #self.UpdateMapButton.clicked.connect(self.updateButtonClick)


        print(self.USER_MAPS)

        self.updateListWidget()


        l.addWidget(self.ImportButton, 0, 0)
        l.addWidget(self.SaveButton, 0, 2)
        l.addWidget(self.sqrt, 1, 2)
        l.addWidget(self.ColorBar, 2, 1)
        l.addWidget(self.CloneButton, 1, 0)
        l.addWidget(self.List, 1, 1,3,1)
        l.addWidget(self.CloseButton, 6, 2)
        l.addWidget(self.ExportButton, 2, 2)
        l.addWidget(self.DeleteButton, 2, 0)
        #l.addWidget(self.UpdateMapButton, 2, 0)



        for map in self.USER_MAPS:
            if self.USER_MAPS[map].colors and (hasattr(self.USER_MAPS[map], "_controls")):
                self.importGradients(map, self.USER_MAPS[map].colors.hex, self.USER_MAPS[map]._controls, True)

        for map in self.ALL_COLORMAPS:
            if self.ALL_COLORMAPS[map].colors and (hasattr(self.ALL_COLORMAPS[map], "_controls")):
                if map not in self.USER_MAPS:
                    self.importGradients(map, self.ALL_COLORMAPS[map].colors.hex, self.ALL_COLORMAPS[map]._controls, False)

                #print("Imported Gradient!")


    def updateButtonClickOld(self):
        self.autoImportData[self.List.item(self.List.currentRow()).text()] = self.ColorBar.saveState()

        for item in self.autoImportData.keys():
            #print("Doing " + item)
            pointList = self.autoImportData[item]["ticks"]
            floats = []
            hex = []
            for point in pointList:
                floats.append(point[0])
                rgb = point[1]
                hexCode = rgb2hex(rgb[0], rgb[1], rgb[2])
                hex.append(hexCode)

            for i in range(len(floats)):
                for k in range(len(floats) - 1, i, -1):
                    if (floats[k] < floats[k - 1]):
                        self.bubbleSortSwap(floats, k, k - 1)
                        self.bubbleSortSwap(hex, k, k - 1)

            print(self.ALL_COLORMAPS[item].colors.hex)
            print(numpy.array(hex))
            print("\n")
            print(self.ALL_COLORMAPS[item]._controls)
            print(floats)
            print("\n")
            try:
                toAdd = Colormap(colors=hex, controls=floats)
                self.ALL_COLORMAPS[item] = toAdd
            except Exception as e:
                print("Error creating or setting colormap 1")
                print(e)
            #try:
            #    toAdd = Colormap(colors=hex, controls=floats)
            #    ALL_COLORMAPS[item] = toAdd
            #except Exception as e:
            #    print("Error updating gradient!")
            #    print(e)

        self.doc.update_colormaps(self.ALL_COLORMAPS)

        print(self.List.item(self.List.currentRow()).text())
        self.doc.change_colormap_for_layers(self.List.item(self.List.currentRow()).text())

    def updateButtonClick(self):
        print("Time to clone")

        cBar = self.getSelected()
        print(cBar)

    def bubbleSortSwap(self, A, x, y):
        tmp = A[x]
        A[x] = A[y]
        A[y] = tmp


    def saveButtonClick(self):
        print("ok")

        name = self.List.item(self.List.currentRow()).text()

        self.gData[name] = self.ColorBar.saveState()
        self.saveNewMap(self.ColorBar.saveState(), name)




    def cloneGradient(self):
        self.p = QtGui.QWidget()
        self.p.setWindowTitle('Save Gradient As:')
        self.p.textbox = QtGui.QLineEdit(self.p)
        self.p.textbox.move(20, 20)
        self.p.textbox.resize(280, 40)
        self.p.resize(320, 150)
        button = QtGui.QPushButton('Save', self.p)
        button.move(20, 80)
        button.clicked.connect(self.cloneGradient2)
        self.p.setWindowModality(QtCore.Qt.WindowModal)
        self.p.show()


    def getSelected(self):
        toReturn = []

        ListCount = self.List.count()

        index = 0
        while index < ListCount:
            if (self.List.item(index).isSelected()):
                toReturn.append(self.List.item(index))
            index = index + 1

        return toReturn


    def toRemoveDelete(self):
        toReturn = False

        ListCount = self.List.count()

        index = 0
        #self.List.item(index).text() in self.autoImportData.keys()
        while index < ListCount:
            if (self.List.item(index).isSelected()):
                if self.List.item(index).text() in self.autoImportData.keys():
                    toReturn = True
            index = index + 1

        return toReturn

    def cloneGradient2(self):
        SaveName = self.p.textbox.text()
        if SaveName in self.gData.keys():
            overwrite_msg = "There is already a save with this name. Would you like to Overwrite?"
            reply = QtGui.QMessageBox.question(self, 'Message',
                                               overwrite_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.Yes:
                if SaveName in self.autoImportData.keys():
                    QtGui.QMessageBox.information(self, "Error", "You cannot save a gradient with the same name as one of the internal gradients.")
                    self.p.close()
                    reply.done(1)
                    return

                self.gData[SaveName] = self.ColorBar.saveState()
                self.p.close()
                #self.saveData()
        else:

            if SaveName in self.autoImportData.keys():
                QtGui.QMessageBox.information(self, "Error",
                                              "You cannot save a gradient with the same name as one of the internal gradients.")
                self.p.close()
                return

            self.gData[SaveName] = self.ColorBar.saveState()
            #self.saveData()
            #self.p.close()
        self.updateListWidget(SaveName)
        self.saveNewMap(self.ColorBar.saveState(), SaveName)
        self.p.close()

    def saveNewMap(self, UpdatedMap, name):
        self.doc.updateGCColorMap(UpdatedMap, name)

    def importButtonClick(self):

        reply2 = QtGui.QMessageBox()
        reply2.setWindowTitle("File or Arrays?")
        reply2.setText("Would you like to import from a file or from point + color arrays?")
        reply2.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel)
        buttonY = reply2.button(QtGui.QMessageBox.Yes)
        buttonY.setText('File')
        buttonN = reply2.button(QtGui.QMessageBox.No)
        buttonN.setText('Arrays')

        reply2.exec_()

        if reply2.clickedButton() == buttonY:
            print("Starting File")
            fname = QtGui.QFileDialog.getOpenFileName(None, 'Get File', 'Export.txt')
            try:
                file = open(fname, "r")
                toImport = ast.literal_eval(file.read())

                self.gData.update(toImport)

                for impItem in toImport.keys():
                    self.saveNewMap(toImport[impItem], impItem)

                self.updateListWidget(impItem)
            except:
                print("Error opening file or reading!")
            print("Done")
        elif reply2.clickedButton() == buttonN:
            print("Going")
            pointArray = QtGui.QInputDialog.getText(self, self.tr("Input Points"),
                                                    self.tr("Point Array:"), QtGui.QLineEdit.Normal)

            if pointArray[0]:
                colorArray = QtGui.QInputDialog.getText(self, self.tr("Input Hex Colors"),
                                                        self.tr("Color Array:"), QtGui.QLineEdit.Normal)

                if colorArray[0]:
                    try:
                        points_values = pointArray[0]

                        points_values = points_values.replace('(', '')
                        points_values = points_values.replace(')', '')
                        points_values = points_values.replace('[', '')
                        points_values = points_values.replace(']', '')
                        points_values = points_values.replace('{', '')
                        points_values = points_values.replace('}', '')
                        points_values = points_values.split(',')

                        points_values = [float(i) for i in points_values]

                        colors_values = colorArray[0]

                        colors_values = colors_values.replace('(', '')
                        colors_values = colors_values.replace(')', '')
                        colors_values = colors_values.replace('[', '')
                        colors_values = colors_values.replace(']', '')
                        colors_values = colors_values.replace('{', '')
                        colors_values = colors_values.replace('}', '')
                        colors_values = colors_values.replace('\'', '')
                        colors_values = colors_values.replace(' ', '')
                        colors_values = colors_values.split(',')

                        data = {}

                        for i in range(len(points_values)):
                            data[points_values[i]] = colors_values[i]

                        newName = QtGui.QInputDialog.getText(self, self.tr("Input ColorBar Name"),
                                                             self.tr("Name:"), QtGui.QLineEdit.Normal)

                        if newName[0]:
                            newWidget = pg.GradientWidget()
                            newWidget.hide()
                            for key in data:
                                newWidget.addTick(key, QtGui.QColor(data[key]), True)
                            self.gData[newName[0]] = newWidget.saveState()
                            self.saveNewMap(newWidget.saveState(), newName[0])
                            #self.saveData()
                            self.updateListWidget(newName[0])


                    except:
                        QtGui.QMessageBox.information(self, "Error", "Error loading the arrays!")

    def importGradients(self, name, hex, floats, editable):
        try:
            data = {}

            for i in range(len(hex)):
                data[floats.astype(float)[i]] = hex[i]

            newWidget = pg.GradientWidget()
            newWidget.hide()
            for key in data:
                newWidget.addTick(key, QtGui.QColor(data[key]), movable=editable)
            #self.gData[name] = newWidget.saveState()

            if editable:
                self.gData[name] = newWidget.saveState()
            else:
                self.autoImportData[name] = newWidget.saveState()

            self.updateListWidget()

        except Exception as e:
            print(e)
            #QtGui.QMessageBox.information(self, "Error", "Error loading the arrays!")

    def closeButtonClick(self):
        self.done(0)

    def updateListWidget(self, toShow = None):
        # TODO Show selected widget
        self.List.clear()
        self.ExportButton.hide()
        self.DeleteButton.hide()

        totalCount = 0
        corVal = 0
        for key2 in self.autoImportData.keys():
            self.List.addItem(key2)
            totalCount = totalCount + 1
            if toShow is not None and key2 == toShow:
                corVal = totalCount

        self.List.addItem("----------------------------- Below Are Custom ColorMaps -----------------------------")
        totalCount = totalCount + 1

        for key in self.gData.keys():
            self.List.addItem(key)
            totalCount = totalCount + 1
            if toShow is not None and key == toShow:
                corVal = totalCount

        if toShow is not None:
            self.List.setCurrentRow(corVal, QtGui.QItemSelectionModel.Select)


    def updateColorBar(self):
        self.DeleteButton.show()
        self.sqrt.show()
        self.CloneButton.show()
        self.SaveButton.show()
        self.ExportButton.show()
        self.ColorBar.show()
        self.sqrt.setCheckState(0)

        if self.List.item(self.List.currentRow()).text() in self.gData.keys():
            NewBar = self.gData[self.List.item(self.List.currentRow()).text()]
            #TODO change this
            self.ColorBar.restoreState(NewBar)

        if self.List.item(self.List.currentRow()).text() in self.autoImportData.keys():
            NewBar = self.autoImportData[self.List.item(self.List.currentRow()).text()]
            #TODO change this
            self.ColorBar.restoreState(NewBar)

        SelectedThings = self.getSelected()

        print(SelectedThings)

        if len(SelectedThings) > 1:
            self.ColorBar.hide()
            self.SaveButton.hide()
            self.sqrt.hide()
        else:
            self.ColorBar.show()
            self.SaveButton.show()
            self.sqrt.show()

        showDel = True
        for thing in SelectedThings:
            print(thing.text())
            if thing.text() in self.autoImportData.keys():
                showDel = False

        if showDel is True:
            self.DeleteButton.show()
            self.sqrt.show()
            self.SaveButton.show()
        else:
            self.DeleteButton.hide()
            self.sqrt.hide()
            self.SaveButton.hide()

        if SelectedThings[0].text() == "----------------------------- Below Are Custom ColorMaps -----------------------------":
            self.DeleteButton.hide()
            self.sqrt.hide()
            self.CloneButton.hide()
            self.SaveButton.hide()
            self.ExportButton.hide()

    def sqrtAction(self):
        if self.sqrt.isChecked() == True:
            tickList = self.ColorBar.listTicks()
            for tick in tickList:
                self.ColorBar.setTickValue(tick[0], math.sqrt(self.ColorBar.tickValue(tick[0])))
        else:
            tickList = self.ColorBar.listTicks()
            for tick in tickList:
                self.ColorBar.setTickValue(tick[0], self.ColorBar.tickValue(tick[0]) * self.ColorBar.tickValue(tick[0]))

    def deleteButtonClick(self):
        block = self.toRemoveDelete()
        if block is True:
            QtGui.QMessageBox.information(self, "Please Unselect Gradient(s)", "You have a \"native\" gradient selected. Please "
                                                                               "unselect it before deleting.")
            return

        selectedGradients = self.getSelected()
        toPrint = ""
        for index in selectedGradients:
            toPrint = toPrint + index.text() + ", "

        toPrint = toPrint[:-2]

        delete_msg = "Please confirm you want to delete the Gradient(s): " + toPrint
        reply = QtGui.QMessageBox.question(self, 'Message',
                                           delete_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            for index in selectedGradients:
                del self.gData[index.text()]
                self.doc.removeGCColorMap(index.text())
            self.updateListWidget()
            #self.saveData()

    def exportButtonClick(self):
        selectedGradients = self.getSelected()
        fname = QtGui.QFileDialog.getSaveFileName(None, 'Save As', 'Export.txt')
        toExport = set()
        for index in selectedGradients:
            toExport.add(index.text())
        #done = {k: self.gData[k] for k in self.gData.keys() & toExport}
        done = {}

        for k in self.gData.keys():
            if k in toExport:
                done[k] = self.gData[k]

        for k in self.autoImportData.keys():
            if k in toExport:
                done[k] = self.autoImportData[k]
        try:
            file = open(fname, 'w')
            file.write(str(done))
        except Exception as e:
            print("Error opening or writing!")
            print(e)


def main():
    app = QtGui.QApplication([])
    w = GradientControl()
    w.show()
    app.exec_()
    return 0


if __name__ == '__main__':
    sys.exit(main())
