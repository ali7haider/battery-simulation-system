import os
import sys
import traceback
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer, QTime
import pandas as pd  # Install with: pip install pandas

class MasterScreen(QtWidgets.QMainWindow):
    def __init__(self, user_data=None):
        super().__init__()
        try:
            ui_file = os.path.join(os.path.dirname(__file__), "main.ui")
            uic.loadUi(ui_file, self)

            # Get slider and label from the UI
            self.powerSlider = self.findChild(QtWidgets.QSlider, "powerSlider")  
            self.sliderValueLabel = self.findChild(QtWidgets.QLabel, "sliderValueLabel")  
            
            # Get battery value labels
            self.voltageLabel = self.findChild(QtWidgets.QLabel, "voltageLabel")  
            self.currentLabel = self.findChild(QtWidgets.QLabel, "currentLabel")  
            self.minVoltageLabel = self.findChild(QtWidgets.QLabel, "minVoltageLabel")  
            self.maxVoltageLabel = self.findChild(QtWidgets.QLabel, "maxVoltageLabel")  
            self.powerLabel = self.findChild(QtWidgets.QLabel, "powerLabel")  
            self.timeLabel = self.findChild(QtWidgets.QLabel, "timeLabel")  

            # Get buttons and connect functions
            self.btnRun = self.findChild(QtWidgets.QPushButton, "btnRun")  
            self.btnStop = self.findChild(QtWidgets.QPushButton, "btnStop")  # Stop button
            if self.btnRun:
                self.btnRun.clicked.connect(self.run_simulation)
            if self.btnStop:
                self.btnStop.clicked.connect(self.stop_simulation)  # Connect stop button

            # Connect slider change signal
            if self.powerSlider and self.sliderValueLabel:
                self.powerSlider.valueChanged.connect(self.update_slider_value)
            self.btnUploadCSV.clicked.connect(self.upload_csv)
            # Timer for tracking elapsed time
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_time)
            self.start_time = QTime(0, 0, 0)  

        except Exception as e:
            self.handle_error("Initialization Error", e)

    def upload_csv(self):
        """Open file dialog, display file name, and print data."""
        options = QtWidgets.QFileDialog.Options()
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select CSV or Excel File", "", 
            "CSV Files (*.csv);;Excel Files (*.xlsx;*.xls)", options=options
        )

        if file_path:
            file_name = os.path.basename(file_path)
            self.txtCSVPath.setText(f"{file_name} Datei Upload")  # Show file name

            # Load and print data
            try:
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path, sep=None, engine='python')  # Auto-detect delimiter
                else:
                    df = pd.read_excel(file_path)  # Read Excel

                print("\nData from file (showing all columns):")
                print(df.to_string(index=False))  # Print full data

            except Exception as e:
                print("Error loading file:", e)
    def update_slider_value(self):
        """Update the label when the slider value changes."""
        try:
            value = self.powerSlider.value()
            self.sliderValueLabel.setText(f"{value} W")  
        except Exception as e:
            self.handle_error("Slider Update Error", e)

    def get_battery_values_and_status(self, batterie_leistung_in_W):
        """Calculates battery parameters based on power input."""
        try:
            batterie_spannung_in_V = 400  # Fixed battery voltage
            zellspannung_min_in_V = 3.1
            zellspannung_max_in_V = 3.4
            batterie_strom_in_A = batterie_leistung_in_W / batterie_spannung_in_V  # Current = Power / Voltage
            return [batterie_spannung_in_V, zellspannung_min_in_V, zellspannung_max_in_V, batterie_strom_in_A]
        except Exception as e:
            print(f"Error in battery_data: {e}")
            return [0, 0, 0, 0]  # Return default values in case of error

    def run_simulation(self):
        """Runs the simulation when btnRun is pressed."""
        try:
            power_value = self.powerSlider.value()  # Get slider value
            print(f"Running simulation with Power: {power_value} W")  

            # Reset and start the timer
            self.start_time = QTime(0, 0, 0)  # Reset to 00:00:00
            self.timer.start(1000)  # Update every second

            # Call the battery data function to get updated values
            batterie_spannung_in_V, zellspannung_min_in_V, zellspannung_max_in_V, batterie_strom_in_A = self.get_battery_values_and_status(power_value)

            # Update the GUI labels
            self.set_battery_power(batterie_spannung_in_V, batterie_strom_in_A, zellspannung_min_in_V, zellspannung_max_in_V)
        except Exception as e:
            self.handle_error("Simulation Error", e)

    def stop_simulation(self):
        """Stops the timer when btnStop is pressed."""
        try:
            self.timer.stop()  # Stop the timer
            print("Simulation stopped.")

            # Optionally reset the time display
            self.start_time = QTime(0, 0, 0)
            self.timeLabel.setText(f"Zeit seit Start: {self.start_time.toString('hh:mm:ss')}")

        except Exception as e:
            self.handle_error("Stop Simulation Error", e)

    def set_battery_power(self, voltage, current, min_voltage, max_voltage):
        """Update the battery values in the GUI and calculate power."""
        try:
            power = voltage * current  # Power (W) = Voltage (V) * Current (A)

            self.voltageLabel.setText(f"Batteriespannung: {voltage} V")
            self.currentLabel.setText(f"Batteriestrom: {round(current, 2)} A")
            self.minVoltageLabel.setText(f"Kleinste Zellspannung: {min_voltage} V")
            self.maxVoltageLabel.setText(f"Höchste Zellspannung: {max_voltage} V")
            self.powerLabel.setText(f"Batterieleistung: {round(power, 2)} W")  
        except Exception as e:
            self.handle_error("Battery Value Update Error", e)

    def update_time(self):
        """Update the elapsed time label."""
        try:
            self.start_time = self.start_time.addSecs(1)  # Increase time by 1 second
            self.timeLabel.setText(f"Zeit seit Start: {self.start_time.toString('hh:mm:ss')}")
        except Exception as e:
            self.handle_error("Time Update Error", e)

    def handle_error(self, error_title, exception):
        """Displays an error message box and logs the error."""
        error_message = f"{error_title}: {str(exception)}\n\nTraceback:\n{traceback.format_exc()}"
        print(error_message)  # Print to console
        self.show_message_box("Error", error_message)

    def show_message_box(self, title, message):
        """Displays a QMessageBox for general errors."""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()

if __name__ == '__main__':
    try:
        app = QtWidgets.QApplication(sys.argv)
        main_window = MasterScreen()
        main_window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Critical Error: {e}")
        sys.exit(1)
