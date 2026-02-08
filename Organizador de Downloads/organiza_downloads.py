import os
import shutil
import time
import sys
import platform
from pathlib import Path

# --- CONFIGURAÇÕES ---
# Detecta a pasta de Downloads automaticamente (Windows e Linux)
PASTA_DOWNLOADS = str(Path.home() / "Downloads")

# Mapeamento de Extensões para Pastas
EXTENSOES = {
    "Imagens": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"],
    "Musicas": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".wma"],
    "Documentos": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx", ".csv"],
    "Compactados": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Executaveis": [".exe", ".msi", ".bat", ".sh", ".deb", ".AppImage", ".apk"],
    "ISOs": [".iso", ".img"],
    "Codigos": [".py", ".js", ".html", ".css", ".cpp", ".java", ".json", ".sql"],
    "Torrents": [".torrent"]
}

# Extensões temporárias de navegadores (NÃO MEXER NESTES ARQUIVOS)
EXTENSOES_TEMP = [".crdownload", ".part", ".tmp", ".download"]

def arquivo_esta_pronto(caminho_arquivo):
    """
    Verifica se o arquivo terminou de ser baixado.
    Lógica:
    1. Não pode ter extensão temporária.
    2. O tamanho do arquivo deve permanecer estável por X segundos.
    """
    nome_arquivo = os.path.basename(caminho_arquivo)
    
    # 1. Checa se é arquivo temporário de navegador
    for ext in EXTENSOES_TEMP:
        if nome_arquivo.endswith(ext):
            return False

    # 2. Checa estabilidade do tamanho (O "Delayzein")
    try:
        tamanho_inicial = os.path.getsize(caminho_arquivo)
        if tamanho_inicial == 0:
            return False # Arquivo acabou de ser criado (0 bytes)
            
        time.sleep(2) # Espera 2 segundos
        
        tamanho_final = os.path.getsize(caminho_arquivo)
        
        # Se o tamanho mudou, ainda está baixando
        if tamanho_inicial != tamanho_final:
            return False
            
        return True
    except OSError:
        return False # Arquivo pode estar bloqueado ou sumiu

def configurar_inicializacao():
    """
    4. Mágica: Configura o script para iniciar junto com o sistema (Windows/Linux)
    """
    sistema = platform.system()
    caminho_script = os.path.abspath(__file__)
    
    if sistema == "Windows":
        pasta_inicializar = os.path.join(os.getenv('APPDATA'), r"Microsoft\Windows\Start Menu\Programs\Startup")
        arquivo_bat = os.path.join(pasta_inicializar, "OrganizadorDownloads.bat")
        
        if os.path.exists(arquivo_bat):
            return # Já está configurado

        resposta = input("Deseja que este organizador inicie junto com o Windows? (S/N): ").strip().upper()
        if resposta == 'S':
            try:
                # Cria um arquivo .bat que chama o python para rodar este script
                with open(arquivo_bat, "w") as bat:
                    bat.write(f'@echo off\npython "{caminho_script}"')
                print(f"✅ Configurado para iniciar com o Windows!")
            except Exception as e:
                print(f"❌ Erro ao configurar inicialização: {e}")

    elif sistema == "Linux":
        pasta_autostart = os.path.expanduser("~/.config/autostart")
        arquivo_desktop = os.path.join(pasta_autostart, "organizador_downloads.desktop")
        
        if os.path.exists(arquivo_desktop):
            return # Já está configurado

        resposta = input("Deseja que este organizador inicie junto com o Linux? (S/N): ").strip().upper()
        if resposta == 'S':
            try:
                if not os.path.exists(pasta_autostart):
                    os.makedirs(pasta_autostart)
                
                conteudo_desktop = f"""[Desktop Entry]
Type=Application
Name=Organizador de Downloads
Exec=python3 "{caminho_script}"
X-GNOME-Autostart-enabled=true
"""
                with open(arquivo_desktop, "w") as f:
                    f.write(conteudo_desktop)
                print(f"✅ Configurado para iniciar com o Linux!")
            except Exception as e:
                print(f"❌ Erro ao configurar inicialização: {e}")

def organizar():
    print(f"--- Iniciando Organizador de Downloads ---")
    print(f"Pasta alvo: {PASTA_DOWNLOADS}")
    
    # Tenta configurar inicialização automática na primeira execução
    configurar_inicializacao()
    
    print("\nO script está rodando em segundo plano...")
    print("Pressione Ctrl+C para parar.\n")

    while True: # Loop infinito para ficar vigiando a pasta
        try:
            arquivos = [f for f in os.listdir(PASTA_DOWNLOADS) if os.path.isfile(os.path.join(PASTA_DOWNLOADS, f))]

            for arquivo in arquivos:
                caminho_origem = os.path.join(PASTA_DOWNLOADS, arquivo)
                nome, extensao = os.path.splitext(arquivo)
                extensao = extensao.lower()

                # Pula o próprio script se ele estiver na pasta Downloads
                if "organizador_downloads" in nome:
                    continue

                # Verifica se o arquivo está pronto para ser movido
                if not arquivo_esta_pronto(caminho_origem):
                    continue

                moved = False
                for pasta, exts in EXTENSOES.items():
                    if extensao in exts:
                        pasta_destino = os.path.join(PASTA_DOWNLOADS, pasta)
                        
                        # Cria a pasta se não existir
                        if not os.path.exists(pasta_destino):
                            os.makedirs(pasta_destino)
                            print(f"📁 Pasta criada: {pasta}")

                        caminho_destino = os.path.join(pasta_destino, arquivo)

                        # Evita sobrescrever arquivos com mesmo nome (adiciona numero)
                        contador = 1
                        while os.path.exists(caminho_destino):
                            novo_nome = f"{nome}_{contador}{extensao}"
                            caminho_destino = os.path.join(pasta_destino, novo_nome)
                            contador += 1

                        try:
                            shutil.move(caminho_origem, caminho_destino)
                            print(f"✅ Movido: {arquivo} -> {pasta}")
                            moved = True
                        except Exception as e:
                            print(f"❌ Erro ao mover {arquivo}: {e}")
                        
                        break # Sai do loop de extensões se já moveu
                
                # Se não se encaixou em nenhuma categoria, vai para "Outros"
                if not moved and arquivo_esta_pronto(caminho_origem):
                    pasta_destino = os.path.join(PASTA_DOWNLOADS, "Outros")
                    if not os.path.exists(pasta_destino):
                        os.makedirs(pasta_destino)
                    
                    caminho_destino = os.path.join(pasta_destino, arquivo)
                    try:
                        shutil.move(caminho_origem, caminho_destino)
                        print(f"📦 Movido para Outros: {arquivo}")
                    except:
                        pass
        except Exception as e:
            print(f"Erro no loop principal: {e}")

        # Espera um pouco antes de verificar a pasta novamente para não fritar a CPU
        time.sleep(5) 

if __name__ == "__main__":
    try:
        organizar()
    except KeyboardInterrupt:
        print("\n🛑 Organizador finalizado pelo usuário.")
