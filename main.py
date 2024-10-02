# vestapy - a cli tool to interact with the local Vestaboard API
# October 1, 2024 - Virgil Vaduva
# Beta version 0.1
# To obstain a local API key, you will need to reach out to Vestaboard support so they can
# enable the feature on your device.  They will provide you with an enamblement key you 
# can then use to turn on the feature.

import os
from dotenv import load_dotenv, find_dotenv
import requests
import json
import argparse
from datetime import datetime

# Load environment variables
load_dotenv(find_dotenv())

# Constants
API_KEY = os.getenv("VBOARD")
IP_ADDRESS = "192.168.86.22" # This will obivously be the internal IP address of your board
BASE_URL = f"http://{IP_ADDRESS}:7000/local-api/message"

# Load character codes from character_codes.json
with open("character_codes.json", "r") as file:
    CHARACTER_CODES = json.load(file)

# Define color codes
COLOR_CODES = {
    "red": 63,
    "orange": 64,
    "yellow": 65,
    "green": 66,
    "blue": 67,
    "violet": 68,
    "white": 69,
    "black": 70,
}

class Vestaboard:
    def __init__(self, api_key, base_url, debug=False):
        """
        Initialize the Vestaboard instance with the API key and the base URL of the device.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.debug = debug

    def send_message(self, message_matrix):
        """
        Sends a message matrix to the Vestaboard.
        """
        headers = {
            "X-Vestaboard-Local-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }

        if self.debug:
            print(f"[DEBUG] Sending message to Vestaboard with the following matrix:\n{json.dumps(message_matrix, indent=4)}")
            print(f"[DEBUG] Headers: {headers}")
            print(f"[DEBUG] URL: {self.base_url}")

        response = requests.post(self.base_url, headers=headers, data=json.dumps(message_matrix))

        if response.status_code in [200, 201]:
            print("Message sent successfully!")
            if self.debug:
                print(f"[DEBUG] Response Status Code: {response.status_code}")
                print(f"[DEBUG] Response Text: {response.text}")
        else:
            print(f"Failed to send message. Status code: {response.status_code}")
            print(f"Response: {response.text}")

        return response

    def convert_text_to_codes(self, text):
        """
        Converts a text message to the corresponding character codes.
        Spaces are represented as 0 to preserve background.
        """
        return [CHARACTER_CODES.get(char.upper(), 0) if char != " " else 0 for char in text]

    def create_gradient_background(self, start_color, end_color):
        """
        Creates a gradient background from the start color to the end color.
        """
        start_code = COLOR_CODES.get(start_color.lower(), 70)  # Default to black
        end_code = COLOR_CODES.get(end_color.lower(), 70)  # Default to black

        gradient_matrix = []
        for row in range(6):
            row_gradient = []
            for col in range(22):
                # Calculate gradient position (linear interpolation)
                ratio = (row * 22 + col) / (6 * 22 - 1)
                code = int(start_code + ratio * (end_code - start_code))
                row_gradient.append(code)
            gradient_matrix.append(row_gradient)

        return gradient_matrix

    def create_message_matrix(self, message, color=None, justify="left", gradient=None):
        """
        Creates a 6x22 message matrix from the given text message.
        """
        # Create the background matrix (either solid color or gradient)
        if gradient:
            background_matrix = self.create_gradient_background(*gradient)
        else:
            default_fill_code = COLOR_CODES.get(color.lower(), 0) if color else 0
            background_matrix = [[default_fill_code for _ in range(22)] for _ in range(6)]

        # Split message into lines to fit within 22 characters per line
        words = message.split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + (1 if current_line else 0) <= 22:
                current_line += (" " if current_line else "") + word
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        # Apply justification
        justified_lines = []
        for line in lines[:6]:  # Only take up to 6 lines
            codes = self.convert_text_to_codes(line)
            if justify == "left":
                justified_line = codes + [None] * (22 - len(codes))
            elif justify == "right":
                justified_line = [None] * (22 - len(codes)) + codes
            elif justify == "center":
                padding = (22 - len(codes)) // 2
                justified_line = [None] * padding + codes + [None] * (22 - len(codes) - padding)
            justified_lines.append(justified_line)

        # Center vertically if justification is "center"
        if justify == "center":
            top_padding = (6 - len(justified_lines)) // 2
            justified_lines = [[None] * 22] * top_padding + justified_lines + [[None] * 22] * (6 - len(justified_lines) - top_padding)

        # Fill in the message matrix, preserving background for spaces
        message_matrix = [row[:] for row in background_matrix]  # Create a copy of the background matrix
        for i, justified_line in enumerate(justified_lines):
            for j, code in enumerate(justified_line):
                if code is not None:  # Only add non-space characters
                    message_matrix[i][j] = code

        return message_matrix
        
# Example usage
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Send a message to a Vestaboard.")
    parser.add_argument("--message", help="The message to be displayed on the Vestaboard.")
    parser.add_argument("--color", help="The color to use for the background fill (optional).")
    parser.add_argument("--justify", choices=["left", "center", "right"], default="left", help="The text justification (left, center, right).")
    parser.add_argument("--gradient", nargs=2, help="Specify the start and end colors for a gradient background.")
    parser.add_argument("--debug", action="store_true", help="Enable debug output.")
    args = parser.parse_args()

    # If no command-line arguments are provided, ask for user input
    if not args.message:
        args.message = input("Enter the message to be displayed on the Vestaboard: ")

    # Initialize Vestaboard instance
    vestaboard = Vestaboard(API_KEY, BASE_URL, debug=args.debug)

    # Create a message matrix with optional gradient background
    message_matrix = vestaboard.create_message_matrix(args.message, args.color, args.justify, args.gradient)

    # Send the message to the Vestaboard
    vestaboard.send_message(message_matrix)
