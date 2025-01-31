import os
import yt_dlp

# Nome do arquivo contendo as músicas
arquivo_txt = "D:\GitHub\Python Converters\lista_de_musicas.txt"
# Pasta onde os arquivos MP3 serão salvos
pasta_destino = "C:\\Users\\Falcon\\Desktop\\musicas_baixadas"

# Criar a pasta de destino, se não existir
os.makedirs(pasta_destino, exist_ok=True)

# Configuração do yt-dlp 
ydl_opts = {
    "format": "bestaudio/best",
    "extractaudio": True,
    "audioformat": "mp3",
    "outtmpl": os.path.join(pasta_destino, "%(title)s.%(ext)s"),
    "postprocessors": [
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
    ],
    "quiet": False,  # Mostrar o progresso no terminal
}

# Ler o arquivo de músicas e baixar cada uma
with open(arquivo_txt, "r", encoding="utf-8") as file:
    for linha in file:
        musica = linha.strip()
        if musica:
            print(f"Baixando: {musica}")
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Pesquisar a música no YouTube e baixar o primeiro resultado
                    ydl.download([f"ytsearch1:{musica}"])
            except Exception as e:
                print(f"Erro ao baixar {musica}: {e}")

print(f"Músicas salvas na pasta '{pasta_destino}'!")
