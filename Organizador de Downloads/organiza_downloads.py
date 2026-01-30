import os
import shutil
import time
import ctypes
import sys
from pathlib import Path
from datetime import datetime

# --- CONFIGURAÇÃO DE AUTO-INICIALIZAÇÃO ---
def adicionar_ao_startup():
    """
    Pergunta ao usuário se quer instalar no Startup do Windows.
    Se Sim -> Copia este arquivo para a pasta de Inicialização como .pyw (silencioso).
    """
    nome_no_startup = "organizador_downloads.pyw"
    
    # Caminho da pasta Inicializar do Windows
    pasta_startup = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
    caminho_destino = os.path.join(pasta_startup, nome_no_startup)
    caminho_atual = os.path.abspath(__file__)

    # 1. Verifica se já está rodando da pasta certa
    if caminho_atual.lower() == caminho_destino.lower():
        return 

    # 2. Verifica se já está instalado
    if os.path.exists(caminho_destino):
        return 

    # 3. Pergunta (Pop-up)
    titulo = "Instalação Automática - Organizador"
    mensagem = ("Deseja que o Organizador de Downloads inicie junto com o Windows?\n\n"
                "Ele rodará em segundo plano organizando seus arquivos automaticamente.")
    
    # 4 = Yes/No, 0x40 = Ícone de Informação, 0x1000 = System Modal (Fica por cima)
    resposta = ctypes.windll.user32.MessageBoxW(0, mensagem, titulo, 4 | 0x40 | 0x1000)
    
    if resposta == 6: # 6 = Yes
        try:
            shutil.copy2(caminho_atual, caminho_destino)
            ctypes.windll.user32.MessageBoxW(0, 
                "Instalado com sucesso!\n\nO organizador agora rodará automaticamente ao ligar o PC.", 
                "Sucesso", 0x40)
        except Exception as e:
            ctypes.windll.user32.MessageBoxW(0, f"Erro ao instalar: {e}", "Erro", 0x10)

class OrganizadorDownloads:
    """
    Script de automação para organizar a pasta de Downloads.
    Versão 2.1: Com Auto-Start inteligente.
    """

    def __init__(self):
        self.download_path = Path.home() / "Downloads"
        self.arquivo_log = self.download_path / "log_organizacao.txt"
        
        self.diretorios = {
            'Imagens': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff', '.ico'],
            'Videos': ['.mp4', '.mkv', '.flv', '.avi', '.mov', '.wmv'],
            'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg'],
            'Documentos': ['.pdf', '.doc', '.docx', '.txt', '.xlsx', '.pptx', '.csv', '.odt'],
            'Instaladores': ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.iso'],
            'Compactados': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'Scripts_Codigos': ['.py', '.js', '.html', '.css', '.cpp', '.java', '.json', '.sql'],
            'Design_3D': ['.psd', '.ai', '.blend', '.obj', '.fbx']
        }
        
        self.ignorar = ['.tmp', '.crdownload', '.ini', 'log_organizacao.txt', os.path.basename(__file__)]

    def registrar_log(self, mensagem):
        """Escreve as ações num arquivo de texto para auditoria."""
        try:
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            # Abre em modo 'append' e garante que fecha o arquivo
            with open(self.arquivo_log, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {mensagem}\n")
        except Exception:
            pass # Se falhar o log, não para o programa

    def obter_pasta_destino(self, arquivo):
        """Define a pasta baseada na extensão e cria subpasta de Data (Ano-Mês)."""
        ext = arquivo.suffix.lower()
        pasta_categoria = 'Outros'
        
        for pasta, extensoes in self.diretorios.items():
            if ext in extensoes:
                pasta_categoria = pasta
                break
        
        # Pega a data de modificação para criar subpasta (Ex: 2024-01)
        try:
            timestamp_arquivo = arquivo.stat().st_mtime
            data_arquivo = datetime.fromtimestamp(timestamp_arquivo)
            subpasta_data = data_arquivo.strftime("%Y-%m")
        except:
            subpasta_data = "Indefinido"
        
        return self.download_path / pasta_categoria / subpasta_data

    def mover_arquivo(self, arquivo, destino_pasta):
        if not destino_pasta.exists():
            try:
                destino_pasta.mkdir(parents=True)
            except: return False, None

        destino_final = destino_pasta / arquivo.name
        contador = 1
        
        # Evita sobrescrever arquivos com mesmo nome
        while destino_final.exists():
            destino_final = destino_pasta / f"{arquivo.stem}_{contador}{arquivo.suffix}"
            contador += 1

        try:
            # Tenta mover. Se estiver em uso, vai falhar e cair no except
            shutil.move(str(arquivo), str(destino_final))
            self.registrar_log(f"MOVIDO: '{arquivo.name}' -> '{destino_pasta.relative_to(self.download_path)}'")
            return True, destino_final.name
        except Exception:
            # Arquivo provavelmente em uso (downloading), ignora silenciosamente
            return False, None

    def limpar_pastas_vazias(self):
        """Remove pastas vazias para manter a higiene."""
        for categoria in self.diretorios.keys():
            pasta_cat = self.download_path / categoria
            if pasta_cat.exists():
                for subpasta in pasta_cat.iterdir():
                    try:
                        if subpasta.is_dir() and not any(subpasta.iterdir()):
                            subpasta.rmdir()
                    except: pass

    def organizar(self):
        if not self.download_path.exists(): return

        # Itera sobre arquivos na raiz
        for item in self.download_path.iterdir():
            if not item.is_file(): continue
            if item.name.startswith('.') or item.name in self.ignorar or item.suffix in self.ignorar: continue
            
            # Verifica se é o próprio script (para não se mover se estiver na pasta downloads)
            if item.name == os.path.basename(__file__) or item.name == "organizador_downloads.pyw":
                continue

            pasta_destino = self.obter_pasta_destino(item)
            sucesso, _ = self.mover_arquivo(item, pasta_destino)
            if sucesso:
                self.limpar_pastas_vazias()

    def monitorar(self):
        """Loop infinito de monitoramento."""
        print(f"--- MONITORAMENTO ATIVO: {self.download_path} ---")
        self.registrar_log("--- INÍCIO DO MONITORAMENTO ---")
        
        try:
            while True:
                self.organizar()
                time.sleep(5) # Verifica a cada 5 segundos
        except KeyboardInterrupt:
            self.registrar_log("--- FIM DO MONITORAMENTO ---")

if __name__ == "__main__":
    # 1. Tenta instalar no startup
    adicionar_ao_startup()
    
    # 2. Inicia o programa
    app = OrganizadorDownloads()
    app.monitorar()