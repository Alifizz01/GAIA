import os
import sys
from PyQt5.QtWidgets import QApplication

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))               
from gui.main_window import AppWindow
from bms_core.battery_model import BatteryModel


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    battery_data = window.get_data()
    battery_chemistry = battery_data.get("Cell Type")
    battery_model = battery_data.get("Model Type")


    window.show()
    sys.exit(app.exec_())