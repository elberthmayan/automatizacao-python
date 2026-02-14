import os
import shutil
import datetime
import platform
import sys
import threading
import time
import json
import customtkinter as ctk
from tkinter import filedialog, messagebox

# --- Dependências Opcionais ---
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from moviepy.editor import VideoFileClip, AudioFileClip
    HAS_MOVIEPY = True
except ImportError:
    HAS_MOVIEPY = False

# --- Configurações Iniciais ---
ctk.set_appearance_mode("Dark")  # Padrão inicial
ctk.set_default_color_theme("blue")

# === PALETA DE CORES INTELIGENTE (Light, Dark) ===
COLOR_BG = ("#F3F4F6", "#121212")           
COLOR_SIDEBAR = ("#FFFFFF", "#0A0A0A")      
COLOR_CARD = ("#FFFFFF", "#1E1E1E")         
COLOR_CARD_BORDER = ("#E5E7EB", "#2A2A2A")  

COLOR_INPUT_BG = ("#F9FAFB", "#181818")     
COLOR_INPUT_BORDER = ("#D1D5DB", "#333333")

COLOR_TEXT_MAIN = ("#111827", "#E0E0E0")
COLOR_TEXT_DIM = ("#6B7280", "#9CA3AF")

COLOR_ACCENT = ("#2563EB", "#2962FF")       
COLOR_ACCENT_HOVER = ("#1D4ED8", "#0039CB")
COLOR_SUCCESS = ("#059669", "#00C853")
COLOR_ERROR = ("#DC2626", "#CF6679")

# =============================================================================
# LÓGICA DE EXECUÇÃO EM BACKGROUND
# =============================================================================
def run_headless_organizer():
    target_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    try:
        if os.path.exists("nexus_config.json"):
            with open("nexus_config.json", "r") as f:
                cfg = json.load(f)
                if "last_organizer_path" in cfg and os.path.exists(cfg["last_organizer_path"]):
                    target_dir = cfg["last_organizer_path"]
    except: pass

    if not os.path.exists(target_dir): return

    moved = 0
    ext_map = {
        'Imagens': ['.jpg','.png','.gif','.webp','.jpeg','.svg'], 
        'Documentos': ['.pdf','.docx','.txt','.xlsx','.pptx'], 
        'Apps': ['.exe','.msi','.bat','.iso'], 
        'Compactados': ['.zip','.rar','.7z'], 
        'Midia': ['.mp4','.mp3','.mkv','.wav']
    }
    
    for f in os.listdir(target_dir):
        fp = os.path.join(target_dir, f)
        if not is_safe_to_move(fp): continue
        _, ext = os.path.splitext(f)
        cat = "Outros"
        for k, v in ext_map.items(): 
            if ext.lower() in v: cat = k; break
        d = datetime.datetime.fromtimestamp(os.path.getmtime(fp)).strftime('%Y-%m')
        dest = os.path.join(target_dir, cat, d)
        os.makedirs(dest, exist_ok=True)
        try:
            shutil.move(fp, os.path.join(dest, f))
            moved += 1
        except: pass

    if moved > 0:
        root = ctk.CTk()
        root.withdraw() 
        messagebox.showinfo("PyAutomator", f"Organização Automática:\n{moved} arquivos organizados.")
        root.destroy()

def run_headless_cleaner():
    count = 0
    paths = [os.environ.get('TEMP')] if platform.system() == "Windows" else ["/tmp"]
    for p in paths:
        if not p: continue
        for root_dir, _, files in os.walk(p):
            for f in files:
                try: os.remove(os.path.join(root_dir, f)); count += 1
                except: pass
    if count > 0:
        root = ctk.CTk()
        root.withdraw()
        messagebox.showinfo("PyAutomator", f"Limpeza Automática:\n{count} arquivos removidos.")
        root.destroy()

def is_safe_to_move(filepath):
    if os.path.isdir(filepath): return False
    if os.path.basename(filepath).startswith("log_"): return False
    try:
        size1 = os.path.getsize(filepath)
        time.sleep(1.0)
        size2 = os.path.getsize(filepath)
        if size1 != size2: return False 
    except: return False
    try:
        new = filepath + "_check"
        os.rename(filepath, new); os.rename(new, filepath)
        return True
    except: return False

