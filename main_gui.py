import os
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
from retarget_engine import RetargetEngine

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class RetargeterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("UE to Arma Reforger Animation Retargeter")
        self.geometry("780x620")
        self.minsize(700, 550)

        self.source_files = []
        self.target_rig_path = os.path.abspath("Start.fbx")
        self.output_dir = os.path.abspath("output_reforger")

        self.engine = RetargetEngine("mapping.json")

        self.create_ui()

    def create_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        title_label = ctk.CTkLabel(header, text="⚔️ UE ➔ Arma Reforger Retargeter", font=ctk.CTkFont(size=22, weight="bold"))
        title_label.pack(anchor="w")

        desc_label = ctk.CTkLabel(header, text="Пакетный перенос анимаций Unreal Engine на скелет Enfusion Engine", text_color="gray70")
        desc_label.pack(anchor="w")

        # Configuration Cards Frame
        cards_frame = ctk.CTkFrame(self)
        cards_frame.pack(fill="x", padx=20, pady=10)

        # Target Rig Path
        rig_label = ctk.CTkLabel(cards_frame, text="Целевой скелет Arma Reforger:", font=ctk.CTkFont(weight="bold"))
        rig_label.grid(row=0, column=0, padx=15, pady=(10, 2), sticky="w")

        self.rig_entry = ctk.CTkEntry(cards_frame, width=480)
        self.rig_entry.insert(0, self.target_rig_path)
        self.rig_entry.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")

        rig_btn = ctk.CTkButton(cards_frame, text="Обзор...", width=100, command=self.browse_rig)
        rig_btn.grid(row=1, column=1, padx=15, pady=(0, 10))

        # Output Folder Path
        out_label = ctk.CTkLabel(cards_frame, text="Папка сохранения результатов:", font=ctk.CTkFont(weight="bold"))
        out_label.grid(row=2, column=0, padx=15, pady=(5, 2), sticky="w")

        self.out_entry = ctk.CTkEntry(cards_frame, width=480)
        self.out_entry.insert(0, self.output_dir)
        self.out_entry.grid(row=3, column=0, padx=15, pady=(0, 15), sticky="ew")

        out_btn = ctk.CTkButton(cards_frame, text="Обзор...", width=100, command=self.browse_output)
        out_btn.grid(row=3, column=1, padx=15, pady=(0, 15))

        cards_frame.columnconfigure(0, weight=1)

        # File List Section
        list_header = ctk.CTkFrame(self, fg_color="transparent")
        list_header.pack(fill="x", padx=20, pady=(10, 5))

        list_label = ctk.CTkLabel(list_header, text="Анимации UE для конвертации:", font=ctk.CTkFont(size=14, weight="bold"))
        list_label.pack(side="left")

        add_files_btn = ctk.CTkButton(list_header, text="+ Добавить FBX", width=120, command=self.add_files)
        add_files_btn.pack(side="right", padx=(5, 0))

        add_folder_btn = ctk.CTkButton(list_header, text="+ Папка с FBX", width=120, fg_color="gray30", hover_color="gray20", command=self.add_folder)
        add_folder_btn.pack(side="right")

        self.file_textbox = ctk.CTkTextbox(self, height=160)
        self.file_textbox.pack(fill="both", expand=True, padx=20, pady=5)
        self.file_textbox.insert("1.0", "Файлы не выбраны. Нажмите «+ Добавить FBX» или выберите папку.")

        # Progress and Action
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=15)

        self.progress_bar = ctk.CTkProgressBar(bottom_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 10))

        self.status_label = ctk.CTkLabel(bottom_frame, text="Готов к работе", text_color="gray70")
        self.status_label.pack(side="left")

        self.run_btn = ctk.CTkButton(bottom_frame, text="🚀 Конвертировать все", font=ctk.CTkFont(size=14, weight="bold"), height=38, command=self.start_batch)
        self.run_btn.pack(side="right")

    def browse_rig(self):
        f = filedialog.askopenfilename(filetypes=[("FBX files", "*.fbx")])
        if f:
            self.target_rig_path = f
            self.rig_entry.delete(0, "end")
            self.rig_entry.insert(0, f)

    def browse_output(self):
        d = filedialog.askdirectory()
        if d:
            self.output_dir = d
            self.out_entry.delete(0, "end")
            self.out_entry.insert(0, d)

    def add_files(self):
        files = filedialog.askopenfilenames(filetypes=[("FBX files", "*.fbx")])
        if files:
            self.source_files.extend(files)
            self.update_file_list()

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            for root, _, filenames in os.walk(folder):
                for fn in filenames:
                    if fn.lower().endswith(".fbx"):
                        self.source_files.append(os.path.join(root, fn))
            self.update_file_list()

    def update_file_list(self):
        self.file_textbox.delete("1.0", "end")
        if not self.source_files:
            self.file_textbox.insert("1.0", "Файлы не выбраны.")
            return
        for idx, path in enumerate(self.source_files, 1):
            self.file_textbox.insert("end", f"{idx}. {os.path.basename(path)}  ({path})\n")

    def start_batch(self):
        if not self.source_files:
            messagebox.showwarning("Внимание", "Добавьте хотя бы один FBX-файл с анимацией!")
            return

        self.run_btn.configure(state="disabled")
        threading.Thread(target=self._run_process, daemon=True).start()

    def _run_process(self):
        os.makedirs(self.output_dir, exist_ok=True)
        total = len(self.source_files)

        for i, src in enumerate(self.source_files):
            fname = os.path.basename(src)
            out_path = os.path.join(self.output_dir, f"Reforger_{fname}")
            
            self.status_label.configure(text=f"Обработка [{i+1}/{total}]: {fname}")
            
            def cb(pct, msg):
                overall = (i + pct) / total
                self.progress_bar.set(overall)
                self.status_label.configure(text=f"[{i+1}/{total}] {fname}: {msg}")

            try:
                self.engine.process_file(src, self.target_rig_path, out_path, progress_callback=cb)
            except Exception as e:
                print(f"Error on {fname}: {e}")

        self.progress_bar.set(1.0)
        self.status_label.configure(text=f"✅ Готово! Обработано файлов: {total}")
        self.run_btn.configure(state="normal")
        messagebox.showinfo("Успех", f"Пакетная конвертация завершена!\nСохранено в: {self.output_dir}")

if __name__ == "__main__":
    app = RetargeterApp()
    app.mainloop()
