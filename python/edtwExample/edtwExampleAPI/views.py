from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
import serial
import serial.tools.list_ports
import threading
import time

class EdtwViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.serial_connection = None
        self.port_in_use = None
        self.read_thread = None
        self.stop_reading = threading.Event()
        self.serial_response = ""

    def get_serial_ports(self):
        """Returns a list of available serial ports"""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    @action(detail=False, methods=['GET'], url_path="get-available-ports")
    def get_available_ports(self, request):
        """API Endpoint to get available serial ports"""
        ports = self.get_serial_ports()
        return Response({"available_ports": ports}, status=status.HTTP_200_OK)

    def connect_serial(self, port, baudrate=115200):
        """Connects to a selected serial port"""
        if self.serial_connection and self.serial_connection.is_open:
            return True

        try:
            self.serial_connection = serial.Serial(port, baudrate=baudrate, timeout=1)
            self.port_in_use = port
            self.start_reading_thread()
            return True
        except serial.SerialException:
            return False

    def start_reading_thread(self):
        """Starts a thread to read responses from the serial port"""
        if not self.read_thread or not self.read_thread.is_alive():
            self.stop_reading.clear()
            self.read_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.read_thread.start()

    def read_serial(self):
        """Reads responses from the serial port and stores the latest response"""
        while not self.stop_reading.is_set():
            try:
                if self.serial_connection and self.serial_connection.is_open:
                    response = self.serial_connection.readline().decode("utf-8").strip()
                    if response:
                        self.serial_response = response
                        print(f"Machine Response: {response}")
            except serial.SerialException:
                break

    def map_error_code(self, code):
        """Maps error codes to messages"""
        error_messages = {
            "0": "OK: Command executed successfully.",
            "1": "Error: G-code command unsupported.",
            "2": "Error: Bad number format in G-code.",
            "3": "Error: Invalid statement in G-code.",
            "4": "Error: Negative value not allowed.",
            "5": "Error: Homing cycle failure.",
            "6": "Error: Minimum step pulse time too short.",
            "7": "Error: EEPROM read failure.",
            "8": "Error: Invalid or unsupported `$` command.",
            "9": "Error: G-code motion command not allowed in current state.",
            "10": "Error: Soft limit triggered. Machine stopped.",
            "11": "Error: Hard limit triggered. Machine halted.",
            "12": "Error: Spindle control command failed.",
            "13": "Error: G-code command requires homing but homing is not enabled.",
            "14": "Error: Arc radius calculation error.",
            "15": "Error: Machine position out of bounds.",
            "16": "Error: Tool change command not supported.",
            "17": "Error: Safety door open. Machine paused.",
            "18": "Error: Invalid feed rate specified.",
            "19": "Error: Invalid spindle speed.",
            "20": "Error: Unsupported motion mode (e.g., G2/G3 without I/J).",
            "21": "Error: Homing cycle required before executing this command.",
            "22": "Error: Invalid coolant command.",
            "23": "Error: Invalid axis selection in G-code.",
            "24": "Error: Machine is in alarm state. Reset required.",
            "25": "Error: Feed hold active. Resume required.",
            "26": "Error: Unhandled G-code command.",
            "27": "Error: Tool offset command unsupported.",
            "28": "Error: Machine axis not calibrated.",
            "29": "Error: Work coordinate system out of range.",
            "30": "Error: Invalid probe command.",
            "31": "Error: Invalid jog command.",
            "32": "Error: Invalid cutter compensation command.",
            "33": "Error: Probe triggered unexpectedly.",
            "34": "Error: Probe did not trigger.",
            "35": "Error: Laser mode active but incompatible G-code used.",
            "36": "Error: Invalid M-code command.",
            "37": "Error: G-code line too long.",
            "38": "Error: Machine is in motion. Stop required before executing command.",
            "39": "Error: Invalid dwell time.",
            "40": "Error: Invalid canned cycle command.",
            "41": "Error: Machine emergency stop activated.",
            "42": "Error: Spindle overload detected.",
            "43": "Error: Stepper driver failure detected.",
            "44": "Error: Serial communication buffer overflow.",
            "45": "Error: G-code comment not properly closed.",
            "46": "Error: Axis limit switch triggered.",
            "47": "Error: Invalid arc mode command.",
            "48": "Error: Machine requires re-homing.",
            "49": "Error: G-code motion command blocked by safety settings.",
            "50": "Error: CNC machine firmware update required.",
            "51": "Error: Tool length offset incorrect.",
            "52": "Error: Soft stop triggered.",
            "53": "Error: Overheat protection activated.",
            "54": "Error: Invalid spindle direction command.",
            "55": "Error: Invalid work offset command.",
            "56": "Error: Motion planner buffer overflow.",
            "57": "Error: Stepper motor stalled.",
            "58": "Error: Machine unable to hold position.",
            "59": "Error: Invalid rotary axis command.",
            "60": "Error: Invalid tool change position.",
            "61": "Error: Invalid coolant system command.",
            "62": "Error: Invalid backlash compensation command.",
            "63": "Error: Machine control lock enabled.",
            "64": "Error: Automatic tool changer not available.",
            "65": "Error: Spindle not enabled before cutting command.",
            "66": "Error: Axis synchronization failure.",
            "67": "Error: CNC motion planner buffer full.",
            "68": "Error: Invalid dwell command.",
            "69": "Error: Machine startup initialization failed.",
            "70": "Error: Invalid soft limit settings.",
            "71": "Error: Machine requires firmware reset.",
            "72": "Error: Machine bed not leveled.",
            "73": "Error: End stop trigger detected during motion.",
            "74": "Error: Unrecognized or corrupted command received.",
            "75": "Error: Machine timeout. Check CNC response time.",
            "76": "Error: Buffer overflow detected.",
            "77": "Error: Machine in an undefined state.",
            "78": "Error: Invalid or missing checksum in G-code.",
            "79": "Error: Safety interlock enabled. Operation blocked.",
            "80": "Error: Servo motor error detected.",
            "81": "Error: Positioning error beyond tolerance.",
            "82": "Error: Unrecognized CNC configuration setting.",
            "83": "Error: Invalid homing settings.",
            "84": "Error: Machine motion exceeded programmed limits.",
            "85": "Error: Spindle load exceeded safe threshold.",
            "86": "Error: Invalid machine mode transition.",
            "87": "Error: Tool table entry not found.",
            "88": "Error: Fixture offset invalid.",
            "89": "Error: CNC controller restart required.",
            "90": "Error: Spindle encoder feedback error.",
            "91": "Error: Limit switch debounce time too short.",
            "92": "Error: Stepper driver power loss detected.",
            "93": "Error: Tool radius compensation conflict.",
            "94": "Error: Feed rate override out of range.",
            "95": "Error: Axis drive fault detected.",
            "96": "Error: MDI (Manual Data Input) command invalid.",
            "97": "Error: Machine safety check failed.",
            "98": "Error: Invalid cycle start command.",
            "99": "Error: CNC watchdog timer triggered.",
            "100": "Error: Unhandled CNC internal error.",
        }

        
        return error_messages.get(str(code), "Unknown CNC response code.")

    @action(methods=['POST'], detail=False, name='Send Text Input')
    def send_text(self, request):
        """API to send text input as G-code over serial connection"""
        text_input = request.data.get("text", "").strip()
        port_input = request.data.get("port", "").strip()

        if not text_input:
            return Response({"error": "No text input provided"}, status=status.HTTP_400_BAD_REQUEST)

        if not port_input:
            return Response({"error": "No port selected"}, status=status.HTTP_400_BAD_REQUEST)

        if self.port_in_use and self.port_in_use != port_input:
            return Response({"error": f"Port {self.port_in_use} is already in use. Please wait or cancel."}, status=status.HTTP_409_CONFLICT)

        if not self.connect_serial(port_input):
            return Response({"error": f"Could not connect to port {port_input}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.write((text_input + "\n").encode("utf-8"))
                time.sleep(0.5)  # Allow response time

                # Parse response
                raw_response = self.serial_response.strip()
                response_message = self.map_error_code(raw_response)

                return Response({
                    "message": "GCode sent successfully",
                    "sent_gcode": text_input,
                    "response_code": raw_response,
                    "response_message": response_message
                }, status=status.HTTP_200_OK)

            else:
                return Response({"error": "Could not establish serial communication"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        except serial.SerialException as e:
            return Response({"error": f"Serial Exception: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"error": f"Failed to send GCode: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'], name="Cancel Operation")
    def cancel_operation(self, request):
        """Cancels the ongoing serial operation and releases the port"""
        if self.release_port():
            return Response({"message": "Port released successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to release port"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def release_port(self):
        """Releases the currently in-use serial port"""
        if self.serial_connection:
            self.stop_reading.set()
            self.serial_connection.close()
            self.serial_connection = None
            self.port_in_use = None
            return True
        return False