# =============================================================================
# INTERFACE GRÁFICA PRINCIPAL
# =============================================================================
class AutomationHub(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config_file = "nexus_config.json"
        self.config = self.load_config()

        self.title("PyAutomator - System Hub")
        self.geometry("1100x750")
        self.minsize(950, 650)
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === SIDEBAR ===
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        # Logo
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="PY AUTOMATOR", 
                                     font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
                                     text_color=COLOR_TEXT_MAIN)
        self.logo_label.grid(row=0, column=0, padx=25, pady=(40, 10), sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(self.sidebar_frame, text="SUITE V8.5", 
                                         text_color=COLOR_ACCENT,
                                         font=ctk.CTkFont(size=11, weight="bold"))
        self.subtitle_label.grid(row=1, column=0, padx=25, pady=(0, 30), sticky="w")

        # Botões Menu
        self.btn_home = self.create_nav_button("DASHBOARD", self.show_home)
        self.btn_home.grid(row=2, column=0, padx=15, pady=5, sticky="ew")
        self.btn_organizer = self.create_nav_button("ORGANIZAR", self.show_organizer)
        self.btn_organizer.grid(row=3, column=0, padx=15, pady=5, sticky="ew")
        self.btn_cleaner = self.create_nav_button("LIMPEZA", self.show_cleaner)
        self.btn_cleaner.grid(row=4, column=0, padx=15, pady=5, sticky="ew")
        self.btn_renamer = self.create_nav_button("RENOMEAR", self.show_renamer)
        self.btn_renamer.grid(row=5, column=0, padx=15, pady=5, sticky="ew")
        self.btn_converter = self.create_nav_button("CONVERSOR", self.show_converter)
        self.btn_converter.grid(row=6, column=0, padx=15, pady=5, sticky="ew")
        self.btn_energy = self.create_nav_button("ENERGIA", self.show_energy)
        self.btn_energy.grid(row=7, column=0, padx=15, pady=5, sticky="ew")

        # Switch de Tema
        self.theme_switch_var = ctk.StringVar(value="Dark")
        self.theme_switch = ctk.CTkSwitch(self.sidebar_frame, text="Modo Escuro", command=self.toggle_theme, 
                                        variable=self.theme_switch_var, onvalue="Dark", offvalue="Light",
                                        progress_color=COLOR_ACCENT, text_color=COLOR_TEXT_MAIN, font=ctk.CTkFont(size=12))
        self.theme_switch.grid(row=11, column=0, padx=25, pady=(0, 20), sticky="w")

        # === CONTEÚDO ===
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color=COLOR_BG)
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (HomeFrame, OrganizerFrame, CleanerFrame, RenamerFrame, ConverterFrame, EnergyFrame):
            frame = F(self.content_area, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_home()

    def toggle_theme(self):
        mode = self.theme_switch_var.get()
        ctk.set_appearance_mode(mode)
        self.theme_switch.configure(text="Modo Escuro" if mode == "Dark" else "Modo Claro")

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f: return json.load(f)
            except: return {}
        return {}

    def save_setting(self, key, value):
        self.config[key] = value
        try:
            with open(self.config_file, "w") as f: json.dump(self.config, f)
        except: pass

    def get_setting(self, key, default=None):
        return self.config.get(key, default)

    def create_nav_button(self, text, command):
        return ctk.CTkButton(self.sidebar_frame, text=text, fg_color="transparent", 
                           text_color=COLOR_TEXT_DIM, hover_color=COLOR_CARD, anchor="w",
                           height=40, font=ctk.CTkFont(size=12, weight="bold"), command=command)

    def highlight_btn(self, active_btn):
        for btn in [self.btn_home, self.btn_organizer, self.btn_cleaner, self.btn_renamer, self.btn_converter, self.btn_energy]:
            btn.configure(fg_color="transparent", text_color=COLOR_TEXT_DIM)
        active_btn.configure(text_color=COLOR_TEXT_MAIN, fg_color=COLOR_CARD)

    def show_frame(self, frame_class, btn):
        frame = self.frames[frame_class]
        frame.tkraise()
        self.highlight_btn(btn)
        if hasattr(frame, 'on_show'): frame.on_show()

    def show_home(self): self.show_frame(HomeFrame, self.btn_home)
    def show_organizer(self): self.show_frame(OrganizerFrame, self.btn_organizer)
    def show_cleaner(self): self.show_frame(CleanerFrame, self.btn_cleaner)
    def show_renamer(self): self.show_frame(RenamerFrame, self.btn_renamer)
    def show_converter(self): self.show_frame(ConverterFrame, self.btn_converter)
    def show_energy(self): self.show_frame(EnergyFrame, self.btn_energy)

    # Boot Logic
    def check_boot_file(self, suffix):
        sys_os = platform.system()
        if sys_os == "Windows":
            p = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup', f"PyAuto_{suffix}.bat")
            return os.path.exists(p)
        elif sys_os == "Linux":
            p = os.path.expanduser(f"~/.config/autostart/pyauto_{suffix.lower()}.desktop")
            return os.path.exists(p)
        return False

    def toggle_boot(self, state, suffix, flag):
        app_path = os.path.abspath(sys.argv[0])
        sys_os = platform.system()
        try:
            if sys_os == "Windows":
                p = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup', f"PyAuto_{suffix}.bat")
                if state == "on":
                    with open(p, "w") as f: f.write(f'@echo off\nstart "" pythonw "{app_path}" {flag}')
                else:
                    if os.path.exists(p): os.remove(p)
            elif sys_os == "Linux":
                p = os.path.expanduser(f"~/.config/autostart/pyauto_{suffix.lower()}.desktop")
                if state == "on":
                    os.makedirs(os.path.dirname(p), exist_ok=True)
                    with open(p, "w") as f: f.write(f"[Desktop Entry]\nType=Application\nExec=python3 \"{app_path}\" {flag}\nHidden=false\nX-GNOME-Autostart-enabled=true\nName=PyAutomator {suffix}")
                else:
                    if os.path.exists(p): os.remove(p)
            return True
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return False


# === TELA HOME ===
class HomeFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        
        self.grid_columnconfigure((0, 1, 2), weight=1)
        
        ctk.CTkLabel(self, text="Bem-vindo", font=ctk.CTkFont(size=28, weight="bold"), text_color=COLOR_TEXT_MAIN).grid(row=0, column=0, columnspan=3, padx=30, pady=(30, 5), sticky="w")
        ctk.CTkLabel(self, text="Selecione uma ferramenta.", text_color=COLOR_TEXT_DIM).grid(row=1, column=0, columnspan=3, padx=30, pady=(0, 20), sticky="w")

        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.grid(row=2, column=0, columnspan=3, padx=20, sticky="nsew")
        self.cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.create_card(0, 0, "📂 Organizador", "Organizar arquivos.", controller.show_organizer)
        self.create_card(0, 1, "🧹 Limpeza", "Limpar temporários.", controller.show_cleaner)
        self.create_card(0, 2, "⚡ Energia", "Auto Shutdown.", controller.show_energy)
        self.create_card(1, 0, "✏️ Renomeador", "Renomear em massa.", controller.show_renamer)
        self.create_card(1, 1, "📸 Conversor", "Img & Vídeo Converter.", controller.show_converter)

    def create_card(self, row, col, title, desc, command):
        card = ctk.CTkFrame(self.cards_frame, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_CARD_BORDER)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew", ipady=5)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=15, weight="bold"), text_color=COLOR_TEXT_MAIN).pack(pady=(15, 5), padx=15, anchor="w")
        ctk.CTkLabel(card, text=desc, text_color=COLOR_TEXT_DIM, font=ctk.CTkFont(size=11)).pack(pady=(0, 15), padx=15, anchor="w")
        ctk.CTkButton(card, text="ABRIR", fg_color="transparent", border_width=1, border_color=COLOR_ACCENT,
                      text_color=COLOR_ACCENT, hover_color=COLOR_CARD_BORDER, height=28,
                      font=ctk.CTkFont(size=11, weight="bold"), command=command).pack(pady=(0, 15), padx=15, anchor="e")


# === TELA ORGANIZADOR ===
class OrganizerFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        ctk.CTkLabel(self, text="Organizador de Arquivos", font=ctk.CTkFont(size=22, weight="bold"), text_color=COLOR_TEXT_MAIN).grid(row=0, column=0, padx=40, pady=(30, 20), sticky="w")
        
        # Container Card
        container = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_CARD_BORDER)
        container.grid(row=1, column=0, padx=40, sticky="ew") # Changed to 'ew' to avoid huge vertical stretch
        container.grid_columnconfigure(0, weight=1)
        
        # Input Area (Compacta)
        input_frame = ctk.CTkFrame(container, fg_color="transparent")
        input_frame.grid(row=0, column=0, padx=25, pady=(25, 15), sticky="ew")
        
        self.path_entry = ctk.CTkEntry(input_frame, placeholder_text="Pasta Alvo...", height=35, 
                                     border_color=COLOR_CARD_BORDER, fg_color=COLOR_INPUT_BG, text_color=COLOR_TEXT_MAIN)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(input_frame, text="Buscar", width=100, height=35, fg_color=COLOR_INPUT_BORDER, 
                    text_color=COLOR_TEXT_MAIN, hover_color=COLOR_CARD_BORDER, command=self.browse).pack(side="right")

        # Botão Ação
        ctk.CTkButton(container, text="INICIAR ORGANIZAÇÃO", height=40, 
                    fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, 
                    font=ctk.CTkFont(size=13, weight="bold"), command=self.run).grid(row=1, column=0, padx=25, pady=(0, 20), sticky="ew")

        # Log Header + Box (Fixed Height to avoid empty space look)
        ctk.CTkLabel(container, text="📝 Status / Log", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_DIM).grid(row=2, column=0, padx=25, pady=(5,0), sticky="w")
        
        self.log_box = ctk.CTkTextbox(container, height=120, fg_color=COLOR_INPUT_BG, text_color=COLOR_TEXT_DIM, 
                                    border_width=1, border_color=COLOR_CARD_BORDER, corner_radius=6)
        self.log_box.grid(row=3, column=0, padx=25, pady=(5, 25), sticky="nsew")
        
        # Footer Boot (External to Card)
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, padx=40, pady=10, sticky="ew")
        self.boot_var = ctk.StringVar(value="off")
        self.switch = ctk.CTkSwitch(footer, text="Iniciar Automaticamente no Boot", 
                                  command=self.toggle_boot, variable=self.boot_var, 
                                  onvalue="on", offvalue="off", progress_color=COLOR_ACCENT, text_color=COLOR_TEXT_MAIN)
        self.switch.pack(side="right")

    def on_show(self):
        self.load_saved_path()
        self.update_boot_status()

    def load_saved_path(self):
        saved = self.controller.get_setting("last_organizer_path")
        default = os.path.join(os.path.expanduser("~"), "Downloads")
        path = saved if saved and os.path.exists(saved) else default
        self.path_entry.delete(0, "end"); self.path_entry.insert(0, path)

    def update_boot_status(self):
        if self.controller.check_boot_file("Organizer"): self.switch.select()
        else: self.switch.deselect()

    def toggle_boot(self):
        state = self.boot_var.get()
        if self.controller.toggle_boot(state, "Organizer", "--boot-organizer"):
            msg = "Boot Ativado." if state == "on" else "Boot Desativado."
            messagebox.showinfo("Sucesso", msg)
        else:
            if state == "on": self.switch.deselect()
            else: self.switch.select()

    def browse(self):
        f = filedialog.askdirectory()
        if f: 
            self.path_entry.delete(0, "end"); self.path_entry.insert(0, f)
            self.controller.save_setting("last_organizer_path", f)

    def run(self):
        folder = self.path_entry.get()
        if not os.path.exists(folder): return
        threading.Thread(target=self.logic, args=(folder,)).start()

    def logic(self, folder):
        self.log(">>> Processando...")
        ext_map = {'Imagens':['.jpg','.png','.gif','.webp','.jpeg'], 'Docs':['.pdf','.docx','.txt','.xlsx'], 'Apps':['.exe','.msi','.bat'], 'Zips':['.zip','.rar'], 'Midia':['.mp4','.mp3','.wav']}
        try:
            c = 0
            for f in os.listdir(folder):
                fp = os.path.join(folder, f)
                if not is_safe_to_move(fp): continue
                _, ext = os.path.splitext(f)
                cat = "Outros"
                for k, v in ext_map.items(): 
                    if ext.lower() in v: cat = k; break
                d = datetime.datetime.fromtimestamp(os.path.getmtime(fp)).strftime('%Y-%m')
                dest = os.path.join(folder, cat, d)
                os.makedirs(dest, exist_ok=True)
                shutil.move(fp, os.path.join(dest, f))
                self.log(f"✔ {f}")
                c += 1
            messagebox.showinfo("Sucesso", f"{c} arquivos organizados.")
        except Exception as e: self.log(f"Erro: {e}")

    def log(self, t):
        self.log_box.insert("end", t+"\n")
        self.log_box.see("end")


