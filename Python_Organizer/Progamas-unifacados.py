import os
import shutil
import threading
import time
import platform
import tempfile
import json
import sys
import ctypes
from datetime import datetime
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox

# --- CONFIGURAÇÃO VISUAL ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# --- ARQUIVO DE CONFIGURAÇÃO ---
CONFIG_FILE = "pyorg_config.json"

# --- CONFIGURAÇÃO DE EXTENSÕES ---
ORGANIZACAO = {
    "Imagens": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff", ".raw"],
    "Documentos": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".csv", ".pptx", ".odt", ".rtf", ".gdoc"],
    "Compactados": [".zip", ".rar", ".7z", ".tar", ".gz", ".iso"],
    "Executaveis": [".exe", ".msi", ".bat", ".sh", ".cmd", ".app", ".jar"],
    "Codigos": [".py", ".js", ".html", ".css", ".cpp", ".java", ".json", ".sql", ".php", ".ts", ".rs", ".go"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv"],
    "Musicas": [".mp3", ".wav", ".flac", ".ogg", ".wma", ".aac"]
}

# --- FUNÇÕES DE ADMINISTRADOR ---
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    # Reinicia o script com privilégios elevados
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

class ConfigManager:
    @staticmethod
    def load():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except:
                pass
        return {"theme": "Dark", "startup_active": False, "cleaner_startup": False}

    @staticmethod
    def save(data):
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)

    @staticmethod
    def set_startup(enable, script_name="PyOrganizerAuto.bat"):
        startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        bat_path = os.path.join(startup_folder, script_name)
        
        if enable:
            script_path = os.path.abspath(__file__)
            python_exe = sys.executable
            python_exe_w = python_exe.replace("python.exe", "pythonw.exe")
            content = f'@echo off\nstart "" "{python_exe_w}" "{script_path}"'
            
            try:
                with open(bat_path, "w") as f:
                    f.write(content)
                return True
            except Exception as e:
                print(f"Erro ao criar startup: {e}")
                return False
        else:
            if os.path.exists(bat_path):
                try:
                    os.remove(bat_path)
                except:
                    pass
            return False

class PyOrganizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.config = ConfigManager.load()
        ctk.set_appearance_mode(self.config.get("theme", "Dark"))

        self.title("PYTHON ORGANIZER - AUTOMATION HUB")
        self.geometry("1100x750")
        self.minsize(950, 650)
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_frame = None
        self.criar_sidebar()
        
        self.frame_home = HomeView(self, self.show_organizer, self.show_downloads, self.show_cleaner)
        self.frame_organizer = OrganizerView(self)
        self.frame_cleaner = CleanerSystemView(self)

        self.show_frame("home")

    def criar_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0, 
                                        fg_color=("#F8F9FA", "#141414")) 
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        self.sidebar_frame.grid_rowconfigure(0, weight=0)
        self.sidebar_frame.grid_rowconfigure(1, weight=0)
        self.sidebar_frame.grid_rowconfigure(2, weight=0)
        self.sidebar_frame.grid_rowconfigure(3, weight=0)
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.sidebar_frame.grid_rowconfigure(5, weight=0)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="PYTHON\nORGANIZER", 
                                     font=ctk.CTkFont(family="Roboto", size=24, weight="bold"), 
                                     text_color=("#1F2937", "#ffffff"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(40, 30))

        self.btn_home = self.criar_botao_sidebar("🏠  INÍCIO", lambda: self.show_frame("home"), 1)
        self.btn_org = self.criar_botao_sidebar("📂  ORGANIZADOR", lambda: self.show_frame("organizer"), 2)
        self.btn_clean = self.criar_botao_sidebar("🧹  LIMPEZA", lambda: self.show_frame("cleaner"), 3)

        self.theme_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.theme_frame.grid(row=5, column=0, padx=20, pady=20, sticky="ew")
        
        self.appearance_mode_menu = ctk.CTkOptionMenu(self.theme_frame, values=["Dark", "Light"],
                                                    command=self.change_appearance_mode_event, 
                                                    fg_color=("#E5E7EB", "#202020"), 
                                                    button_color=("#D1D5DB", "#333333"), 
                                                    button_hover_color=("#9CA3AF", "#444444"),
                                                    text_color=("#111827", "white"))
        self.appearance_mode_menu.set(self.config.get("theme", "Dark"))
        self.appearance_mode_menu.pack(fill="x")

    def criar_botao_sidebar(self, text, command, row):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, anchor="w", command=command,
                            fg_color="transparent", text_color=("#111827", "gray85"), 
                            hover_color=("#E5E7EB", "#202020"), height=45, 
                            font=ctk.CTkFont(size=13, weight="bold"))
        btn.grid(row=row, column=0, padx=15, pady=2, sticky="ew")
        return btn

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        self.config["theme"] = new_appearance_mode
        ConfigManager.save(self.config)

    def show_frame(self, name):
        if self.current_frame:
            self.current_frame.grid_forget()

        if name == "home":
            self.current_frame = self.frame_home
        elif name == "organizer":
            self.frame_organizer.reset_mode("Manual")
            self.current_frame = self.frame_organizer
        elif name == "downloads":
            self.frame_organizer.set_downloads_mode()
            self.current_frame = self.frame_organizer
        elif name == "cleaner":
            self.current_frame = self.frame_cleaner
        
        self.current_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

    def show_organizer(self): self.show_frame("organizer")
    def show_downloads(self): self.show_frame("downloads")
    def show_cleaner(self): self.show_frame("cleaner")


