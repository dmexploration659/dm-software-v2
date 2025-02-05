# from datetime import datetime
# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# import serial
# import serial.tools.list_ports

# class EdtwViewSet(viewsets.ViewSet):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.serial_connection = None

#     def get_serial_ports(self):
#         """Returns a list of available serial ports"""
#         ports = serial.tools.list_ports.comports()
#         return [port.device for port in ports]

#     @action(detail=False, methods=['GET'], url_path="get-available-ports")
#     def get_available_ports(self, request):
#         """API Endpoint to get available serial ports"""
#         ports = self.get_serial_ports()
#         return Response({"available_ports": ports}, status=status.HTTP_200_OK)


#     @action(methods=['GET'], detail=False, name='Get Available Ports')
#     def get_available_ports(self, request):
#         """API Endpoint to get available serial ports"""
#         ports = self.get_serial_ports()
#         return Response({"available_ports": ports}, status=status.HTTP_200_OK)

#     def connect_serial(self, port='COM1', baudrate=115200):
#         """Connects to a selected serial port"""
#         try:
#             self.serial_connection = serial.Serial(port, baudrate=baudrate, timeout=1)
#             return True
#         except serial.SerialException as e:
#             return False

#     @action(methods=['GET'], detail=False, name='Get Value from input')
#     def get_val_from(self, request):
#         input_str = request.GET.get('input', '')

#         # Validate the length of input
#         if not (10 <= len(input_str) <= 20):
#             return Response(
#                 status=status.HTTP_200_OK,
#                 data={"message": "Input must be between 10 and 20 characters long.", "ports": self.get_serial_ports()}
#             )

#         # Try to send the input as GCode if not connected
#         if not self.serial_connection or not self.serial_connection.is_open:
#             self.connect_serial()

#         try:
#             if self.serial_connection and self.serial_connection.is_open:
#                 # Send the GCode command
#                 self.serial_connection.write((input_str + "\n").encode("utf-8"))
#                 # Read the response (optional)
#                 response = self.serial_connection.readline().decode("utf-8").strip()

#                 return Response(
#                     status=status.HTTP_200_OK,
#                     data={
#                         "input": input_str,
#                         "length": len(input_str),
#                         "message": "GCode sent successfully",
#                         "machine_response": response
#                     }
#                 )
#             else:
#                 return Response(
#                     status=status.HTTP_503_SERVICE_UNAVAILABLE,
#                     data={"error": "Could not connect to CNC machine"}
#                 )

#         except Exception as e:
#             return Response(
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 data={"error": f"Failed to send GCode: {str(e)}"}
#             )

from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
import serial
import serial.tools.list_ports

class EdtwViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.serial_connection = None

    def get_serial_ports(self):
        """Returns a list of available serial ports"""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    @action(detail=False, methods=['GET'], url_path="get-available-ports")
    def get_available_ports(self, request):
        """API Endpoint to get available serial ports"""
        ports = self.get_serial_ports()
        return Response({"available_ports": ports}, status=status.HTTP_200_OK)

    def connect_serial(self, port='COM1', baudrate=115200):
        """Connects to a selected serial port"""
        try:
            self.serial_connection = serial.Serial(port, baudrate=baudrate, timeout=1)
            return True
        except serial.SerialException:
            return False

    @action(methods=['GET'], detail=False, name='Get Value from input')
    def get_val_from(self, request):
        """API Endpoint to send input text as GCode"""
        input_str = request.GET.get('input', '')

        if not (10 <= len(input_str) <= 20):
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "Input must be between 10 and 20 characters long.", "ports": self.get_serial_ports()}
            )

        if not self.serial_connection or not self.serial_connection.is_open:
            self.connect_serial()

        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.write((input_str + "\n").encode("utf-8"))
                response = self.serial_connection.readline().decode("utf-8").strip()

                return Response(
                    status=status.HTTP_200_OK,
                    data={"input": input_str, "length": len(input_str), "message": "GCode sent successfully", "machine_response": response}
                )
            else:
                return Response(
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                    data={"error": "Could not connect to CNC machine"}
                )

        except Exception as e:
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data={"error": f"Failed to send GCode: {str(e)}"}
            )

    @action(methods=['POST'], detail=False, name='Send Text Input')
    def send_text(self, request):
        """API to send text input as G-code over serial connection"""
        text_input = request.data.get("text", "").strip()
        port_input = request.data.get("port", "").strip()

        if not text_input:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"error": "No text input provided"}
            )

        if not port_input:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"error": "No port selected"}
            )

        # Connect to the specified port
        if not self.connect_serial(port_input):
            return Response(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                data={"error": f"Could not connect to port {port_input}"}
            )

        try:
            if self.serial_connection and self.serial_connection.is_open:
                # ✅ Send the input as G-code command
                self.serial_connection.write((text_input + "\n").encode("utf-8"))

                # ✅ Read the machine response
                response = self.serial_connection.readline().decode("utf-8").strip()

                return Response(
                    status=status.HTTP_200_OK,
                    data={
                        "message": "GCode sent successfully",
                        "sent_gcode": text_input,
                        "machine_response": response
                    }
                )
            else:
                return Response(
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                    data={"error": "Could not establish serial communication"}
                )

        except Exception as e:
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data={"error": f"Failed to send GCode: {str(e)}"}
            )
            
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
