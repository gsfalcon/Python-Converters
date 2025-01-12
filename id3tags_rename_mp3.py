import os
import re
import eyed3
import shutil

def limpar_texto(texto):
    """
    Remove trechos indesejados como '(Official Video)', '[HD]', etc.
    """
    return re.sub(r"[\(\[].*?[\)\]]", "", texto).strip()

def identificar_artista_titulo(nome_arquivo):
    """
    Identifica o artista e o título a partir do nome do arquivo.
    """
    nome_sem_extensao = os.path.splitext(nome_arquivo)[0]
    partes = nome_sem_extensao.split(" - ")

    if len(partes) >= 2:
        # Caso padrão: "Artista - Título"
        artista = limpar_texto(partes[0])
        titulo = limpar_texto(" - ".join(partes[1:]))
    else:
        # Nome incompleto: considera tudo como título
        artista = "Desconhecido"
        titulo = limpar_texto(nome_sem_extensao)
    
    return artista, titulo

def atualizar_tags_e_renomear(caminho_origem, caminho_destino):
    # Verifica se as pastas existem
    if not os.path.isdir(caminho_origem):
        print(f"A pasta de origem '{caminho_origem}' não existe.")
        return

    # Cria a pasta de destino, se não existir
    if not os.path.exists(caminho_destino):
        os.makedirs(caminho_destino)

    # Processa os arquivos MP3
    for arquivo in os.listdir(caminho_origem):
        if arquivo.endswith(".mp3"):
            caminho_arquivo_origem = os.path.join(caminho_origem, arquivo)

            try:
                # Identificar artista e título
                artista, titulo = identificar_artista_titulo(arquivo)

                # Atualizar tags ID3 usando eyed3
                audiofile = eyed3.load(caminho_arquivo_origem)
                if audiofile is None:
                    print(f"Não foi possível processar '{arquivo}'.")
                    continue

                if not audiofile.tag:
                    audiofile.initTag()

                audiofile.tag.artist = artista
                audiofile.tag.title = titulo
                audiofile.tag.save()

                # Definir o novo nome e o caminho na pasta de destino
                novo_nome = f"{artista} - {titulo}.mp3"
                caminho_arquivo_destino = os.path.join(caminho_destino, novo_nome)

                # Evitar conflitos de nomes
                contador = 1
                while os.path.exists(caminho_arquivo_destino):
                    novo_nome = f"{artista} - {titulo} ({contador}).mp3"
                    caminho_arquivo_destino = os.path.join(caminho_destino, novo_nome)
                    contador += 1

                # Copiar o arquivo renomeado para a pasta de destino
                shutil.copy2(caminho_arquivo_origem, caminho_arquivo_destino)
                print(f"Arquivo renomeado e copiado: {arquivo} -> {novo_nome}")

            except Exception as e:
                print(f"Erro ao processar '{arquivo}': {e}")

# Caminho da pasta de origem (com os arquivos originais)
caminho_origem = r"C:\Users\Falcon\Desktop\musicas_baixadas"

# Caminho da pasta de destino (onde os arquivos renomeados serão salvos)
caminho_destino = r"C:\Users\Falcon\Desktop\musicas_id3"

atualizar_tags_e_renomear(caminho_origem, caminho_destino)
