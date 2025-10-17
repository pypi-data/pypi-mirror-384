from tkinter import Label, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from pathlib import Path
import re
import piket

class ConverterApp:
    def __init__(self, root: TkinterDnD.Tk):
        self.root = root
        self.root.title("Pikmin e+ Converter")
        self.label = Label(
            self.root,
            text="Drag .raw to get .bin (trimmed + decompressed)\n\n" \
                "Drag (.bin + original .raw) to get .raw",
            width=50, height=10, bg="lightgray")
        self.label.pack(padx=10, pady=10)
        self.center_window()

        self.label.drop_target_register(DND_FILES) # type: ignore
        self.label.dnd_bind('<<Drop>>', self.on_file_drop) # type: ignore
        
    def center_window(self):
        root = self.root
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")

    def on_file_drop(self, event):
        paths = [f[0] or f[1] for f in re.findall(r'\{([^}]*)\}|(\S+)', event.data)]
        print(f"Files dropped:\n- {"\n- ".join(paths)}")
        self.process_files([Path(file).resolve() for file in paths])

    def process_files(self, files: list[Path]):
        bin_index = next((i for i, file in enumerate(files) if file.suffix == ".bin"), None)
        if bin_index is not None:
            bin_file = files[bin_index]
            if len(files) != 2 or files[1-bin_index].suffix != ".raw":
                message = "To convert .bin to .raw, you need to ONLY drop both the new .bin and " \
                    "the original .raw (2 files)."
                print(f"[ERROR] {message}")
                messagebox.showerror("Error", message)
                return

            raw_file = files[1-bin_index]
            self.process_bin_file(bin_file, raw_file)

        else:
            for file in files:
                self.process_raw_file(file)
    
    def process_raw_file(self, file: Path):
        out = file.with_suffix(".bin")
        out.write_bytes(piket.decode_raw(file))
        
    def process_bin_file(self, file: Path, original_raw: Path):
        out = original_raw.with_stem(original_raw.stem + "_new")
        out.write_bytes(piket.encode_raw(original_raw, file))

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ConverterApp(root)
    root.mainloop()
