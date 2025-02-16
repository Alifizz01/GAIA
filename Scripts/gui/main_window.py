from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QSlider, QLabel, 
    QDesktopWidget, QPushButton, QHBoxLayout, QLineEdit, QComboBox, QCheckBox
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
        self.setupUI()

    def setGeometryToFullScreen(self):
        """Set the window to full screen size."""
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(0, 0, screen.width(), int(screen.height() * 0.90))
    
    def setupUI(self):
        mainWidget = QWidget()
        self.setCentralWidget(mainWidget)
        mainLayout = QHBoxLayout()
        layout1 = QVBoxLayout()
        layout2 = QVBoxLayout()

        controlLabel = QLabel("Control")
        controlLabel.setFixedHeight(50)
        controlPanelLayout = QVBoxLayout()
        controlPanelLayout.addWidget(controlLabel)

        cellLayout = QHBoxLayout()
        cellTypeComboBox = QComboBox()
        cellTypeComboBox.setFixedWidth(100)
        cellTypeComboBox.addItem("NMC")
        cellTypeComboBox.addItem("LTO")
        cellTypeComboBox.addItem("LFP")
        cellTypeComboBox.addItem("LMO")
        cellTypeComboBox.addItem("NCA")
        chooseButton = QPushButton("Choose", self)
        cellLayout.addWidget(cellTypeComboBox)
        cellLayout.addWidget(chooseButton)

        # Cell Configurations
        cellConfigutaionLayout = QHBoxLayout()
        cellConfiguration = QComboBox()
        cellConfiguration.setFixedWidth(100)
        cellConfiguration.addItem("6s74p")
        cellConfiguration.addItem("8s24p")
        cellConfiguration.addItem("12s48p")
        cellConfiguration.addItem("14s96p")
        cellConfiguration.addItem("16s1p")
        cellConfiguration.addItem("24s1p")
        cellConfiguration.addItem("48s1p")
        cellConfiguration.addItem("96s74p")
        cellConfiguration.addItem("112s96p")
        cellConfigurationChoose = QPushButton("Choose", self)
        cellConfigutaionLayout.addWidget(cellConfiguration)
        cellConfigutaionLayout.addWidget(cellConfigurationChoose)

        # C-rate
        CRateLayout = QVBoxLayout()
        CRateSliderLabel = QLabel("C-Rate: ")
        CRateSliderLabel.setFixedHeight(50)
        CRateSlider = QSlider(Qt.Horizontal)
        CRateSlider.setRange(1, 50)
        CRateSlider.setTickInterval(10)
        CRateSlider.valueChanged.connect(lambda x: CRateSliderLabel.setText(f"C-Rate: {x/10}"))
        CRateLayout.addWidget(CRateSliderLabel)
        CRateLayout.addWidget(CRateSlider)


        # Slider SOC layout
        sliderLayout = QVBoxLayout()
        slider = QSlider(Qt.Horizontal)
        slider.setTickInterval(10)
        slider.setRange(0, 100)
        slider.setValue(50)  # Default value
        sliderLabel = QLabel("SOC (%): 50")
        sliderLabel.setFixedHeight(50)
        slider.valueChanged.connect(
            lambda x: sliderLabel.setText(f"SOC (%): {x}"))
        # Add slider and label to the layout
        sliderLayout.addWidget(sliderLabel)
        sliderLayout.addWidget(slider)

        # Slider Voltage layout
        sliderVoltageLayout = QVBoxLayout()
        sliderVoltage = QSlider(Qt.Horizontal)
        sliderVoltage.setRange(20, 40)
        sliderVoltage.setValue(30)
        sliderVoltage.setTickInterval(5)
        sliderVoltageLabel = QLabel("Voltage (V): 3.0")  # Corrected initial value
        sliderVoltageLabel.setFixedHeight(50)
        sliderVoltage.valueChanged.connect(
            lambda x: sliderVoltageLabel.setText(f"Voltage (V): {x/10:.1f}"))
        # Add voltage slider and label to the layout
        sliderVoltageLayout.addWidget(sliderVoltageLabel)
        sliderVoltageLayout.addWidget(sliderVoltage)


        # Buttons
        threeButtonLayout = QHBoxLayout()
        startButton = QPushButton("start", self)
        stopButton = QPushButton("stop", self)
        resetButton = QPushButton("reset", self)
        threeButtonLayout.addWidget(startButton)
        threeButtonLayout.addWidget(stopButton)
        threeButtonLayout.addWidget(resetButton)

        # Save Button
        ButtonLayout = QHBoxLayout()
        SaveButton = QPushButton("SAVE", self)
        SaveButton.setGeometry(200, 0, 150, 40)
        SaveButton.setStyleSheet("font-family: calibri;")
        ButtonLayout.addWidget(SaveButton)

        # Ambient temperature setup
        temperatureLayout = QHBoxLayout()
        ambientTemperature = QLineEdit()
        ambientTemperature.setPlaceholderText("Input your Ambient temperature")
        applyButton = QPushButton("Apply", self)
        temperatureLayout.addWidget(ambientTemperature)
        temperatureLayout.addWidget(applyButton)

        # Fault Injection
        faultInjectionLayout = QVBoxLayout()

        # Checkboxes for faults
        self.overvoltageCheckBox = QCheckBox("Overvoltage")
        self.overtemperatureCheckBox = QCheckBox("Overtemperature")
        self.cellImbalanceCheckBox = QCheckBox("Cell Imbalance")

        # Add checkboxes to faultInjectionLayout
        faultInjectionLayout.addWidget(self.overvoltageCheckBox)
        faultInjectionLayout.addWidget(self.overtemperatureCheckBox)
        faultInjectionLayout.addWidget(self.cellImbalanceCheckBox)

        # Load Button
        loadButton = QPushButton("LOAD", self)
        loadButton.setGeometry(0, 0, 150, 40)
        loadButton.setStyleSheet("font-family: calibri;")  # Corrected from SaveButton to loadButton
        ButtonLayout.addWidget(loadButton)

        # Add all layouts to the control panel
        controlPanelLayout.addLayout(cellLayout)        
        controlPanelLayout.addLayout(cellConfigutaionLayout)

        controlPanelLayout.addLayout(sliderLayout)
        controlPanelLayout.addLayout(sliderVoltageLayout)
        controlPanelLayout.addLayout(CRateLayout)
        controlPanelLayout.addLayout(faultInjectionLayout)
        controlPanelLayout.addLayout(temperatureLayout)
        controlPanelLayout.addStretch()
        controlPanelLayout.addLayout(threeButtonLayout)
        controlPanelLayout.addLayout(ButtonLayout)

        # Analysis and message sections
        analysisLabel = QLabel("Analysis")
        analysisLabel.setFixedHeight(50)
        analysisLayout = QVBoxLayout()
        analysisLayout.addWidget(analysisLabel)
        
        messageLabel = QLabel("Message")
        messageLabel.setFixedHeight(50)
        messageLayout = QVBoxLayout()
        messageLayout.addWidget(messageLabel)
        
        analysisFirstRowLayout = QHBoxLayout()
        analysisSecondRowLayout = QHBoxLayout()

        label1 = QLabel("#1")
        label1.setFixedHeight(50)
        label2 = QLabel("#2")
        label2.setFixedHeight(50)
        label3 = QLabel("#3")
        label3.setFixedHeight(50)
        label4 = QLabel("#4")
        label4.setFixedHeight(50)
        label5 = QLabel("#5")
        label5.setFixedHeight(50)
        label6 = QLabel("#6")
        label6.setFixedHeight(50)

        analysisFirstRowLayout.addWidget(label1)
        analysisFirstRowLayout.addWidget(label2)
        analysisFirstRowLayout.addWidget(label3)
        analysisSecondRowLayout.addWidget(label4)
        analysisSecondRowLayout.addWidget(label5)
        analysisSecondRowLayout.addWidget(label6)

        analysisLayout.addLayout(analysisFirstRowLayout)
        analysisLayout.addLayout(analysisSecondRowLayout)


        # Combine layouts
        layout1.addLayout(controlPanelLayout)
        layout2.addLayout(analysisLayout)
        layout2.addStretch()
        layout2.addLayout(messageLayout)

        # Set stretch factors
        layout2.setStretchFactor(messageLayout, 3)
        layout2.setStretchFactor(analysisLayout, 5)

        mainLayout.addLayout(layout1)
        mainLayout.addLayout(layout2)
        mainLayout.setStretchFactor(layout1, 1)
        mainLayout.setStretchFactor(layout2, 4)

        mainWidget.setLayout(mainLayout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec_())