# === TELA LIMPEZA ===
class CleanerFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="Limpeza de Sistema", font=ctk.CTkFont(size=22, weight="bold"), text_color=COLOR_TEXT_MAIN).grid(row=0, column=0, padx=40, pady=(30, 20), sticky="w")
        
        container = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_CARD_BORDER)
        container.grid(row=1, column=0, padx=40, sticky="ew") # Compact card
        container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(container, text="🧹 LIMPEZA DE CACHE", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLOR_TEXT_DIM).pack(pady=(40, 10))
        ctk.CTkLabel(container, text="Remove arquivos temporários seguros (%TEMP%).", text_color="gray").pack()

        ctk.CTkButton(container, text="EXECUTAR LIMPEZA AGORA", height=45, width=250,
                    fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                    font=ctk.CTkFont(weight="bold"), command=self.run).pack(pady=30)
        
        self.status = ctk.CTkLabel(container, text="", font=ctk.CTkFont(weight="bold"), text_color=COLOR_TEXT_MAIN)
        self.status.pack(pady=(0, 20))

        # Boot Toggle
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, padx=40, pady=10, sticky="ew")
        self.boot_var = ctk.StringVar(value="off")
        self.switch = ctk.CTkSwitch(footer, text="Iniciar no Boot", 
                                  command=self.toggle_boot, variable=self.boot_var, 
                                  onvalue="on", offvalue="off", progress_color=COLOR_ACCENT, text_color=COLOR_TEXT_MAIN)
        self.switch.pack(side="right")

    def on_show(self): self.update_boot_status()
    def update_boot_status(self):
        if self.controller.check_boot_file("Cleaner"): self.switch.select()
        else: self.switch.deselect()

    def toggle_boot(self):
        state = self.boot_var.get()
        if self.controller.toggle_boot(state, "Cleaner", "--boot-cleaner"):
            messagebox.showinfo("Sucesso", "Configuração salva.")
        else:
            if state == "on": self.switch.deselect()
            else: self.switch.select()

    def run(self):
        if not messagebox.askyesno("Confirmar", "Limpar temporários?"): return
        self.status.configure(text="Limpando...", text_color=COLOR_ACCENT)
        threading.Thread(target=self.logic).start()

    def logic(self):
        c = 0
        paths = [os.environ.get('TEMP')] if platform.system() == "Windows" else ["/tmp"]
        for p in paths:
            if not p: continue
            for root, _, files in os.walk(p):
                for f in files:
                    try: os.remove(os.path.join(root, f)); c += 1
                    except: pass
        self.status.configure(text=f"Concluído! {c} arquivos limpos.", text_color=COLOR_SUCCESS)


