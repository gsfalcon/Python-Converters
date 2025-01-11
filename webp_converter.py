from PIL import Image
import os

# Caminho da pasta com as imagens .webp
pasta = 'D:/xxx/Sissy'

# Cria uma pasta para salvar as imagens convertidas
pasta_convertida = os.path.join(pasta, 'convertidas')
os.makedirs(pasta_convertida, exist_ok=True)

# Loop pelas imagens e converte cada uma
for arquivo in os.listdir(pasta):
    if arquivo.endswith('.webp'):
        caminho_imagem = os.path.join(pasta, arquivo)
        with Image.open(caminho_imagem) as img:
            # Define o novo formato (jpeg ou png)
            formato_destino = 'jpeg'  # ou 'png'
            novo_nome = f"{os.path.splitext(arquivo)[0]}.{formato_destino}"
            caminho_convertido = os.path.join(pasta_convertida, novo_nome)
            img.convert("RGB").save(caminho_convertido, formato_destino.upper())
print("Conversão concluída!")
