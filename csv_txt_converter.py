import os
import csv

# Pasta onde estão os arquivos CSV
pasta_csv = r"C:\Users\Falcon\Desktop\spotify_playlists"
# Nome do arquivo de saída
arquivo_saida = "lista_de_musicas.txt"

# Conjunto para armazenar combinações únicas de "Artista - Título"
musicas = set()

# Percorrer todos os arquivos na pasta
for nome_arquivo in os.listdir(pasta_csv):
    if nome_arquivo.endswith(".csv"):  # Processar apenas arquivos CSV
        caminho_arquivo = os.path.join(pasta_csv, nome_arquivo)
        with open(caminho_arquivo, encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Extrair artista e título
                artista = row.get("Artist Name(s)") or row.get("Artist")
                titulo = row.get("Track Name") or row.get("Title")
                if artista and titulo:
                    # Adicionar a música ao conjunto para remover duplicatas
                    musicas.add(f"{artista} - {titulo}")

# Ordenar as músicas alfabeticamente e salvar no arquivo de saída
with open(arquivo_saida, "w", encoding="utf-8") as txtfile:
    for musica in sorted(musicas):  # A função `sorted` organiza os itens em ordem alfabética
        txtfile.write(f"{musica}\n")

print(f"Lista gerada com sucesso e organizada alfabeticamente em '{arquivo_saida}'!")