# === TELA RENOMEADOR ===
class RenamerFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Renomeador em Massa", font=ctk.CTkFont(size=22, weight="bold"), text_color=COLOR_TEXT_MAIN).grid(row=0, column=0, padx=40, pady=(30, 20), sticky="w")
        
        container = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_CARD_BORDER)
        container.grid(row=1, column=0, padx=40, sticky="ew")
        container.grid_columnconfigure(0, weight=1)

        # Inputs Grouped
        input_area = ctk.CTkFrame(container, fg_color="transparent")
        input_area.pack(pady=25, padx=25, fill="x")

        self.folder_entry = ctk.CTkEntry(input_area, placeholder_text="Pasta...", height=35, border_color=COLOR_CARD_BORDER, fg_color=COLOR_INPUT_BG, text_color=COLOR_TEXT_MAIN)
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(input_area, text="Buscar", width=90, height=35, fg_color=COLOR_INPUT_BORDER, text_color=COLOR_TEXT_MAIN, hover_color=COLOR_CARD_BORDER, command=self.browse).pack(side="right")

        pref_area = ctk.CTkFrame(container, fg_color="transparent")
        pref_area.pack(pady=(0, 15), padx=25, fill="x")
        ctk.CTkLabel(pref_area, text="Prefixo:", text_color=COLOR_TEXT_DIM).pack(side="left", padx=(0,10))
        self.base_name = ctk.CTkEntry(pref_area, placeholder_text="Ex: Férias", width=250, height=35, border_color=COLOR_CARD_BORDER, fg_color=COLOR_INPUT_BG, text_color=COLOR_TEXT_MAIN)
        self.base_name.pack(side="left")

        ctk.CTkButton(container, text="RENOMEAR ARQUIVOS", height=40, 
                    fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, 
                    font=ctk.CTkFont(weight="bold"), command=self.run).pack(pady=(10, 25), padx=25, fill="x")

        # Log area compacta
        ctk.CTkLabel(container, text="📝 Status / Log", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_DIM).pack(anchor="w", padx=25, pady=(0,5))
        self.log_box = ctk.CTkTextbox(container, height=100, fg_color=COLOR_INPUT_BG, text_color=COLOR_TEXT_DIM, border_width=1, border_color=COLOR_CARD_BORDER, corner_radius=6)
        self.log_box.pack(pady=(0, 25), padx=25, fill="both")

    def on_show(self): self.load_saved_path()
    def load_saved_path(self):
        saved = self.controller.get_setting("last_renamer_path")
        if saved and os.path.exists(saved):
            self.folder_entry.delete(0, "end"); self.folder_entry.insert(0, saved)

    def browse(self):
        f = filedialog.askdirectory()
        if f: 
            self.folder_entry.delete(0, "end"); self.folder_entry.insert(0, f)
            self.controller.save_setting("last_renamer_path", f)

    def run(self):
        folder = self.folder_entry.get()
        name = self.base_name.get()
        if not folder or not os.path.exists(folder): messagebox.showerror("Erro", "Pasta inválida."); return
        if not name: messagebox.showerror("Erro", "Digite um nome."); return
        threading.Thread(target=self.logic, args=(folder, name)).start()

    def logic(self, folder, base_name):
        self.log_message(f">>> Pasta: {folder}")
        try:
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            files.sort()
            count = 1; renamed = 0
            for f in files:
                if f.startswith(base_name): continue
                _, ext = os.path.splitext(f)
                new_name = f"{base_name}_{count}{ext}"
                try:
                    os.rename(os.path.join(folder, f), os.path.join(folder, new_name))
                    self.log_message(f"✔ {f} -> {new_name}")
                    renamed += 1
                except: pass
                count += 1
            messagebox.showinfo("Sucesso", f"{renamed} arquivos renomeados!")
        except Exception as e: self.log_message(f"Erro: {e}")

    def log_message(self, msg):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")


