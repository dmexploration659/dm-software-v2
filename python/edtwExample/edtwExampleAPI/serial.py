import serial
import serial.tools.list_ports
import threading
import time

class SerialHandler:
    def __init__(self):
        self.serial_connection = None
        self.hardcoded_port = "COM3"
        self.hardcoded_baudrate = 115200
        self.hardcoded_gcode_command = "G01 X10 Y10 F1000"
    
    def get_serial_ports(self):
        """Returns a list of available serial ports"""
        ports = serial.tools.list_ports.comports()
        available_ports = [port.device for port in ports]
        print("Available COM Ports:", available_ports)
        return available_ports
    
    def connect_serial(self):
        """Establishes serial connection"""
        try:
            self.serial_connection = serial.Serial(self.hardcoded_port, baudrate=self.hardcoded_baudrate, timeout=1)
            print(f"Connected to {self.hardcoded_port} at {self.hardcoded_baudrate} baud.")
            self.start_reading_thread()
        except serial.SerialException as e:
            print(f"Error: Failed to connect to {self.hardcoded_port}: {e}")
    
    def start_reading_thread(self):
        """Starts a thread to read responses from the CNC machine"""
        self.read_thread = threading.Thread(target=self.read_serial, daemon=True)
        self.read_thread.start()
    
    def read_serial(self):
        """Reads responses from the CNC machine and prints them"""
        while self.serial_connection and self.serial_connection.is_open:
            try:
                response = self.serial_connection.readline().decode("utf-8").strip()
                if response:
                    print(f"Response: {response}")  # Print machine response
            except Exception as e:
                print(f"Error reading serial data: {e}")
                break
    
    def send_gcode(self):
        """Sends a hardcoded G-code command"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.write((self.hardcoded_gcode_command + "\n").encode("utf-8"))
            print(f"Sent: {self.hardcoded_gcode_command}")  # Print sent command
        else:
            print("Warning: Not connected to a CNC machine.")
    
    def disconnect_serial(self):
        """Closes the serial connection"""
        if self.serial_connection:
            self.serial_connection.close()
            print("Disconnected from CNC machine.")
            self.serial_connection = None

if __name__ == "__main__":
    serial_handler = SerialHandler()
    serial_handler.get_serial_ports()
    serial_handler.connect_serial()
    time.sleep(2)
    serial_handler.send_gcode()
    time.sleep(2)
    serial_handler.disconnect_serial()