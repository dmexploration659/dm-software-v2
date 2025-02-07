from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
import serial
import serial.tools.list_ports
import time

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
                time.sleep(0.5)

            self.serial_connection = serial.Serial(port, baudrate=baudrate, timeout=1)
            self.port_in_use = port  # Track port in use
            time.sleep(0.2)
            return True
        except serial.SerialException:
            return False

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
                response = self.serial_connection.readline().decode("utf-8").strip()

                return Response({
                    "message": "GCode sent successfully",
                    "sent_gcode": text_input,
                    "machine_response": response
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
