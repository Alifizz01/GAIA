from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QSlider, QLabel, 
    QDesktopWidget, QPushButton
)
from PyQt5.QtCore import Qt
import sys

class AppWindow(QMainWindow):
    def __init__(self):   
        super().__init__()
        self.initUI()
    
    def initUI(self):
        """Initialize the main window."""
        self.setWindowTitle("GAIA Simulator")
        self.setGeometryToFullScreen()
        self.setupControlPanel()
    
    def setGeometryToFullScreen(self):
        """Set the window to full screen size."""
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(0, 0, screen.width(), int(screen.height() * 0.90))
    
    def setupControlPanel(self):
        """Create and set up the control panel."""
        controlPanel = QWidget()
        controlPanel.setFixedHeight(300)
        controlPanel.setFixedWidth(300)
        controlPanelLabel = QLabel("CONTROL PANEL")
        self.setCentralWidget(controlPanel)

        mainLayout = QVBoxLayout(controlPanel)
        mainLayout.addSpacing(10)
        
        # Slider SOC layout
        sliderLayout = QVBoxLayout()
        slider = QSlider(Qt.Horizontal)
        slider.setTickInterval(10)
        slider.setRange(0, 100)
        slider.setValue(50)  # Default value

        # Slider Voltage layout
        sliderVoltageLayout = QVBoxLayout()
        sliderVoltage = QSlider(Qt.Horizontal)
        sliderVoltage.setRange(20, 40)
        sliderVoltage.setValue(30)
        sliderVoltage.setTickInterval(5)
        sliderVoltageLabel = QLabel("Voltage (V): 2.5")
        sliderVoltage.valueChanged.connect(
            lambda x: sliderVoltageLabel.setText(f"Voltage (V) : {float(x/10)}"))


        # Label to display slider value
        sliderLabel = QLabel("SOC (%): 50")
        slider.valueChanged.connect(
            lambda x: sliderLabel.setText(f"SOC (%): {x}"))

        # Save Button
        ButtonLayout = QVBoxLayout()
        SaveButton = QPushButton("SAVE", self)
        SaveButton.setGeometry(200, 0, 150, 40)
        SaveButton.setStyleSheet("font-family: calibri;")
        ButtonLayout.addWidget(SaveButton)
        
        
        sliderLayout.addWidget(sliderLabel)
        sliderLayout.addWidget(slider)
        sliderVoltageLayout.addWidget(sliderVoltageLabel)
        sliderVoltageLayout.addWidget(sliderVoltage)
        mainLayout.addWidget(controlPanelLabel)
        mainLayout.addLayout(sliderLayout)
        mainLayout.addLayout(sliderVoltageLayout)
        mainLayout.addLayout(ButtonLayout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec_())