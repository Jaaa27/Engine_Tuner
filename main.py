import customtkinter as ctk
from ui.tuner_window import TunerWindow

def main():
    root = ctk.CTk()
    app = TunerWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
