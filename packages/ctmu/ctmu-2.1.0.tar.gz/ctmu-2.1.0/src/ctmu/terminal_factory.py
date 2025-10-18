"""Terminal-specific QR display factory"""

import os
from abc import ABC, abstractmethod

class BaseTerminalDisplay(ABC):
    @abstractmethod
    def display(self, image):
        pass

class iTerm2Display(BaseTerminalDisplay):
    def display(self, image):
        # iTerm2 supports better Unicode blocks
        width, height = image.size
        for y in range(0, height, 2):
            line = ""
            for x in range(width):
                pixel = image.getpixel((x, y))
                line += "█" if sum(pixel[:3]) < 384 else " "
            print(line)

class StandardTerminalDisplay(BaseTerminalDisplay):
    def display(self, image):
        # Standard terminal display
        width, height = image.size
        for y in range(0, height, 2):
            line = ""
            for x in range(width):
                pixel = image.getpixel((x, y))
                line += "██" if sum(pixel[:3]) < 384 else "  "
            print(line)

class TerminalFactory:
    @staticmethod
    def create_display():
        term_program = os.environ.get('TERM_PROGRAM', '')
        if 'iTerm' in term_program:
            return iTerm2Display()
        return StandardTerminalDisplay()