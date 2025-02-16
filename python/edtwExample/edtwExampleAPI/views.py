from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
import serial
import serial.tools.list_ports
import time

# CNC Response Code Mapping
ERROR_MESSAGES = {
    "ok": "Command executed successfully.",
    "error:1": "G-code motion command without active G-code.",
    "error:2": "Invalid G-code command.",
    "error:3": "Attempt to move without homing cycle.",
    "ALARM:1": "Hard limit triggered. Check end stops.",
    "ALARM:2": "Soft limit reached. Adjust work area.",
    "error:5": "Jogging command cannot be executed because the machine is not in a jogging state.",
    "error:9": "G-code command received but ignored due to a modal state conflict.",
    # Add more CNC error mappings if needed...
}

class EdtwViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.serial_connection = None
        self.port_in_use = None  # Track active port

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
        """Connects to a selected serial port, ensuring old connections are closed first"""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                time.sleep(0.5)  # Allow some time before reopening

            self.serial_connection = serial.Serial(port, baudrate=baudrate, timeout=2)
            self.port_in_use = port  # Track port in use
            time.sleep(0.2)
            return True
        except serial.SerialException:
            return False

    def read_serial_response(self):
        """Reads response from CNC and returns the mapped message"""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                responses = []
                start_time = time.time()
                
                while time.time() - start_time < 2:  # Read response for 2 seconds max
                    response = self.serial_connection.readline().decode("utf-8").strip()
                    if response:
                        responses.append({
                            "cnc_response_code": response,
                            "cnc_response_message": ERROR_MESSAGES.get(response, f"Unknown response: {response}")
                        })

                return responses if responses else [{"cnc_response_code": None, "cnc_response_message": "No response from CNC"}]
        except Exception as e:
            return [{"cnc_response_code": "error", "cnc_response_message": f"Failed to read response: {str(e)}"}]

    @action(methods=['POST'], detail=False, name='Send Text Input')
    def send_text(self, request):
        """API to send text input as G-code over serial connection"""
        text_input = request.data.get("text", "").strip()
        port_input = request.data.get("port", "").strip()

        if not text_input:
            return Response({"error": "No text input provided"}, status=status.HTTP_400_BAD_REQUEST)

        if not port_input:
            return Response({"error": "No port selected"}, status=status.HTTP_400_BAD_REQUEST)

        if self.port_in_use:  # If another command is in progress
            return Response({"error": f"Port {self.port_in_use} is already in use. Please wait or cancel."}, status=status.HTTP_409_CONFLICT)

        if not self.connect_serial(port_input):
            return Response({"error": f"Could not connect to port {port_input}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.write((text_input + "\n").encode("utf-8"))
                time.sleep(0.2)

                # Read CNC response and return it
                cnc_responses = self.read_serial_response()

                return Response({
                    "message": "GCode sent successfully",
                    "sent_gcode": text_input,
                    "cnc_responses": cnc_responses
                }, status=status.HTTP_200_OK)

            else:
                return Response({"error": "Could not establish serial communication"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        except serial.SerialException as e:
            return Response({"error": f"Serial Exception: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"error": f"Failed to send GCode: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        finally:
            self.release_port()

    @action(detail=False, methods=['POST'], name="Release Port")
    def release_port(self, request=None):
        """Releases the currently in-use serial port"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            time.sleep(0.2)

        self.serial_connection = None
        self.port_in_use = None
        return Response({"message": "Port released successfully"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'], name="Generate G-Code")
    def generate_gcode(self, request):
        """Generates G-code from user-drawn shapes"""
        shape = request.data.get("shape", "").lower()
        feedrate = request.data.get("feedrate", 1000)
        gcode = ["G21", "G90"]  # Set units to mm, absolute positioning

        if shape == "rectangle":
            start_x = request.data.get("start_x", 0)
            start_y = request.data.get("start_y", 0)
            width = request.data.get("width", 50)
            height = request.data.get("height", 30)

            gcode.append(f"G0 X{start_x} Y{start_y}")  # Move to start
            gcode.append(f"G1 X{start_x + width} Y{start_y} F{feedrate}")  # Top edge
            gcode.append(f"G1 X{start_x + width} Y{start_y + height} F{feedrate}")  # Right edge
            gcode.append(f"G1 X{start_x} Y{start_y + height} F{feedrate}")  # Bottom edge
            gcode.append(f"G1 X{start_x} Y{start_y} F{feedrate}")  # Close rectangle

        elif shape == "circle":
            center_x = request.data.get("center_x", 40)
            center_y = request.data.get("center_y", 40)
            radius = request.data.get("radius", 25)

            gcode.append(f"G0 X{center_x + radius} Y{center_y}")  # Move to start
            gcode.append(f"G2 X{center_x + radius} Y{center_y} I-{radius} J0 F{feedrate}")  # Draw circle

        else:
            return Response(
                {"error": "Invalid shape type"},
                status=status.HTTP_400_BAD_REQUEST
            )

        gcode.append("M30")  # End program
        return Response({"gcode": "\n".join(gcode)}, status=status.HTTP_200_OK)
