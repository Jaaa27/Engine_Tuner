import tkinter as tk
from ui.tuner_window import TunerWindow

def main():
    root = tk.Tk()
    TunerWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
