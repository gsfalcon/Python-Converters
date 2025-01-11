import os
from tqdm import tqdm
from PIL import Image
from mutagen import File
from mutagen.mp4 import MP4
import ffmpeg  # Certifique-se de que FFmpeg esteja instalado e no PATH

def limpar_exif_imagem(caminho):
    """Remove informações EXIF de uma imagem."""
    try:
        with Image.open(caminho) as img:
            data = list(img.getdata())
            img_no_exif = Image.new(img.mode, img.size)
            img_no_exif.putdata(data)
            img_no_exif.save(caminho)
        return True
    except Exception as e:
        print(f"\033[91mErro ao limpar EXIF de {caminho}: {e}\033[0m")
        return False

def limpar_exif_video(caminho):
    """Remove informações EXIF de um vídeo."""
    try:
        # Usando ffmpeg para remover metadados
        output_path = f"{os.path.splitext(caminho)[0]}_no_metadata.mp4"
        ffmpeg.input(caminho).output(output_path, map_metadata=-1).run(overwrite_output=True)
        os.replace(output_path, caminho)
        return True
    except Exception as e:
        print(f"\033[91mErro ao limpar EXIF de {caminho}: {e}\033[0m")
        return False

def processar_pasta(pasta):
    """Processa todos os arquivos de imagem e vídeo em uma pasta e subpastas."""
    for root, _, files in os.walk(pasta):
        for file in tqdm(files, desc="Processando arquivos", unit="file"):
            caminho = os.path.join(root, file)

            # Limpar EXIF para imagens
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                if limpar_exif_imagem(caminho):
                    print(f"\033[92mEXIF limpo: {caminho}\033[0m")

            # Limpar EXIF para vídeos
            elif file.lower().endswith(('.mp4', '.webm')):
                if limpar_exif_video(caminho):
                    print(f"\033[92mMetadados limpos: {caminho}\033[0m")

if __name__ == "__main__":
    pasta = input("Digite o caminho da pasta que deseja processar: ")
    if os.path.isdir(pasta):
        print("\033[94mIniciando a limpeza de EXIF e metadados...\033[0m")
        processar_pasta(pasta)
        print("\033[92mProcessamento concluído!\033[0m")
    else:
        print("\033[91mErro: O caminho fornecido não é uma pasta válida.\033[0m")