class HomeView(ctk.CTkFrame):
    def __init__(self, master, cmd_org, cmd_down, cmd_clean):
        super().__init__(master, fg_color=("#FFFFFF", "#0F0F0F"))
        
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(expand=True, fill="both", padx=60, pady=60)

        self.lbl_title = ctk.CTkLabel(self.container, text="Bem-vindo ao Python Organizer", 
                                    font=("Roboto", 32, "bold"), text_color=("#111827", "white"))
        self.lbl_title.pack(anchor="w", pady=(0, 5))
        
        self.lbl_sub = ctk.CTkLabel(self.container, text="Selecione uma ferramenta de automação para começar:", 
                                  font=("Roboto", 14), text_color="gray")
        self.lbl_sub.pack(anchor="w", pady=(0, 40))

        self.grid_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.grid_frame.pack(fill="x")
        self.grid_frame.grid_columnconfigure((0,1,2), weight=1, uniform="a")

        self.create_card(self.grid_frame, "📁 Downloads", "Organize Downloads com subpastas por data e relatório.", 
                         "#3b82f6", cmd_down, 0, 0)
        
        self.create_card(self.grid_frame, "☁️ Organizador", "Escolha qualquer pasta para arrumar.", 
                         "#8b5cf6", cmd_org, 0, 1)
        
        self.create_card(self.grid_frame, "🧹 Limpeza", "Limpe cache, navegadores e sistema.", 
                         "#ef4444", cmd_clean, 0, 2)

    def create_card(self, parent, title, desc, color, cmd, r, c):
        card = ctk.CTkFrame(parent, corner_radius=20, fg_color=("#F3F4F6", "#18181b"), 
                          border_width=1, border_color=("#E5E7EB", "#262626"))
        card.grid(row=r, column=c, padx=15, pady=10, sticky="nsew")
        
        ctk.CTkLabel(card, text=title, font=("Roboto", 20, "bold")).pack(padx=25, pady=(35, 10), anchor="w")
        
        desc_label = ctk.CTkLabel(card, text=desc, font=("Roboto", 13), text_color="gray", 
                                wraplength=200, justify="left")
        desc_label.pack(padx=25, pady=(0, 25), anchor="w")
        
        ctk.CTkButton(card, text="ABRIR FERRAMENTA", command=cmd, fg_color=color, hover_color=color, 
                      corner_radius=10, height=45, font=("Roboto", 12, "bold")).pack(padx=25, pady=(0, 35), fill="x")