# === TELA CONVERSOR ===
class ConverterFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self, text="Conversor Multimídia", font=ctk.CTkFont(size=22, weight="bold"), text_color=COLOR_TEXT_MAIN).grid(row=0, column=0, padx=40, pady=(30, 20), sticky="w")
        
        container = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_CARD_BORDER)
        container.grid(row=1, column=0, padx=40, sticky="ew") # Compact
        container.grid_columnconfigure(0, weight=1)
        
        # Seleção
        top_frame = ctk.CTkFrame(container, fg_color="transparent")
        top_frame.pack(pady=25, padx=25, fill="x")
        ctk.CTkButton(top_frame, text="Selecionar Arquivos", width=160, height=35, 
                    fg_color=COLOR_INPUT_BORDER, text_color=COLOR_TEXT_MAIN, hover_color=COLOR_CARD_BORDER, command=self.select_files).pack(side="left", padx=(0,15))
        self.lbl_count = ctk.CTkLabel(top_frame, text="Nenhum selecionado", text_color=COLOR_TEXT_DIM)
        self.lbl_count.pack(side="left")

        # Destino
        dest_frame = ctk.CTkFrame(container, fg_color="transparent")
        dest_frame.pack(pady=(0, 15), padx=25, fill="x")
        self.output_entry = ctk.CTkEntry(dest_frame, placeholder_text="Destino (Vazio = Mesma pasta)", height=35, border_color=COLOR_CARD_BORDER, fg_color=COLOR_INPUT_BG, text_color=COLOR_TEXT_MAIN)
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(dest_frame, text="Destino", width=80, height=35, fg_color=COLOR_INPUT_BORDER, text_color=COLOR_TEXT_MAIN, hover_color=COLOR_CARD_BORDER, command=self.select_output).pack(side="right")

        # Opções
        opt_frame = ctk.CTkFrame(container, fg_color="transparent")
        opt_frame.pack(pady=(0, 15), padx=25, fill="x")
        ctk.CTkLabel(opt_frame, text="Converter para:", text_color=COLOR_TEXT_MAIN).pack(side="left", padx=(0,10))
        self.fmt_var = ctk.StringVar(value="PNG (Img)")
        ctk.CTkComboBox(opt_frame, values=["PNG (Img)", "JPG (Img)", "WEBP (Img)", "PDF (Img)", "MP3 (Áudio)", "MP4 (Vídeo)"], 
                      variable=self.fmt_var, width=150, border_color=COLOR_CARD_BORDER, fg_color=COLOR_INPUT_BG, text_color=COLOR_TEXT_MAIN).pack(side="left")

        ctk.CTkButton(container, text="INICIAR CONVERSÃO", height=40, 
                    fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, 
                    font=ctk.CTkFont(weight="bold"), command=self.run).pack(pady=20, padx=25, fill="x")

        ctk.CTkLabel(container, text="📝 Log de Processamento", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_DIM).pack(anchor="w", padx=25, pady=(0,5))
        self.log_box = ctk.CTkTextbox(container, height=100, fg_color=COLOR_INPUT_BG, text_color=COLOR_TEXT_DIM, border_width=1, border_color=COLOR_CARD_BORDER, corner_radius=6)
        self.log_box.pack(pady=(0, 25), padx=25, fill="both")
        
        self.selected_files = []

    def select_files(self):
        files = filedialog.askopenfilenames()
        if files:
            self.selected_files = files
            self.lbl_count.configure(text=f"{len(files)} arquivos carregados")
            self.log_box.insert("end", f">>> {len(files)} arquivos na fila.\n")

    def select_output(self):
        f = filedialog.askdirectory()
        if f: self.output_entry.delete(0, "end"); self.output_entry.insert(0, f)

    def run(self):
        target = self.fmt_var.get().split(" ")[0].lower()
        if target in ['png','jpg','webp','pdf'] and not HAS_PIL:
            messagebox.showerror("Erro", "Instale Pillow: pip install Pillow")
            return
        if target in ['mp3','mp4'] and not HAS_MOVIEPY:
            messagebox.showerror("Erro", "Instale MoviePy: pip install moviepy")
            return
        if not self.selected_files: return
        threading.Thread(target=self.logic, args=(target,)).start()

    def logic(self, target_fmt):
        out_dir = self.output_entry.get()
        success = 0
        for file in self.selected_files:
            try:
                base_name = os.path.basename(os.path.splitext(file)[0])
                final_folder = out_dir if out_dir and os.path.exists(out_dir) else os.path.dirname(file)
                output_path = os.path.join(final_folder, f"{base_name}.{target_fmt}")

                if target_fmt in ['png', 'jpg', 'jpeg', 'webp', 'pdf']:
                    img = Image.open(file)
                    if target_fmt in ['jpg', 'jpeg', 'pdf'] and img.mode in ('RGBA', 'LA'):
                        bg = Image.new('RGB', img.size, (255, 255, 255)); bg.paste(img, mask=img.split()[3]); img = bg
                    elif target_fmt in ['jpg', 'jpeg', 'pdf'] and img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(output_path)
                elif target_fmt == 'mp3':
                    clip = AudioFileClip(file); clip.write_audiofile(output_path, verbose=False, logger=None); clip.close()
                elif target_fmt == 'mp4':
                    clip = VideoFileClip(file); clip.write_videofile(output_path, codec="libx264", verbose=False, logger=None); clip.close()

                self.log_box.insert("end", f"✔ Salvo: {os.path.basename(output_path)}\n")
                success += 1
            except Exception as e: self.log_box.insert("end", f"❌ Erro {os.path.basename(file)}: {str(e)}\n")
        self.log_box.see("end")
        messagebox.showinfo("Sucesso", f"Concluído! {success} arquivos.")


