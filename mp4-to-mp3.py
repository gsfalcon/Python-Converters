import os
import yt_dlp
from rich.console import Console

def download_audio(url):
    console = Console()
    output_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(output_dir, exist_ok=True)
    
    options = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }]
    }
    
    console.print("[bold cyan]Iniciando o download do áudio...[/bold cyan]")
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])
    
    console.print("[bold green]Download concluído![/bold green]")
    show_saved_files(output_dir, console)

def show_saved_files(output_dir, console):
    files = [f for f in os.listdir(output_dir) if f.endswith('.mp3')]
    console.print("\n[bold blue]Arquivos salvos:[/bold blue]")
    for file in files:
        console.print(f"[green]{os.path.join(output_dir, file)}[/green]")

if __name__ == "__main__":
    console = Console()
    console.print("[bold yellow]Cole o link do vídeo do YouTube e pressione Enter:[/bold yellow]")
    url = input().strip()
    if url:
        download_audio(url)
    else:
        console.print("[bold red]Nenhum link fornecido![/bold red]")