class OrganizerView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=("#FFFFFF", "#0F0F0F"))
        self.caminho_selecionado = ctk.StringVar()
        self.is_download_mode = False
        
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(expand=True, fill="both", padx=60, pady=40)

        self.header_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 20))
        
        self.header = ctk.CTkLabel(self.header_frame, text="Organizador de Arquivos", font=("Roboto", 24, "bold"))
        self.header.pack(side="left")

        self.startup_var = ctk.BooleanVar(value=ConfigManager.load().get("startup_active", False))
        self.switch_startup = ctk.CTkSwitch(self.header_frame, text="Iniciar com o Windows", 
                                          command=self.toggle_startup, variable=self.startup_var,
                                          progress_color="#00e676", font=("Roboto", 12, "bold"))

        self.card = ctk.CTkFrame(self.container, corner_radius=15, fg_color=("#F3F4F6", "#18181b"))
        self.card.pack(fill="x", pady=20)

        self.entry = ctk.CTkEntry(self.card, textvariable=self.caminho_selecionado, 
                                placeholder_text="Selecione o diretório...", height=55,
                                font=("Roboto", 14), border_width=0, fg_color=("#FFFFFF", "#27272a"))
        self.entry.pack(side="left", fill="x", expand=True, padx=20, pady=20)
        
        self.btn_browse = ctk.CTkButton(self.card, text="📁 PROCURAR", width=120, height=55, 
                                      command=self.selecionar_pasta, fg_color="#3b82f6", corner_radius=10)
        self.btn_browse.pack(side="right", padx=(0, 20))

        self.btn_run = ctk.CTkButton(self.container, text="EXECUTAR ORGANIZAÇÃO", height=60, command=self.iniciar,
                                     fg_color="#00e676", hover_color="#00c853", text_color="white", 
                                     font=("Roboto", 16, "bold"), corner_radius=12, state="disabled")
        self.btn_run.pack(fill="x", pady=10)

        self.log_frame = ctk.CTkFrame(self.container, corner_radius=15, fg_color=("#F3F4F6", "#18181b"))
        self.log_frame.pack(fill="both", expand=True, pady=20)
        
        ctk.CTkLabel(self.log_frame, text="LOG DE ATIVIDADE", font=("Roboto", 11, "bold"), 
                   text_color="gray").pack(anchor="w", padx=20, pady=(15,5))

        self.log_box = ctk.CTkTextbox(self.log_frame, font=("Consolas", 12), fg_color="transparent")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log("Sistema pronto. Selecione uma pasta.")

    def log(self, msg):
        self.log_box.insert("end", f"> {msg}\n")
        self.log_box.see("end")

    def toggle_startup(self):
        active = self.startup_var.get()
        success = ConfigManager.set_startup(active, "PyOrganizer_Downloads.bat")
        cfg = ConfigManager.load()
        cfg["startup_active"] = active
        ConfigManager.save(cfg)
        
        if success and active:
            messagebox.showinfo("Sucesso", "O Organizador iniciará com o Windows!")
        elif not success and active:
            self.startup_var.set(False)
            messagebox.showerror("Erro", "Não foi possível criar o atalho.")

    def reset_mode(self, mode_name):
        self.header.configure(text=f"Organizador - Modo Manual")
        self.caminho_selecionado.set("")
        self.btn_browse.configure(state="normal")
        self.btn_browse.pack(side="right", padx=(0, 20))
        self.switch_startup.pack_forget()
        self.log_box.delete("1.0", "end")
        self.log("Modo Manual: Escolha uma pasta.")
        self.is_download_mode = False

    def set_downloads_mode(self):
        self.header.configure(text="Organizador de Downloads")
        path = os.path.join(os.path.expanduser("~"), "Downloads")
        
        self.caminho_selecionado.set(path)
        self.btn_browse.pack_forget()
        self.btn_run.configure(state="normal")
        self.switch_startup.pack(side="right")
        
        self.log_box.delete("1.0", "end")
        self.log(f"Pasta Downloads detectada: {path}")
        self.log("INFO: Arquivos serão organizados em subpastas por data.")
        self.log("INFO: Um relatório de auditoria será gerado ao final.")
        self.is_download_mode = True
        
        if self.startup_var.get():
            self.log("AVISO: Inicialização automática ativa.")

    def selecionar_pasta(self):
        p = filedialog.askdirectory()
        if p:
            self.caminho_selecionado.set(p)
            self.btn_run.configure(state="normal")

    def iniciar(self):
        threading.Thread(target=self.run_logic).start()

    def run_logic(self):
        path = Path(self.caminho_selecionado.get())
        if not path.exists(): return
        
        self.btn_run.configure(state="disabled", text="ORGANIZANDO...", fg_color="#10b981")
        arquivos = [f for f in path.iterdir() if f.is_file()]
        
        movidos = 0
        log_auditoria = []
        data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        log_auditoria.append(f"RELATÓRIO DE ORGANIZAÇÃO")
        log_auditoria.append(f"Data da execução: {data_hoje}")
        log_auditoria.append(f"Diretório Alvo: {path}")
        log_auditoria.append("-" * 50)

        for f in arquivos:
            ext = f.suffix.lower()
            if ext == ".ini" or f.name.startswith("Relatorio_Org"): continue
            
            dest_folder = "Outros"
            for cat, exts in ORGANIZACAO.items():
                if ext in exts: dest_folder = cat; break
            
            timestamp = f.stat().st_mtime
            data_mod = datetime.fromtimestamp(timestamp)
            pasta_data = data_mod.strftime("%Y-%m-%d")
            
            target_folder = path / dest_folder / pasta_data

            target_folder.mkdir(parents=True, exist_ok=True)
            
            try:
                destino_final = target_folder / f.name
                shutil.move(str(f), str(destino_final))
                
                msg = f"[SUCESSO] {f.name} -> {dest_folder}/{pasta_data}"
                self.log(msg)
                log_auditoria.append(msg)
                movidos += 1
            except Exception as e:
                err_msg = f"[ERRO] {f.name}: {e}"
                self.log(err_msg)
                log_auditoria.append(err_msg)
            time.sleep(0.02)
        
        if movidos > 0:
            nome_log = f"Relatorio_Organizacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            caminho_log = path / nome_log
            try:
                with open(caminho_log, "w", encoding="utf-8") as f_log:
                    f_log.write("\n".join(log_auditoria))
                self.log(f"Relatório salvo em: {nome_log}")
            except Exception as e:
                self.log(f"Erro ao salvar relatório: {e}")

        self.btn_run.configure(state="normal", text="EXECUTAR ORGANIZAÇÃO", fg_color="#00e676")
        self.log("-" * 30)
        self.log(f"Concluído. {movidos} arquivos organizados.")