# === TELA ENERGIA (Layout Otimizado) ===
class EnergyFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.shutdown_job = None; self.target_time = None
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Controle de Energia", font=ctk.CTkFont(size=22, weight="bold"), text_color=COLOR_TEXT_MAIN).grid(row=0, column=0, padx=40, pady=(30, 20), sticky="w")
        
        container = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_CARD_BORDER)
        container.grid(row=1, column=0, padx=40, sticky="ew") # Compact vertical
        container.grid_columnconfigure(0, weight=1)

        # Header simples
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(pady=25)
        ctk.CTkLabel(header, text="⚡ Agendamento", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLOR_TEXT_MAIN).pack()
        
        # Ação (Centralizada)
        self.action_var = ctk.StringVar(value="shutdown")
        action_frame = ctk.CTkFrame(container, fg_color="transparent")
        action_frame.pack(pady=10)
        ctk.CTkRadioButton(action_frame, text="Desligar", variable=self.action_var, value="shutdown", fg_color=COLOR_ACCENT, text_color=COLOR_TEXT_MAIN).pack(side="left", padx=15)
        ctk.CTkRadioButton(action_frame, text="Reiniciar", variable=self.action_var, value="restart", fg_color=COLOR_ACCENT, text_color=COLOR_TEXT_MAIN).pack(side="left", padx=15)

        # Tabs compactas
        self.tabview = ctk.CTkTabview(container, height=180, width=400, fg_color="transparent", segmented_button_selected_color=COLOR_ACCENT, segmented_button_unselected_color=COLOR_INPUT_BORDER, text_color=COLOR_TEXT_MAIN)
        self.tabview.pack(pady=10)
        tab_timer = self.tabview.add("Timer")
        tab_clock = self.tabview.add("Horário")

        # Tab 1
        grid = ctk.CTkFrame(tab_timer, fg_color="transparent")
        grid.pack(pady=15)
        for label, mins in [("30 Min", 30), ("1 Hora", 60), ("2 Horas", 120)]:
            ctk.CTkButton(grid, text=label, width=90, height=32, fg_color=COLOR_INPUT_BORDER, text_color=COLOR_TEXT_MAIN, hover_color=COLOR_CARD_BORDER, command=lambda m=mins: self.schedule_timer(m)).pack(side="left", padx=5)
        
        custom = ctk.CTkFrame(tab_timer, fg_color="transparent")
        custom.pack(pady=5)
        self.entry_mins = ctk.CTkEntry(custom, placeholder_text="Min...", width=80, border_color=COLOR_CARD_BORDER, fg_color=COLOR_INPUT_BG, text_color=COLOR_TEXT_MAIN)
        self.entry_mins.pack(side="left", padx=5)
        ctk.CTkButton(custom, text="Definir", fg_color=COLOR_ACCENT, width=90, command=self.schedule_custom_timer).pack(side="left", padx=5)

        # Tab 2
        clock = ctk.CTkFrame(tab_clock, fg_color="transparent")
        clock.pack(pady=30)
        ctk.CTkLabel(clock, text="Às:", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
        self.entry_time = ctk.CTkEntry(clock, placeholder_text="HH:MM", width=100, font=ctk.CTkFont(size=16), border_color=COLOR_CARD_BORDER, fg_color=COLOR_INPUT_BG, text_color=COLOR_TEXT_MAIN)
        self.entry_time.pack(side="left", padx=5)
        ctk.CTkButton(clock, text="Agendar", fg_color=COLOR_ACCENT, width=100, command=self.schedule_fixed_time).pack(side="left", padx=10)

        # Status
        self.countdown_label = ctk.CTkLabel(container, text="", font=ctk.CTkFont(size=24, weight="bold"), text_color=COLOR_SUCCESS)
        self.countdown_label.pack(pady=10)
        ctk.CTkButton(container, text="CANCELAR", fg_color=COLOR_ERROR, width=200, height=35, hover_color="#B00020", command=self.cancel_action).pack(pady=(0, 30))

    def schedule_custom_timer(self):
        try: self.schedule_timer(int(self.entry_mins.get()))
        except: pass

    def schedule_timer(self, minutes):
        self.cancel_action(silent=True)
        seconds = minutes * 60
        self.target_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        action = self.action_var.get()
        flag = "/s" if action == "shutdown" else "/r"
        cmd = f"shutdown {flag} /t {seconds}" if platform.system() == "Windows" else f"shutdown {'-h' if action=='shutdown' else '-r'} +{minutes}"
        if os.system(cmd) == 0:
            self.update_countdown()
            messagebox.showinfo("Sucesso", f"Agendado para {minutes} minutos.")

    def schedule_fixed_time(self):
        try:
            h, m = map(int, self.entry_time.get().split(':'))
            now = datetime.datetime.now()
            target = now.replace(hour=h, minute=m, second=0)
            if target <= now: target += datetime.timedelta(days=1)
            minutes = int((target - now).total_seconds() / 60)
            if minutes < 1: return
            self.schedule_timer(minutes)
        except: pass

    def update_countdown(self):
        if not self.target_time: return
        rem = self.target_time - datetime.datetime.now()
        if rem.total_seconds() <= 0: self.countdown_label.configure(text="Executando...", text_color=COLOR_ERROR); self.target_time = None; return
        s = int(rem.total_seconds())
        self.countdown_label.configure(text=f"{s//3600:02}:{(s%3600)//60:02}:{s%60:02}")
        self.shutdown_job = self.after(1000, self.update_countdown)

    def cancel_action(self, silent=False):
        if self.shutdown_job: self.after_cancel(self.shutdown_job); self.shutdown_job = None
        self.target_time = None
        self.countdown_label.configure(text="")
        os.system("shutdown /a" if platform.system() == "Windows" else "shutdown -c")
        if not silent: messagebox.showinfo("Cancelado", "Agendamento cancelado.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--boot-organizer": run_headless_organizer()
        elif sys.argv[1] == "--boot-cleaner": run_headless_cleaner()
    else:
        app = AutomationHub()
        app.mainloop()