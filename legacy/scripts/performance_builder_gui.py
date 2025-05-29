import tkinter as tk
from tkinter import ttk
from mido import get_output_names, open_output, Message
import json

PATCH_DB_FILE = "jv1080_patch_database.json"

def load_patch_db():
    with open(PATCH_DB_FILE, 'r') as f:
        data = json.load(f)
    patch_map = {}
    for patch in data:
        bank = patch['bank']
        if bank not in patch_map:
            patch_map[bank] = []
        patch_map[bank].append(patch)
    return patch_map

class PerformanceBuilderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JV-1080 Performance Builder")
        self.patch_db = load_patch_db()
        self.midi_port = tk.StringVar()
        self.part_frames = []
        self.create_midi_selector()
        self.create_parts_ui()
        self.create_send_button()

    def create_midi_selector(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)
        tk.Label(frame, text="Select MIDI Output Port:").pack(side=tk.LEFT)
        self.midi_dropdown = ttk.Combobox(frame, textvariable=self.midi_port, values=get_output_names(), width=40)
        self.midi_dropdown.pack(side=tk.LEFT)

    def create_parts_ui(self):
        self.parts = []
        for part_num in range(1, 17):
            frame = tk.LabelFrame(self.root, text=f"Part {part_num}")
            frame.pack(fill="x", padx=5, pady=2)
            row = {}
            row["bank"] = ttk.Combobox(frame, values=sorted(self.patch_db.keys()), width=12)
            row["bank"].grid(row=0, column=0, padx=2)
            row["patch"] = ttk.Combobox(frame, width=30)
            row["patch"].grid(row=0, column=1, padx=2)
            row["volume"] = tk.Scale(frame, from_=0, to=127, orient="horizontal", label="Volume")
            row["volume"].grid(row=0, column=2)
            row["pan"] = tk.Scale(frame, from_=0, to=127, orient="horizontal", label="Pan")
            row["pan"].grid(row=0, column=3)
            row["fx"] = ttk.Combobox(frame, values=["Reverb", "Chorus", "MFX"], width=10)
            row["fx"].grid(row=0, column=4, padx=2)
            row["fx_send"] = tk.Scale(frame, from_=0, to=127, orient="horizontal", label="FX Send")
            row["fx_send"].grid(row=0, column=5)
            row["output"] = ttk.Combobox(frame, values=["MAIN", "SUB A", "SUB B"], width=10)
            row["output"].grid(row=0, column=6, padx=2)
            row["bank"].bind("<<ComboboxSelected>>", lambda e, r=row: self.update_patch_list(r))
            self.parts.append(row)

    def update_patch_list(self, row):
        selected_bank = row["bank"].get()
        patches = self.patch_db.get(selected_bank, [])
        patch_names = [f"{p['number']:03d} - {p['name']}" for p in patches]
        row["patch"]["values"] = patch_names
        if patch_names:
            row["patch"].current(0)

    def create_send_button(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)
        tk.Button(frame, text="Send to JV-1080", command=self.send_all_sysex).pack()

    def send_all_sysex(self):
        port_name = self.midi_port.get()
        if not port_name:
            print("No MIDI port selected.")
            return
        try:
            with open_output(port_name) as port:
                for idx, row in enumerate(self.parts):
                    patch_name = row["patch"].get()
                    if patch_name:
                        patch_number = int(patch_name.split(" - ")[0])
                        port.send(Message('program_change', channel=idx, program=patch_number))
                        print(f"Sent patch {patch_number} to part {idx+1}")
        except Exception as e:
            print(f"Failed to send MIDI: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PerformanceBuilderApp(root)
    root.mainloop()