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
            "error:0": "OK: Command executed successfully.",
            "error:1": "error:: G-code command unsupported.",
            "error:2": "error:: Bad number format in G-code.",
            "error:3": "error:: Invalid statement in G-code.",
            "error:4": "error:: Negative value not allowed.",
            "error:5": "error:: Homing cycle failure.",
            "error:6": "error:: Minimum step pulse time too short.",
            "error:7": "error:: EEPROM read failure.",
            "error:8": "error:: Invalid or unsupported `$` command.",
            "error:9": "error:: G-code motion command not allowed in current state.",
            "error:10": "error:: Soft limit triggered. Machine stopped.",
            "error:11": "error:: Hard limit triggered. Machine halted.",
            "error:12": "error:: Spindle control command failed.",
            "error:13": "error:: G-code command requires homing but homing is not enabled.",
            "error:14": "error:: Arc radius calculation error.",
            "error:15": "error:: Machine position out of bounds.",
            "error:16": "error:: Tool change command not supported.",
            "error:17": "error:: Safety door open. Machine paused.",
            "error:18": "error:: Invalid feed rate specified.",
            "error:19": "error:: Invalid spindle speed.",
            "error:20": "error:: Unsupported motion mode (e.g., G2/G3 without I/J).",
            "error:21": "error:: Homing cycle required before executing this command.",
            "error:22": "error:: Invalid coolant command.",
            "error:23": "error:: Invalid axis selection in G-code.",
            "error:24": "error:: Machine is in alarm state. Reset required.",
            "error:25": "error:: Feed hold active. Resume required.",
            "error:26": "error:: Unhandled G-code command.",
            "error:27": "error:: Tool offset command unsupported.",
            "error:28": "error:: Machine axis not calibrated.",
            "error:29": "error:: Work coordinate system out of range.",
            "error:30": "error:: Invalid probe command.",
            "error:31": "error:: Invalid jog command.",
            "error:32": "error:: Invalid cutter compensation command.",
            "error:33": "error:: Probe triggered unexpectedly.",
            "error:34": "error:: Probe did not trigger.",
            "error:35": "error:: Laser mode active but incompatible G-code used.",
            "error:36": "error:: Invalid M-code command.",
            "error:37": "error:: G-code line too long.",
            "error:38": "error:: Machine is in motion. Stop required before executing command.",
            "error:39": "error:: Invalid dwell time.",
            "error:40": "error:: Invalid canned cycle command.",
            "error:41": "error:: Machine emergency stop activated.",
            "error:42": "error:: Spindle overload detected.",
            "error:43": "error:: Stepper driver failure detected.",
            "error:44": "error:: Serial communication buffer overflow.",
            "error:45": "error:: G-code comment not properly closed.",
            "error:46": "error:: Axis limit switch triggered.",
            "error:47": "error:: Invalid arc mode command.",
            "error:48": "error:: Machine requires re-homing.",
            "error:49": "error:: G-code motion command blocked by safety settings.",
            "error:50": "error:: CNC machine firmware update required.",
            "error:51": "error:: Tool length offset incorrect.",
            "error:52": "error:: Soft stop triggered.",
            "error:53": "error:: Overheat protection activated.",
            "error:54": "error:: Invalid spindle direction command.",
            "error:55": "error:: Invalid work offset command.",
            "error:56": "error:: Motion planner buffer overflow.",
            "error:57": "error:: Stepper motor stalled.",
            "error:58": "error:: Machine unable to hold position.",
            "error:59": "error:: Invalid rotary axis command.",
            "error:60": "error:: Invalid tool change position.",
            "error:61": "error:: Invalid coolant system command.",
            "error:62": "error:: Invalid backlash compensation command.",
            "error:63": "error:: Machine control lock enabled.",
            "error:64": "error:: Automatic tool changer not available.",
            "error:65": "error:: Spindle not enabled before cutting command.",
            "error:66": "error:: Axis synchronization failure.",
            "error:67": "error:: CNC motion planner buffer full.",
            "error:68": "error:: Invalid dwell command.",
            "error:69": "error:: Machine startup initialization failed.",
            "error:70": "error:: Invalid soft limit settings.",
            "error:71": "error:: Machine requires firmware reset.",
            "error:72": "error:: Machine bed not leveled.",
            "error:73": "error:: End stop trigger detected during motion.",
            "error:74": "error:: Unrecognized or corrupted command received.",
            "error:75": "error:: Machine timeout. Check CNC response time.",
            "error:76": "error:: Buffer overflow detected.",
            "error:77": "error:: Machine in an undefined state.",
            "error:78": "error:: Invalid or missing checksum in G-code.",
            "error:79": "error:: Safety interlock enabled. Operation blocked.",
            "error:80": "error:: Servo motor error detected.",
            "error:81": "error:: Positioning error beyond tolerance.",
            "error:82": "error:: Unrecognized CNC configuration setting.",
            "error:83": "error:: Invalid homing settings.",
            "error:84": "error:: Machine motion exceeded programmed limits.",
            "error:85": "error:: Spindle load exceeded safe threshold.",
            "error:86": "error:: Invalid machine mode transition.",
            "error:87": "error:: Tool table entry not found.",
            "error:88": "error:: Fixture offset invalid.",
            "error:89": "error:: CNC controller restart required.",
            "error:90": "error:: Spindle encoder feedback error.",
            "error:91": "error:: Limit switch debounce time too short.",
            "error:92": "error:: Stepper driver power loss detected.",
            "error:93": "error:: Tool radius compensation conflict.",
            "error:94": "error:: Feed rate override out of range.",
            "error:95": "error:: Axis drive fault detected.",
            "error:96": "error:: MDI (Manual Data Input) command invalid.",
            "error:97": "error:: Machine safety check failed.",
            "error:98": "error:: Invalid cycle start command.",
            "error:99": "error:: CNC watchdog timer triggered.",
            "error:100": "error:: Unhandled CNC internal error.",
        }

        
        return error_messages.get(str(code), "Unknown CNC response code.")

    @action(methods=['POST'], detail=False, name='Send Text Input')
    def send_text(self, request):
        """API to send text input as G-code over serial connection"""
        text_input = request.data.get("text", "").strip()
        port_input = request.data.get("port", "").strip()

        if not text_input:
            return Response({"error:": "No text input provided"}, status=status.HTTP_400_BAD_REQUEST)

        if not port_input:
            return Response({"error:": "No port selected"}, status=status.HTTP_400_BAD_REQUEST)

        if self.port_in_use and self.port_in_use != port_input:
            return Response({"error:": f"Port {self.port_in_use} is already in use. Please wait or cancel."}, status=status.HTTP_409_CONFLICT)

        if not self.connect_serial(port_input):
            return Response({"error:": f"Could not connect to port {port_input}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

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
                return Response({"error:": "Could not establish serial communication"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        except serial.SerialException as e:
            return Response({"error:": f"Serial Exception: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"error:": f"Failed to send GCode: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'], name="Cancel Operation")
    def cancel_operation(self, request):
        """Cancels the ongoing serial operation and releases the port"""
        if self.release_port():
            return Response({"message": "Port released successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error:": "Failed to release port"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def release_port(self):
        """Releases the currently in-use serial port"""
        if self.serial_connection:
            self.stop_reading.set()
            self.serial_connection.close()
            self.serial_connection = None
            self.port_in_use = None
            return True
        return False
