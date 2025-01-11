from moviepy.editor import VideoFileClip
import os

# Caminho da pasta com os vídeos .webm
pasta = 'D:/xxx/Sissy/videos'

# Cria uma pasta para salvar os vídeos convertidos
pasta_convertida = os.path.join(pasta, 'convertidos_mp4')
os.makedirs(pasta_convertida, exist_ok=True)

# Loop pelos arquivos e converte cada vídeo
for arquivo in os.listdir(pasta):
    if arquivo.endswith('.webm'):
        caminho_video = os.path.join(pasta, arquivo)
        novo_nome = f"{os.path.splitext(arquivo)[0]}.mp4"
        caminho_convertido = os.path.join(pasta_convertida, novo_nome)

        # Abre e converte o vídeo
        with VideoFileClip(caminho_video) as video:
            video.write_videofile(caminho_convertido, codec="libx264")

print("Conversão concluída!")
