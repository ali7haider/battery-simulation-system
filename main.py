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
            # Get UI elements
            self.powerSlider = self.findChild(QtWidgets.QSlider, "powerSlider")  
            self.sliderValueLabel = self.findChild(QtWidgets.QLabel, "sliderValueLabel")  
            self.voltageLabel = self.findChild(QtWidgets.QLabel, "voltageLabel")  
            self.currentLabel = self.findChild(QtWidgets.QLabel, "currentLabel")  
            self.minVoltageLabel = self.findChild(QtWidgets.QLabel, "minVoltageLabel")  
            self.maxVoltageLabel = self.findChild(QtWidgets.QLabel, "maxVoltageLabel")  
            self.powerLabel = self.findChild(QtWidgets.QLabel, "powerLabel")  
            self.timeLabel = self.findChild(QtWidgets.QLabel, "timeLabel")  
            self.btnRun = self.findChild(QtWidgets.QPushButton, "btnRun")  
            self.btnStop = self.findChild(QtWidgets.QPushButton, "btnStop")  
            self.btnUploadCSV = self.findChild(QtWidgets.QPushButton, "btnUploadCSV")
            self.txtCSVPath = self.findChild(QtWidgets.QLineEdit, "txtCSVPath")

            # Connect buttons
            self.btnRun.clicked.connect(self.run_simulation)
            self.btnStop.clicked.connect(self.stop_simulation)
            self.btnUploadCSV.clicked.connect(self.upload_csv)

            # Timers
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_time)
            self.csv_timer = QTimer(self)
            self.csv_timer.timeout.connect(self.update_power_from_csv)

            # Variables
            self.start_time = QTime(0, 0, 0)
            self.csv_power_values = []
            self.csv_index = 0
            self.csv_loaded = False

            # Other initializations...
            self.elapsed_time = 0  # Store the time when simulation is paused
            self.is_paused = False  # Track if the simulation is paused
            self.elapsed_seconds = 0  # Track elapsed time in seconds

                        
            self.powerSlider.setMinimum(-5000)  # Example: -5000W (charging)
            self.powerSlider.setMaximum(5000)   # 5000W (discharging)
            self.powerSlider.sliderReleased.connect(self.on_slider_released)

        except Exception as e:
            self.handle_error("Initialization Error", e)

    def upload_csv(self):
        """Load power values from a CSV file."""
        try:
            options = QtWidgets.QFileDialog.Options()
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Select CSV File", "", "CSV Files (*.csv);;Excel Files (*.xlsx;*.xls)", options=options
            )

            if file_path:
                file_name = os.path.basename(file_path)
                self.txtCSVPath.setText(f"{file_name} Datei Upload")

            
                # Try loading CSV or Excel file
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)

                if "Power" in df.columns:
                    self.csv_power_values = df["Power"].tolist()
                elif "Current" in df.columns:
                    self.csv_power_values = (df["Current"] * 400).tolist()
                else:
                    self.show_message_box("Error", "CSV must have a 'Power' or 'Current' column.")
                    return
                
                self.csv_index = 0
                self.csv_loaded = True

        except Exception as e:
            self.show_message_box("CSV Upload Error", f"An error occurred: {e}")


    def update_power_from_csv(self):
        """Update power from CSV file every second."""
        if self.csv_index < len(self.csv_power_values):
            # Get the power value from CSV
            power_value = self.csv_power_values[self.csv_index]  # Leave this as is (float or int)

            # Determine if the power is charging or discharging
            if power_value < 0:
                status = "Charging"
            else:
                status = "Discharging"
            
            # Update the power label with power and status (abs() for display purposes)
            self.powerLabel.setText(f"Batterieleistung: {power_value} W ({status})")

            # Calculate battery values based on the current power value
            batterie_spannung_in_V, zellspannung_min_in_V, zellspannung_max_in_V, batterie_strom_in_A = self.get_battery_values_and_status(power_value)

            # Update battery info in the GUI
            self.set_battery_power(batterie_spannung_in_V, batterie_strom_in_A, zellspannung_min_in_V, zellspannung_max_in_V)

            # Move to the next value in the CSV
            self.csv_index += 1
        else:
            # Stop the CSV timer when all values have been processed
            self.csv_timer.stop()
            self.powerSlider.setEnabled(True)



    def on_slider_released(self):
        """Handle the slider release event and update values accordingly."""
        try:
            # Get the current value of the slider (power)
            power_value = self.powerSlider.value()

            # Determine if the power is charging or discharging
            status = "Charging" if power_value < 0 else "Discharging"

            # Update the UI with the new values
            self.sliderValueLabel.setText(f"{power_value} W")
            self.powerLabel.setText(f"Batterieleistung: {power_value} W ({status})")

            # Calculate and update battery values
            batterie_spannung_in_V, zellspannung_min_in_V, zellspannung_max_in_V, batterie_strom_in_A = self.get_battery_values_and_status(power_value)
            self.set_battery_power(batterie_spannung_in_V, batterie_strom_in_A, zellspannung_min_in_V, zellspannung_max_in_V)

        except Exception as e:
            self.handle_error("Slider Release Error", e)

    def resume_simulation(self):
        """Resume the simulation after 5 seconds."""
        try:
            if not hasattr(self, "csv_power_values") or not self.csv_power_values:
                print("No CSV file loaded. Simulation cannot resume.")
                return
            # Resume from where it was paused
            self.sliderValueLabel.setText("0 W")  # Reset slider label
            self.powerSlider.setValue(0)  # Reset slider to 0
            self.timer.start(1000)  # Restart the timer
            self.csv_timer.start(1000)  # Resume CSV simulation
            self.is_paused = False
            print("Simulation resumed after 5 seconds.")
        except Exception as e:
            self.handle_error("Simulation Resume Error", e)

    def update_time(self):
        """Update the elapsed time."""
        try:
            if not self.is_paused:
                self.elapsed_seconds += 1  # Track elapsed simulation time manually
                elapsed_time = QTime(0, 0, 0).addSecs(self.elapsed_seconds)  # Simulated time
                self.timeLabel.setText(f"Zeit seit Start: {elapsed_time.toString('hh:mm:ss')}")
        except Exception as e:
            self.handle_error("Time Update Error", e)

    def run_simulation(self):
        """Runs the simulation when btnRun is pressed."""
        try:
            if not self.csv_loaded:
                self.show_message_box("Error", "Please upload a CSV file first.")
                return

            self.sliderValueLabel.setText("0 W")  # Reset slider label
            self.powerSlider.setValue(0)  # Reset slider to 0
            self.elapsed_seconds = 0  # Reset elapsed time tracking
            self.powerSlider.setDisabled(True)
            self.timer.start(1000)  # Update every second
            self.csv_timer.start(1000)  # Update power from CSV every second
            self.is_paused = False  # Ensure it's not paused when starting
            print("Simulation started.")
        except Exception as e:
            self.handle_error("Simulation Error", e)

    def stop_simulation(self):
        """Stops the simulation."""
        try:
            self.timer.stop()
            self.csv_timer.stop()
            print("Simulation stopped.")
            self.powerSlider.setEnabled(True)
            self.elapsed_seconds = 0  # Reset elapsed time
            self.timeLabel.setText(f"Zeit seit Start: 00:00:00")
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
            # self.powerLabel.setText(f"Batterieleistung: {round(power, 2)} W")  
        except Exception as e:
            self.handle_error("Battery Value Update Error", e)

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
