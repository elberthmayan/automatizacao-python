import os
import shutil
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp

# --- CONFIGURAÇÕES DE CREDENCIAIS ---

# 1. Acede a https://developer.spotify.com/dashboard
# 2. Cria um "App" ou seleciona um existente.
# 3. Copia o 'Client ID' e cola-o abaixo.
SPOTIPY_CLIENT_ID = 'O_TEU_CLIENT_ID_AQUI'

# 4. Clica em 'View client secret' no Dashboard do Spotify e cola-o abaixo.
# NUNCA partilhes este código com ninguém!
SPOTIPY_CLIENT_SECRET = 'O_TEU_CLIENT_SECRET_AQUI'

# 5. Copia o link da tua playlist no Spotify (Partilhar -> Copiar link da playlist)
PLAYLIST_URL = 'LINK_DA_TUA_PLAYLIST_AQUI'

# --- CONFIGURAÇÕES DE SAÍDA ---

# Nome da pasta onde as músicas serão guardadas temporariamente
OUTPUT_FOLDER = 'minhas_musicas'

# Nome do ficheiro final compactado (será gerado um .zip)
FINAL_ZIP_NAME = 'playlist_downloaded'

# Se definires como True, o script apaga a pasta 'minhas_musicas' após criar o ZIP.
# Se definires como False, ficas com o ZIP e com os ficheiros MP3 soltos.
APAGAR_PASTA_TEMPORARIA = True

def get_playlist_tracks(playlist_url):
    """
    Usa a API do Spotify para obter nomes das músicas e artistas da playlist.
    """
    try:
        auth_manager = SpotifyClientCredentials(
            client_id=SPOTIPY_CLIENT_ID, 
            client_secret=SPOTIPY_CLIENT_SECRET
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        results = sp.playlist_items(playlist_url)
        tracks = results['items']
        
        # Lida com a paginação caso a playlist tenha mais de 100 músicas
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])
            
        track_list = []
        for item in tracks:
            track = item['track']
            if track:
                # Formata a string de busca: "Nome da Música - Artista"
                track_name = f"{track['name']} - {track['artists'][0]['name']}"
                track_list.append(track_name)
                
        return track_list
    except Exception as e:
        print(f"[ERRO] Falha ao aceder à API do Spotify: {e}")
        return []

def download_as_mp3(track_names, output_dir):
    """
    Procura as músicas no YouTube e descarrega-as em formato MP3.
    Requer o FFmpeg instalado ou na pasta do script.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Configurações do yt-dlp para extração de áudio de alta qualidade
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'quiet': False,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for track in track_names:
            print(f"\n[A DESCARREGAR] {track}")
            try:
                # Procura no YouTube e descarrega o primeiro resultado encontrado
                ydl.download([f"ytsearch1:{track} audio"])
            except Exception as e:
                print(f"[ERRO] Falha ao descarregar {track}: {e}")

def main():
    print("=== Spotify para MP3 - Descarregador Automático ===")
    
    # Verificação básica de segurança
    if 'AQUI' in SPOTIPY_CLIENT_ID or 'AQUI' in PLAYLIST_URL:
        print("\n[AVISO] Precisas de preencher as tuas credenciais e o link da playlist no código!")
        return

    # Passo 1: Obter a lista de músicas do Spotify
    print("\n[PASSO 1] A ler músicas da playlist...")
    tracks = get_playlist_tracks(PLAYLIST_URL)
    
    if not tracks:
        print("[ERRO] Nenhuma música encontrada. Verifica se a playlist é pública ou se as chaves estão corretas.")
        return
        
    print(f"Total encontrado: {len(tracks)} músicas.")

    # Passo 2: Descarregar do YouTube
    print("\n[PASSO 2] A iniciar os downloads (isto pode demorar dependendo da internet)...")
    download_as_mp3(tracks, OUTPUT_FOLDER)

    # Passo 3: Criar o ficheiro ZIP
    print(f"\n[PASSO 3] A criar o ficheiro compactado: {FINAL_ZIP_NAME}.zip")
    try:
        shutil.make_archive(FINAL_ZIP_NAME, 'zip', OUTPUT_FOLDER)
        caminho_completo = os.path.abspath(f"{FINAL_ZIP_NAME}.zip")
        print(f"[SUCESSO] Ficheiro gerado em: {caminho_completo}")
    except Exception as e:
        print(f"[ERRO] Falha ao compactar ficheiros: {e}")

    # Passo 4: Limpeza (opcional)
    if APAGAR_PASTA_TEMPORARIA:
        print("\n[PASSO 4] A remover a pasta temporária de músicas...")
        if os.path.exists(OUTPUT_FOLDER):
            shutil.rmtree(OUTPUT_FOLDER)
    else:
        caminho_pasta = os.path.abspath(OUTPUT_FOLDER)
        print(f"\n[INFO] As músicas individuais foram mantidas em: {caminho_pasta}")

    print("\nPROCESSO CONCLUÍDO! Podes fechar o terminal.")

if __name__ == "__main__":
    main()