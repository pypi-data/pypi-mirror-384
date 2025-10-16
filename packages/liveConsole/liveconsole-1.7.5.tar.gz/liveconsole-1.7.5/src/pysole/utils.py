import os
import sys

settingsPath = os.path.join(os.path.dirname(__file__), "settings.json")
themesPath = os.path.join(os.path.dirname(__file__), "themes.json")

def stdPrint(text):
    """Print text to the terminal."""
    try:
        sys.__stdout__.write(f"{text}\n")
        sys.__stdout__.flush()
    except:
        pass