class CleanerSystemView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=("#FFFFFF", "#0F0F0F"))
        
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(expand=True, fill="both", padx=60, pady=40)
        
        self.header_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 20))

        self.header = ctk.CTkLabel(self.header_frame, text="Limpeza de Sistema", font=("Roboto", 24, "bold"))
        self.header.pack(side="left")

        # Switch de Startup para Limpeza
        self.startup_var = ctk.BooleanVar(value=ConfigManager.load().get("cleaner_startup", False))
        self.switch_startup = ctk.CTkSwitch(self.header_frame, text="Iniciar com o Windows", 
                                          command=self.toggle_startup, variable=self.startup_var,
                                          progress_color="#ef4444", font=("Roboto", 12, "bold"))
        self.switch_startup.pack(side="right")

        info_card = ctk.CTkFrame(self.container, fg_color=("#FEF2F2", "#2e1010"), 
                               border_color="#ef4444", border_width=1)
        info_card.pack(fill="x", pady=(0, 20))
        
        # Texto atualizado para incluir navegadores
        warning_text = ("ATENÇÃO: Limpa arquivos temporários do Usuário e do Sistema.\n"
                        "Também limpa Cache de Navegadores (Chrome/Edge).\n"
                        "Certifique-se de salvar seus trabalhos.")
        
        ctk.CTkLabel(info_card, text=warning_text, 
                     text_color=("#DC2626", "#ef4444"), justify="left", font=("Roboto", 13)).pack(padx=20, pady=20)

        self.btn_clean = ctk.CTkButton(self.container, text="ESCANEAR E LIMPAR LIXO", height=60, command=self.iniciar_limpeza,
                                     fg_color="#ef4444", hover_color="#dc2626", text_color="white",
                                     font=("Roboto", 16, "bold"), corner_radius=12)
        self.btn_clean.pack(fill="x", pady=10)

        self.log_frame = ctk.CTkFrame(self.container, corner_radius=15, fg_color=("#F3F4F6", "#18181b"))
        self.log_frame.pack(fill="both", expand=True, pady=20)
        
        self.log_box = ctk.CTkTextbox(self.log_frame, font=("Consolas", 12), fg_color="transparent")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)
        self.log("Sistema pronto. Aguardando comando...")

    def log(self, msg):
        self.log_box.insert("end", f"> {msg}\n")
        self.log_box.see("end")
    
    def toggle_startup(self):
        active = self.startup_var.get()
        success = ConfigManager.set_startup(active, "PyOrganizer_Cleaner.bat")
        cfg = ConfigManager.load()
        cfg["cleaner_startup"] = active
        ConfigManager.save(cfg)
        
        if success and active:
            messagebox.showinfo("Sucesso", "O Limpador iniciará com o Windows!")
        elif not success and active:
            self.startup_var.set(False)
            messagebox.showerror("Erro", "Não foi possível criar o atalho.")

    def iniciar_limpeza(self):
        # Verifica Admin
        admin = is_admin()
        
        if not admin:
            # Pergunta se quer elevar
            res = messagebox.askyesno("Permissão Necessária", 
                                    "Deseja realizar uma Limpeza Profunda?\n"
                                    "(Inclui: Caches de Navegadores, Windows Temp, Prefetch)\n\n"
                                    "Isso reiniciará o aplicativo como Administrador.\n"
                                    "Clique em 'Não' para manter apenas a limpeza básica (%TEMP%).")
            if res:
                run_as_admin()
                sys.exit() # Fecha para reabrir como admin
                return
            else:
                self.log("Iniciando modo Básico (%TEMP%)...")
        else:
            self.log("Modo Administrador detectado. Limpeza Profunda ativada.")

        threading.Thread(target=self.run_cleaner).start()

    def run_cleaner(self):
        self.btn_clean.configure(state="disabled", text="LIMPANDO...")
        
        # Lista de pastas para limpar
        paths_to_clean = []
        
        # 1. Básico (Usuário Temp)
        temp_user = tempfile.gettempdir()
        paths_to_clean.append(("TEMP Usuário", temp_user))
        
        # 2. Avançado (Se for Admin)
        if is_admin():
            # Windows Temp
            sys_temp = os.path.join(os.environ['SystemRoot'], 'Temp')
            paths_to_clean.append(("TEMP Sistema", sys_temp))
            
            # Prefetch
            prefetch = os.path.join(os.environ['SystemRoot'], 'Prefetch')
            paths_to_clean.append(("Prefetch", prefetch))
            
            # Navegadores
            local_app_data = os.getenv('LOCALAPPDATA')
            if local_app_data:
                # Chrome Cache
                chrome_cache = os.path.join(local_app_data, 'Google', 'Chrome', 'User Data', 'Default', 'Cache')
                if os.path.exists(chrome_cache):
                    paths_to_clean.append(("Chrome Cache", chrome_cache))
                
                # Edge Cache
                edge_cache = os.path.join(local_app_data, 'Microsoft', 'Edge', 'User Data', 'Default', 'Cache')
                if os.path.exists(edge_cache):
                    paths_to_clean.append(("Edge Cache", edge_cache))

        deleted_count = 0
        bytes_saved = 0
        
        for nome_tipo, pasta in paths_to_clean:
            self.log(f"Varrendo: {nome_tipo}...")
            if not os.path.exists(pasta): continue

            try:
                items = os.listdir(pasta)
                for item in items:
                    path = os.path.join(pasta, item)
                    try:
                        if os.path.isfile(path):
                            size = os.path.getsize(path)
                            os.remove(path)
                            bytes_saved += size
                            deleted_count += 1
                        elif os.path.isdir(path):
                            shutil.rmtree(path)
                            deleted_count += 1
                    except Exception:
                        pass # Arquivo em uso
                    time.sleep(0.001) # Pequeno delay para não travar UI
            except Exception as e:
                self.log(f"Erro ao acessar {nome_tipo}: {e}")

        mb_saved = round(bytes_saved / (1024 * 1024), 2)
        self.log("-" * 30)
        self.log(f"LIMPEZA CONCLUÍDA.")
        self.log(f"Itens Removidos: {deleted_count}")
        self.log(f"Espaço Recuperado: {mb_saved} MB")
        self.btn_clean.configure(state="normal", text="ESCANEAR E LIMPAR LIXO")


if __name__ == "__main__":
    app = PyOrganizerApp()
    app.mainloop()
