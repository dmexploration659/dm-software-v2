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
        
    def connect_serial(self, port='COM1', baudrate=115200):
        try:
            self.serial_connection = serial.Serial(port, baudrate=baudrate, timeout=1)
            return True
        except serial.SerialException as e:
            return False

    @action(methods=['GET'], detail=False, name='Get Value from input')
    def get_val_from(self, request):
        input_str = request.GET.get('input', '')

        # Validate the length of input
        if not (10 <= len(input_str) <= 20):
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"error": "Input must be between 10 and 20 characters long."}
            )

        # Try to send the input as GCode if not connected
        if not self.serial_connection or not self.serial_connection.is_open:
            self.connect_serial()

        try:
            return Response(
                status=status.HTTP_200_OK,
                data={"error": "Input must be between 10 and 20 characters long."}
            )
            # if self.serial_connection and self.serial_connection.is_open:
            #     # Send the GCode command
            #     self.serial_connection.write((input_str + "\n").encode("utf-8"))
            #     # Read the response (optional)
            #     response = self.serial_connection.readline().decode("utf-8").strip()
                
            #     return Response(
            #         status=status.HTTP_200_OK,
            #         data={
            #             "input": input_str,
            #             "length": len(input_str),
            #             "message": "GCode sent successfully",
            #             "machine_response": response
            #         }
            #     )
            # else:
            #     return Response(
            #         status=status.HTTP_503_SERVICE_UNAVAILABLE,
            #         data={"error": "Could not connect to CNC machine"}
            #     )
                
        except Exception as e:
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data={"error": f"Failed to send GCode: {str(e)}"}
            ) 