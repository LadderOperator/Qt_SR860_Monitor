# This Python file uses the following encoding: utf-8
import sys
import os
import SR860
import time

from PySide2.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide2.QtCore import QFile, Slot, QTimer, QThread, Qt
from PySide2.QtUiTools import QUiLoader

colorSetting = {
        False: "background-color: rgb(120, 120, 120);",
        True: "background-color: rgb(255, 0, 0);"
    }

connectSetting = {
        False: "background-color: rgb(0, 255, 0);",
        True: "background-color: rgb(120, 120, 120);"
    }


class updateTextTask(QThread):

    def __init__(self, winObj):
        QThread.__init__(self)
        self.winObj = winObj

    @Slot()
    def run(self):

        while not self.isInterruptionRequested():

            self.device = SR860.SR860Device(self.winObj.IPaddress.text())

            XYRTDict = self.device.queryXYRT()

            if XYRTDict != 42:

                self.winObj.X_VAL.setText("%s" % XYRTDict["X"]["val"])
                self.winObj.X_UNIT.setText("%s" % XYRTDict["X"]["unit"])
                self.winObj.Y_VAL.setText("%s" % XYRTDict["Y"]["val"])
                self.winObj.Y_UNIT.setText("%s" % XYRTDict["Y"]["unit"])
                self.winObj.R_VAL.setText("%s" % XYRTDict["R"]["val"])
                self.winObj.R_UNIT.setText("%s" % XYRTDict["R"]["unit"])
                self.winObj.T_VAL.setText("%s" % XYRTDict["Theta"]["val"])
                self.winObj.T_UNIT.setText("%s" % XYRTDict["Theta"]["unit"])

            res = self.device.querySensitivity()

            if res != 42:
                self.winObj.currentSensi.setText(
                    self.winObj.Sensitivity.itemText(res)
                )

            res = self.device.queryPhase()

            if res != 42:
                self.winObj.refPhase.setText("%s Deg" % res)

            self.winObj.statusLight.setVisible(
                res != 42 and XYRTDict != 42
            )

            time.sleep(0.1)

    @Slot()
    def stop(self):
        print("Thread 1 Stopped.")
        self.requestInterruption()
        self.wait()


class updateLightTask(QThread):

    def __init__(self, winObj):
        QThread.__init__(self)
        self.winObj = winObj
        self.OLLightMap = {
            "inputRange": self.winObj.inRanOL,
            "extRefUnlocked": self.winObj.extRefULOL,
            "CH1Output": self.winObj.CH1OL,
            "CH2Output": self.winObj.CH2OL,
            "dataCH1Output": self.winObj.DCH1OL,
            "dataCH2Output": self.winObj.DCH2OL,
            "dataCH3Output": self.winObj.DCH3OL,
            "dataCH4Output": self.winObj.DCH4OL
        }

    @Slot()
    def run(self):

        while not self.isInterruptionRequested():

            self.device = SR860.SR860Device(self.winObj.IPaddress.text())

            self.OLStatus = self.device.queryOVLoad()

            if self.OLStatus != 42:

                for OLName in self.OLLightMap.keys():
                    self.OLLightMap[OLName].setVisible(self.OLStatus[OLName])
                    time.sleep(0.02)

            self.winObj.statusLight.setStyleSheet(
                connectSetting[self.OLStatus == 42]
            )

            #time.sleep(0.1)

    @Slot()
    def stop(self):
        print("Thread 2 Stopped.")
        self.requestInterruption()
        self.wait()


