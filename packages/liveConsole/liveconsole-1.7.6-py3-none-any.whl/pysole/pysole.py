import threading
import time
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import inspect
import sys
import io
import json

from .utils import settingsPath, themesPath, stdPrint
from .helpTab import HelpTab
from .mainConsole import InteractiveConsoleText

class StdoutRedirect(io.StringIO):
    """Redirects stdout/stderr to a callback function."""
    
    def __init__(self, writeCallback):
        super().__init__()
        self.writeCallback = writeCallback

    def write(self, s):
        if s.strip():
            self.writeCallback(s, "output")

    def flush(self):
        pass

class StdinRedirect(io.StringIO):
    """Redirects stdin to capture input() from the console."""
    def __init__(self, readCallback):
        super().__init__()
        self.readCallback = readCallback

    def readline(self, *args, **kwargs):
        return(self.readCallback())

class InteractiveConsole(ctk.CTk):
    """Main console window application."""

    def __init__(self, userGlobals=None, userLocals=None, callerFrame=None,
                 defaultSize=None, primaryPrompt=None, font=None, fontSize=None,
                 runRemainingCode=False, printStartupCode=False,
                 removeWaterMark=False):
        super().__init__()
        with open(settingsPath, "r") as f:
            settings = json.load(f)
        self.THEME = settings["THEME"]
        self.FONT = self.THEME["FONT"]
        self.BEHAVIOR = settings["BEHAVIOR"]

        if primaryPrompt != None:
            self.BEHAVIOR["PRIMARY_PROMPT"] = primaryPrompt
        if defaultSize != None:
            self.BEHAVIOR["DEFAULT_SIZE"] = defaultSize
        if font != None:
            self.FONT["FONT"] = font
        if fontSize != None:
            self.FONT["FONT_SIZE"] = fontSize

        self.title("Live Interactive Console")
        self.geometry(self.BEHAVIOR["DEFAULT_SIZE"])

        ctk.set_appearance_mode(self.THEME["APPEARANCE"])
        ctk.set_default_color_theme("blue")

        # Get namespace from caller if not provided
        if userGlobals is None or userLocals is None:
            if callerFrame == None:
                callerFrame = inspect.currentframe().f_back
            if userGlobals is None:
                userGlobals = callerFrame.f_globals
            if userLocals is None:
                userLocals = callerFrame.f_locals

        self.userGlobals = userGlobals
        self.userLocals = userLocals

        # Create UI
        self._createMenu()
        self._createUi()

        # Redirect stdout/stderr
        self._setupOutputRedirect()
        self._setupInputRedirect()
        
        self.runRemainingCode = runRemainingCode
        self.printStartupCode = printStartupCode
        self.removeWaterMark = removeWaterMark
        self.startupCode = ()
        if runRemainingCode:
            code_obj = callerFrame.f_code
            filename = code_obj.co_filename

            # Read the rest of the file after the call to probe()
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()

            startLineIndex = callerFrame.f_lineno
            startLine = lines[startLineIndex - 1]
            leadingWhitespaceLen = len(startLine) - len(startLine.lstrip())
            self.startupCode = lines[startLineIndex:]
            self.startupCode = [line.rstrip()[leadingWhitespaceLen:] for line in self.startupCode]

    def _createMenu(self):
        """Create a menu bar using CTkOptionMenu."""
        menuBar = ctk.CTkFrame(self, fg_color=self.THEME["BACKGROUND"])
        menuBar.pack(side="top", fill="x")

        self.menu_var = ctk.StringVar(value="File")
        fileMenu = ctk.CTkOptionMenu(menuBar,
                                     values=["Edit Settings", "Load Theme"],
                                     variable=self.menu_var,
                                     command=self._handleMenu,
                                     fg_color=self.THEME["BACKGROUND"],
                                     button_color=self.THEME["BACKGROUND"],
                                     button_hover_color=self.THEME["HIGHLIGHTED_BACKGROUND"],
                                     dropdown_fg_color=self.THEME["BACKGROUND"],
                                     dropdown_hover_color=self.THEME["HIGHLIGHTED_BACKGROUND"],
                                     dropdown_text_color=self.THEME["FOREGROUND"],
                                     text_color=self.THEME["FOREGROUND"])
        fileMenu.pack(side="left", padx=5, pady=2)

    def _handleMenu(self, choice):
        if choice == "Edit Settings":
            self._editSettings()
        elif choice == "Load Theme":
            self._loadTheme()

    def _loadTheme(self):
        """
        Open a CTk popup to let the user choose a theme from themes.json.
        The chosen theme will override the THEME key in settings.json
        and apply immediately.
        """

        # Load themes from themes.json
        try:
            with open(themesPath, "r") as f:
                themes = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load themes.json:\n{e}")
            return

        if not themes:
            messagebox.showerror("Error", "No themes found in themes.json")
            return

        # Create the CTk popup window
        popup = ctk.CTkToplevel(self)
        popup.title("Select Theme")
        popup.geometry("300x150")
        popup.grab_set()

        ctk.CTkLabel(popup, text="Choose a theme:").pack(pady=(10, 5))

        # Dropdown with theme keys
        themeVar = tk.StringVar(value=list(themes.keys())[0])
        themeDropdown = ctk.CTkOptionMenu(popup, values=list(themes.keys()), variable=themeVar)
        themeDropdown.pack(pady=5)

        def applyTheme():
            chosenKey = themeVar.get()
            chosenTheme = themes[chosenKey]

            # Update self.THEME
            self.THEME = chosenTheme

            # Save to settings.json
            try:
                with open(settingsPath, "r") as f:
                    settings = json.load(f)
                settings["THEME"] = chosenTheme
                with open(settingsPath, "w") as f:
                    json.dump(settings, f, indent=4)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save settings.json:\n{e}")
                return

            messagebox.showinfo("Theme Applied", f"Theme '{chosenKey}' applied successfully, relaunch app for changes to take effect!")
            popup.destroy()

        applyBtn = ctk.CTkButton(popup, text="Apply", command=applyTheme)
        applyBtn.pack(pady=(10, 10))

    def _editSettings(self):
        """Open a simple JSON editor for settings.json."""
        editor = ctk.CTkToplevel(self)
        editor.title("Edit Settings")
        editor.geometry("500x400")

        try:
            with open(settingsPath, "r") as f:
                jsonText = f.read()
        except Exception as e:
            jsonText = f"{{}}\n\n# Failed to load settings.json:\n{e}"

        textbox = ctk.CTkTextbox(editor)
        textbox.pack(fill="both", expand=True, padx=10, pady=10)
        textbox.insert("0.0", jsonText)

        def saveSettings():
            try:
                newSettings = json.loads(textbox.get("0.0", "end-1c"))
                with open("settings.json", "w") as f:
                    json.dump(newSettings, f, indent=4)
                messagebox.showinfo("Success", "Settings saved!")
                editor.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid JSON:\n{e}")

        saveBtn = ctk.CTkButton(editor, text="Save", command=saveSettings)
        saveBtn.pack(pady=5)

    def _createUi(self):
        """Create UI with console and help tab."""
        frame = ctk.CTkFrame(self)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Horizontal frame
        self.horizFrame = ctk.CTkFrame(frame)
        self.horizFrame.pack(fill="both", expand=True)

        # Right: Help Tab
        self.helpTab = HelpTab(self.horizFrame, theme=self.THEME, font=self.FONT, width=500)

        # Left: Console
        self.consoleFrame = ctk.CTkFrame(self.horizFrame, width=600)
        self.consoleFrame.pack(side="left", fill="both", expand=True)
        self.consoleFrame.pack_propagate(False)  # prevent shrinking to fit contents

        self.console = InteractiveConsoleText(
            self.consoleFrame,
            self.helpTab,
            userGlobals=self.userGlobals,
            userLocals=self.userLocals,
            theme=self.THEME,
            font=self.FONT,
            behavior=self.BEHAVIOR,
            wrap="word",
            bg=self.THEME["BACKGROUND"],
            fg=self.THEME["FOREGROUND"],
            insertbackground=self.THEME["INSERTBACKGROUND"]
        )
        self.console.pack(fill="both", expand=True, padx=5, pady=5)
        self.console.master = self

    def _setupOutputRedirect(self):
        """Setup stdout/stderr redirection to console."""
        sys.stdout = StdoutRedirect(self.console.writeOutput)
        sys.stderr = StdoutRedirect(
            lambda text, tag: self.console.writeOutput(text, "error", "end")
        )

    def _setupInputRedirect(self):
        """Setup stdin redirection to console."""
        sys.stdin = StdinRedirect(self.console.readInput)

    def onClose(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        self.destroy()
    
    def _printWaterMark(self):
        m = (
            "Welcome to Pysole, if you find me useful, please star me on GitHub:\n"
            "https://github.com/TzurSoffer/Pysole"
        )
        stdPrint(m)
        self.console.newline()
        self.console.writeOutput(m, "instruction")
        time.sleep(0.1)
        if self.runRemainingCode:
            if self.printStartupCode:
                self.console.addPrompt()
            else:
                self.console.newline()
        else:
            self.console.addPrompt()
    
    def _splitCodeIntoChunks(self):
        codeChunks = []
        currentChunk = []

        for line in self.startupCode:
            strippedLine = line.lstrip()
            indentLevel = len(line) - len(strippedLine)

            if not strippedLine:  #< Blank line, keep it in current chunk
                currentChunk.append(line)
                continue

            if indentLevel != 0:
                currentChunk.append(line)
            else:
                codeChunks.append(currentChunk)
                currentChunk = [line]

        if currentChunk:
            codeChunks.append(currentChunk)

        return(["\n".join(chunk).strip() for chunk in codeChunks if any(line.strip() for line in chunk)])

    
    def _runStartup(self):
        if self.removeWaterMark == False:
            self._printWaterMark()

        if self.runRemainingCode == False:
            return

        if self.printStartupCode == False:
            self.console.newline()
            code = "\n".join(self.startupCode)
            self.console.executeCommandThreaded(code, addPrompt=True)
            return
        
        chunks = self._splitCodeIntoChunks()
        for chunk in chunks:
            while self.console.isExecuting:
                time.sleep(0.01)
            self.console.runCommand(chunk, printCommand=True, clearPrompt=True)

    def probe(self, *args, **kwargs):
        """Start the console main loop."""
        self.after(0, threading.Thread(target=self._runStartup).start)
        self.mainloop(*args, **kwargs)

def probe(userGlobals=None, userLocals=None, callerFrame=None,
          runRemainingCode=False, printStartupCode=False,
          primaryPrompt=None, font=None, fontSize=None, **kwargs):
    if callerFrame == None:
        callerFrame = inspect.currentframe().f_back
    InteractiveConsole(userGlobals=userGlobals,
                              userLocals=userLocals,
                              callerFrame=callerFrame,
                              runRemainingCode=runRemainingCode,
                              printStartupCode=printStartupCode,
                              primaryPrompt=primaryPrompt,
                              font=font,
                              fontSize=fontSize,
                              removeWaterMark=False,
                              **kwargs).probe()

def _standalone():
    import pysole
    pysole.probe(callerFrame=inspect.currentframe().f_back)

# Example usage
if __name__ == "__main__":
    _standalone()