class Window(QMainWindow):

    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        self.loader = QUiLoader()
        self.ui_path = os.path.join(os.path.dirname(__file__), "form.ui")
        self.ui_file = QFile(self.ui_path)
        self.ui_file.open(QFile.ReadOnly)

        self.window = self.loader.load(self.ui_file)

        self.window.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.window.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
        self.window.setWindowFlag(Qt.WindowMinimizeButtonHint, False)

        self.flags = self.window.windowFlags()

        self.clearStatus()

        self.window.stayOnTop.stateChanged.connect(self.setStayOnTop)

        self.window.pushButton.clicked.connect(self.checkValidAddress)

        self.sensiMax = self.window.Sensitivity.count() - 1
        self.window.Sensitivity.currentIndexChanged.connect(
            self.sButtonControl
            )

        self.sButtonControl()
        self.window.sDown.clicked.connect(self.sensiDown)
        self.window.sUp.clicked.connect(self.sensiUp)
        self.window.sendButton.clicked.connect(self.setSensi)

        self.APHS_Timer = QTimer()
        self.APHS_Timer.setSingleShot(True)
        self.APHS_Timer.timeout.connect(self.APHS_Ready)
        self.window.autoPhase.clicked.connect(self.APHS_Start)

        self.task1 = updateTextTask(self.window)
        self.task2 = updateLightTask(self.window)

        self.window.quit.clicked.connect(self.closeAll)

        self.ui_file.close()

    @Slot()
    def setStayOnTop(self):
        if self.window.stayOnTop.isChecked():
            self.window.setWindowFlags(self.flags | Qt.WindowStaysOnTopHint)
        elif not self.window.stayOnTop.isChecked():
            self.window.setWindowFlags(self.flags)
        self.window.show()

    @Slot()
    def APHS_Ready(self):
        self.window.autoPhase.setEnabled(True)
        self.window.APHS_Label.setText("Status: Ready.")

    @Slot()
    def APHS_Start(self):
        self.window.autoPhase.setEnabled(False)
        self.window.APHS_Label.setText("Status: Waiting...")
        self.device = SR860.SR860Device(self.window.IPaddress.text())
        res = self.device.autoPhase()
        if res != 42:
            self.APHS_Timer.start(1000)
        else:
            self.window.APHS_Label.setText("Status: Failure.")
            self.window.autoPhase.setEnabled(True)

        self.window.statusLight.setVisible(res != 42)

    @Slot()
    def clearStatus(self):

        OLLightMap = {
            "inputRange": self.window.inRanOL,
            "extRefUnlocked": self.window.extRefULOL,
            "CH1Output": self.window.CH1OL,
            "CH2Output": self.window.CH2OL,
            "dataCH1Output": self.window.DCH1OL,
            "dataCH2Output": self.window.DCH2OL,
            "dataCH3Output": self.window.DCH3OL,
            "dataCH4Output": self.window.DCH4OL
        }

        for OLName in OLLightMap.keys():
            OLLightMap[OLName].setVisible(False)

        self.window.statusLight.setVisible(False)
        self.window.autoPhase.setEnabled(False)

    @Slot()
    def checkValidAddress(self):

        self.device = SR860.SR860Device(self.window.IPaddress.text())

        if self.window.pushButton.text() == "Connect":
            if self.device.checkIP():
                self.window.statusLight.setVisible(True)
                self.window.sendButton.setEnabled(True)
                self.window.pushButton.setText("Disconnect")
                self.window.IPaddress.setEnabled(False)
                self.window.autoPhase.setEnabled(True)
                self.window.Sensitivity.setCurrentIndex(
                    self.device.querySensitivity()
                )
                self.task1.start()
                self.task2.start()

            else:
                self.window.statusLight.setVisible(False)
                self.msgBox = QMessageBox()
                self.msgBox.setWindowTitle("Invalid IP")
                self.msgBox.setText("Please check IP address!")
                self.msgBox.setStandardButtons(QMessageBox.Yes)
                self.ret = self.msgBox.exec_()
                self.window.sendButton.setEnabled(False)
                self.task1.stop()
                self.task2.stop()
                self.clearStatus()

        elif self.window.pushButton.text() == "Disconnect":
            self.window.statusLight.setVisible(False)
            self.window.IPaddress.setEnabled(True)
            self.window.pushButton.setText("Connect")
            self.task1.stop()
            self.task2.stop()
            self.clearStatus()

    @Slot()
    def setSensi(self):
        self.device.setSensitivity(
            self.window.Sensitivity.currentIndex()
        )

    @Slot()
    def sensiUp(self):
        self.window.Sensitivity.setCurrentIndex(
            self.window.Sensitivity.currentIndex() - 1
        )

    @Slot()
    def sensiDown(self):
        self.window.Sensitivity.setCurrentIndex(
            self.window.Sensitivity.currentIndex() + 1
        )

    @Slot()
    def sButtonControl(self):
        if self.window.Sensitivity.currentIndex() == 0:
            self.window.sUp.setEnabled(False)
        else:
            self.window.sUp.setEnabled(True)
        if self.window.Sensitivity.currentIndex() == self.sensiMax:
            self.window.sDown.setEnabled(False)
        else:
            self.window.sDown.setEnabled(True)

    @Slot()
    def closeAll(self):

        print("Finishing...")
        self.task1.stop()
        self.task2.stop()
        self.window.close()


if __name__ == "__main__":

    app = QApplication([])
    ui = Window()
    ui.window.show()
    sys.exit(app.exec_())
