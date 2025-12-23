#!/usr/bin/env python3
"""
Script de conversão em lote de vídeos para MP4 (H.264 + AAC)
Com upscale para 720p mínimo, efeito blur nas bordas e legendas embutidas
Compatível com Plex Media Server
"""

import os
import subprocess
import json
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import argparse
import sys

# Formatos de vídeo suportados para conversão
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', 
                   '.webm', '.m4v', '.mpg', '.mpeg', '.3gp', '.ts', 
                   '.m2ts', '.vob', '.ogv'}

# Cores ANSI para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ProgressTracker:
    def __init__(self, total):
        self.total = total
        self.current = 0
        self.success = 0
        self.errors = 0
        self.skipped = 0
        self.current_file = ""
        self.start_time = time.time()
        self.lock = threading.Lock()
        
    def update(self, current_file=""):
        with self.lock:
            if current_file:
                self.current_file = current_file
            self.current += 1
    
    def add_success(self):
        with self.lock:
            self.success += 1
    
    def add_error(self):
        with self.lock:
            self.errors += 1
    
    def add_skipped(self):
        with self.lock:
            self.skipped += 1
    
    def get_eta(self):
        with self.lock:
            if self.current == 0:
                return "Calculando..."
            elapsed = time.time() - self.start_time
            avg_time = elapsed / self.current
            remaining = (self.total - self.current) * avg_time
            return str(timedelta(seconds=int(remaining)))
    
    def display(self):
        with self.lock:
            # Limpa linha
            sys.stdout.write('\r' + ' ' * 150 + '\r')
            
            # Calcula percentual
            percent = (self.current / self.total * 100) if self.total > 0 else 0
            
            # Barra de progresso
            bar_length = 40
            filled = int(bar_length * self.current / self.total) if self.total > 0 else 0
            bar = '█' * filled + '░' * (bar_length - filled)
            
            # Monta mensagem
            status = f"{Colors.CYAN}[{bar}]{Colors.ENDC} "
            status += f"{Colors.BOLD}{percent:.1f}%{Colors.ENDC} "
            status += f"({self.current}/{self.total}) "
            status += f"| {Colors.GREEN}✓ {self.success}{Colors.ENDC} "
            status += f"| {Colors.RED}✗ {self.errors}{Colors.ENDC} "
            status += f"| {Colors.YELLOW}⊘ {self.skipped}{Colors.ENDC} "
            status += f"| ETA: {Colors.BLUE}{self.get_eta()}{Colors.ENDC}"
            
            sys.stdout.write(status)
            sys.stdout.flush()
            
            # Arquivo atual (em nova linha se necessário)
            if self.current_file:
                file_display = self.current_file[:80] + "..." if len(self.current_file) > 80 else self.current_file
                sys.stdout.write(f"\n{Colors.YELLOW}Processando: {file_display}{Colors.ENDC}")
                sys.stdout.flush()

class VideoConverter:
    def __init__(self, source_dir, output_dir=None, threads=2, delete_original=False, 
                 target_bitrate=None, dry_run=False, min_height=720):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir) if output_dir else self.source_dir
        self.threads = threads
        self.delete_original = delete_original
        self.target_bitrate = target_bitrate
        self.dry_run = dry_run
        self.min_height = min_height
        self.log_file = self.output_dir / f'conversion_log_{datetime.now():%Y%m%d_%H%M%S}.txt'
        self.progress = None
        
    def log(self, message, print_to_console=True):
        """Registra mensagens no arquivo de log"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        if print_to_console:
            # Limpa linha de progresso temporariamente
            if self.progress:
                sys.stdout.write('\r' + ' ' * 150 + '\r')
            print(log_msg)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_msg + '\n')
    
    def check_ffmpeg(self):
        """Verifica se FFmpeg está instalado"""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE, 
                         check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"{Colors.RED}ERRO: FFmpeg não encontrado. Instale com:{Colors.ENDC}")
            print("  Ubuntu/Debian: sudo apt install ffmpeg")
            print("  Windows: Baixe de https://ffmpeg.org/download.html")
            print("  macOS: brew install ffmpeg")
            return False
    
    def get_video_info(self, video_path):
        """Obtém informações do vídeo usando ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format', '-show_streams',
                str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except Exception as e:
            self.log(f"Erro ao obter info de {video_path.name}: {e}", False)
            return None
    
    def find_subtitle(self, video_path):
        """Encontra arquivo de legenda .srt correspondente"""
        srt_path = video_path.with_suffix('.srt')
        if srt_path.exists():
            return srt_path
        
        # Procura por legenda com mesmo nome na mesma pasta
        base_name = video_path.stem
        for srt_file in video_path.parent.glob(f"{base_name}*.srt"):
            return srt_file
        
        return None
    
    def calculate_bitrate(self, info, target_width, target_height):
        """Calcula bitrate apropriado baseado na resolução alvo"""
        if self.target_bitrate:
            return self.target_bitrate
        
        # Bitrates recomendados por resolução (qualidade alta)
        if target_height <= 480:
            return '2M'
        elif target_height <= 720:
            return '5M'
        elif target_height <= 1080:
            return '8M'
        elif target_height <= 1440:
            return '16M'
        else:  # 4K+
            return '35M'
    
    def build_filter_complex(self, width, height, target_width, target_height, has_subtitle, subtitle_path):
        """Constrói filtro complexo do FFmpeg com efeito blur e proporção 16:9"""
        filters = []
        
        # Calcula aspect ratio atual e alvo
        current_aspect = width / height
        target_aspect = 16 / 9  # Força 16:9
        
        # SEMPRE aplica efeito blur para manter 16:9
        # 1. Cria background desfocado esticado em 16:9
        # 2. Escala vídeo original mantendo proporção (fit dentro do 16:9)
        # 3. Sobrepõe vídeo centralizado
        
        # Calcula dimensões do vídeo central para caber em 16:9
        if current_aspect > target_aspect:
            # Vídeo mais largo que 16:9 - ajusta pela largura
            new_width = target_width
            new_height = int(target_width / current_aspect)
        else:
            # Vídeo mais alto que 16:9 - ajusta pela altura
            new_height = target_height
            new_width = int(target_height * current_aspect)
        
        # Garante dimensões pares
        new_width = new_width if new_width % 2 == 0 else new_width - 1
        new_height = new_height if new_height % 2 == 0 else new_height - 1
        
        # Offset para centralizar
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        
        # Filtro complexo com efeito blur
        filters.append(
            f"[0:v]split=2[bg][fg];"
            f"[bg]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,crop={target_width}:{target_height},boxblur=20:5[bg_blur];"
            f"[fg]scale={new_width}:{new_height}[fg_scaled];"
            f"[bg_blur][fg_scaled]overlay={x_offset}:{y_offset}[v]"
        )
        video_label = "[v]"
        
        # Adiciona legenda se existir
        if has_subtitle and subtitle_path:
            # Escapa caracteres especiais no caminho
            subtitle_escaped = str(subtitle_path).replace('\\', '/').replace(':', '\\:').replace("'", "\\'")
            filters.append(f"{video_label}subtitles='{subtitle_escaped}'[vout]")
            video_label = "[vout]"
        
        if filters:
            return ";".join(filters), video_label
        return None, "[0:v]"
    
    def convert_video(self, input_path):
        """Converte um vídeo individual"""
        try:
            # Atualiza progresso IMEDIATAMENTE
            if self.progress:
                self.progress.update(str(input_path.relative_to(self.source_dir)))
                self.progress.display()
            
            # Log imediato
            relative_path = input_path.relative_to(self.source_dir)
            print(f"\n{Colors.CYAN}► Processando: {relative_path}{Colors.ENDC}")
            
            # Define caminho de saída
            output_path = self.output_dir / relative_path.parent / f"{input_path.stem}.mp4"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Verifica se já existe
            if output_path.exists() and output_path != input_path:
                print(f"{Colors.YELLOW}  ⊘ Já existe, pulando...{Colors.ENDC}")
                self.log(f"SKIP: {relative_path} (já existe conversão)", False)
                if self.progress:
                    self.progress.add_skipped()
                return {'status': 'skipped', 'path': str(input_path)}
            
            if self.dry_run:
                print(f"{Colors.BLUE}  ℹ DRY-RUN: Simulação apenas{Colors.ENDC}")
                self.log(f"DRY-RUN: Converteria {relative_path}", False)
                if self.progress:
                    self.progress.add_success()
                return {'status': 'dry_run', 'path': str(input_path)}
            
            # Obtém informações do vídeo
            print(f"{Colors.BLUE}  → Analisando vídeo...{Colors.ENDC}")
            info = self.get_video_info(input_path)
            if not info:
                raise Exception("Não foi possível obter informações do vídeo")
            
            video_stream = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)
            if not video_stream:
                raise Exception("Nenhum stream de vídeo encontrado")
            
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            
            print(f"{Colors.BLUE}  → Resolução original: {width}x{height}{Colors.ENDC}")
            
            # Calcula resolução alvo em 16:9
            # Sempre usa proporção 16:9 independente do original
            if height < self.min_height:
                target_height = self.min_height
            else:
                target_height = height
            
            # Força proporção 16:9
            target_width = int(target_height * 16 / 9)
            
            # Garante que seja par (requisito do H.264)
            target_width = target_width if target_width % 2 == 0 else target_width + 1
            target_height = target_height if target_height % 2 == 0 else target_height + 1
            
            bitrate = self.calculate_bitrate(info, target_width, target_height)
            
            # Procura legenda
            subtitle_path = self.find_subtitle(input_path)
            has_subtitle = subtitle_path is not None
            
            print(f"{Colors.GREEN}  → Convertendo para: {target_width}x{target_height} (16:9){Colors.ENDC}")
            print(f"{Colors.GREEN}  → Bitrate: {bitrate}{Colors.ENDC}")
            if has_subtitle:
                print(f"{Colors.GREEN}  → Legenda encontrada: {subtitle_path.name}{Colors.ENDC}")
            
            self.log(f"CONVERTENDO: {relative_path}", False)
            self.log(f"  Resolução: {width}x{height} ({width/height:.2f}:1) → {target_width}x{target_height} (16:9)", False)
            self.log(f"  Bitrate: {bitrate}", False)
            if has_subtitle:
                self.log(f"  Legenda: {subtitle_path.name}", False)
            
            # Arquivo temporário para conversão
            temp_output = output_path.parent / f"temp_{output_path.name}"
            
            # Constrói filtro complexo
            print(f"{Colors.BLUE}  → Preparando filtros de vídeo...{Colors.ENDC}")
            filter_complex, video_map = self.build_filter_complex(
                width, height, target_width, target_height, 
                has_subtitle, subtitle_path
            )
            
            # Comando FFmpeg
            cmd = [
                'ffmpeg', '-i', str(input_path),
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-profile:v', 'high',
                '-level:v', '4.0',
                '-b:v', bitrate,
                '-maxrate', bitrate,
                '-bufsize', f'{int(bitrate[:-1])*2}M',
            ]
            
            # Adiciona filtro se necessário
            if filter_complex:
                cmd.extend(['-filter_complex', filter_complex])
                cmd.extend(['-map', video_map.strip('[]')])
            else:
                cmd.extend(['-map', '0:v:0'])
            
            # Configurações de áudio
            cmd.extend([
                '-c:a', 'aac',
                '-b:a', '192k',
                '-ac', '2',
                '-map', '0:a:0?',
            ])
            
            # Legendas embutidas (se não foi processada no filtro)
            if not has_subtitle:
                cmd.extend(['-map', '0:s?', '-c:s', 'mov_text'])
            
            # Otimizações
            cmd.extend([
                '-movflags', '+faststart',
                '-progress', 'pipe:1',  # Mostra progresso
                '-y',
                str(temp_output)
            ])
            
            # Executa conversão COM FEEDBACK
            print(f"{Colors.YELLOW}  ⚙ Convertendo... (isso pode demorar){Colors.ENDC}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            # Lê progresso do FFmpeg
            last_time = 0
            for line in process.stdout:
                if 'out_time_ms=' in line:
                    try:
                        time_ms = int(line.split('=')[1]) / 1000000
                        if time_ms > last_time + 5:  # Atualiza a cada 5 segundos
                            last_time = time_ms
                            mins = int(time_ms / 60)
                            secs = int(time_ms % 60)
                            print(f"\r{Colors.CYAN}  ⏱ Tempo processado: {mins:02d}:{secs:02d}{Colors.ENDC}", end='')
                    except:
                        pass
            
            process.wait()
            print()  # Nova linha após progresso
            
            if process.returncode == 0:
                # Move arquivo temporário para destino final
                if temp_output.exists():
                    if output_path.exists():
                        output_path.unlink()
                    temp_output.rename(output_path)
                    
                    print(f"{Colors.GREEN}  ✓ SUCESSO: Conversão concluída!{Colors.ENDC}")
                    self.log(f"✓ SUCESSO: {relative_path}", False)
                    if self.progress:
                        self.progress.add_success()
                    
                    # Deleta original se configurado
                    if self.delete_original and input_path != output_path:
                        input_path.unlink()
                        if subtitle_path and subtitle_path.exists():
                            subtitle_path.unlink()
                        self.log(f"  Removido original: {input_path.name}", False)
                    
                    return {'status': 'success', 'path': str(input_path)}
                else:
                    raise Exception("Arquivo de saída não foi criado")
            else:
                stderr_output = process.stderr.read()
                raise Exception(f"FFmpeg erro: {stderr_output[-500:]}")
                
        except Exception as e:
            print(f"{Colors.RED}  ✗ ERRO: {str(e)}{Colors.ENDC}")
            self.log(f"✗ ERRO: {input_path.name} - {str(e)}", False)
            if self.progress:
                self.progress.add_error()
            # Remove arquivo temporário se existir
            if 'temp_output' in locals() and temp_output.exists():
                temp_output.unlink()
            return {'status': 'error', 'path': str(input_path), 'error': str(e)}
    
    def find_videos(self):
        """Encontra todos os vídeos na pasta e subpastas"""
        videos = []
        for ext in VIDEO_EXTENSIONS:
            videos.extend(self.source_dir.rglob(f'*{ext}'))
        return sorted(videos)
    
    def run(self):
        """Executa o processo de conversão"""
        if not self.check_ffmpeg():
            return
        
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}CONVERSÃO EM LOTE DE VÍDEOS{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"Pasta origem: {Colors.YELLOW}{self.source_dir}{Colors.ENDC}")
        print(f"Pasta destino: {Colors.YELLOW}{self.output_dir}{Colors.ENDC}")
        print(f"Threads: {Colors.GREEN}{self.threads}{Colors.ENDC}")
        print(f"Resolução mínima: {Colors.GREEN}{self.min_height}p{Colors.ENDC}")
        print(f"Deletar originais: {Colors.RED if self.delete_original else Colors.GREEN}{self.delete_original}{Colors.ENDC}")
        print(f"Modo dry-run: {Colors.YELLOW if self.dry_run else Colors.GREEN}{self.dry_run}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
        
        # Encontra vídeos
        print(f"{Colors.CYAN}Buscando vídeos...{Colors.ENDC}")
        videos = self.find_videos()
        print(f"{Colors.GREEN}Encontrados {len(videos)} arquivos de vídeo{Colors.ENDC}\n")
        
        if not videos:
            print(f"{Colors.RED}Nenhum vídeo encontrado!{Colors.ENDC}")
            return
        
        if self.dry_run:
            print(f"{Colors.YELLOW}MODO DRY-RUN: Nenhuma conversão será realizada{Colors.ENDC}\n")
        
        # Inicializa rastreador de progresso
        self.progress = ProgressTracker(len(videos))
        
        # Processa vídeos em paralelo
        results = {'success': 0, 'error': 0, 'skipped': 0, 'no_conversion_needed': 0}
        
        print(f"{Colors.CYAN}Iniciando conversão...{Colors.ENDC}\n")
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {executor.submit(self.convert_video, video): video 
                      for video in videos}
            
            for future in as_completed(futures):
                result = future.result()
                results[result['status']] += 1
                if self.progress:
                    self.progress.display()
        
        # Limpa linha de progresso
        print("\n" * 3)
        
        # Resumo final
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}CONVERSÃO CONCLUÍDA{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"Total processado: {Colors.BOLD}{len(videos)}{Colors.ENDC}")
        print(f"  {Colors.GREEN}✓ Sucesso: {results['success']}{Colors.ENDC}")
        print(f"  {Colors.CYAN}✓ Já no formato: {results.get('no_conversion_needed', 0)}{Colors.ENDC}")
        print(f"  {Colors.YELLOW}⊘ Pulados: {results['skipped']}{Colors.ENDC}")
        print(f"  {Colors.RED}✗ Erros: {results['error']}{Colors.ENDC}")
        print(f"\n{Colors.BLUE}Log salvo em: {self.log_file}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")


def main():
    parser = argparse.ArgumentParser(
        description='Converte vídeos em lote para MP4 (H.264 + AAC) com upscale e legendas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python converter.py /caminho/pasta/videos
  python converter.py /origem -o /destino -t 4
  python converter.py /videos --delete-original --bitrate 10M
  python converter.py /videos --min-height 1080
  python converter.py /videos --dry-run
        """
    )
    
    parser.add_argument('source', nargs='?', help='Pasta com os vídeos para converter')
    parser.add_argument('-o', '--output', help='Pasta de destino (padrão: mesma da origem)')
    parser.add_argument('-t', '--threads', type=int, default=2,
                       help='Número de conversões simultâneas (padrão: 2)')
    parser.add_argument('--min-height', type=int, default=720,
                       help='Altura mínima em pixels (padrão: 720)')
    parser.add_argument('--delete-original', action='store_true',
                       help='Deleta arquivos originais após conversão bem-sucedida')
    parser.add_argument('--bitrate', help='Bitrate alvo (ex: 8M, 12M). Se não especificado, calcula automaticamente')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simula a conversão sem processar arquivos')
    
    args = parser.parse_args()
    
    # Se não passou o source, pede interativamente
    source_path = args.source
    if not source_path:
        print(f"{Colors.CYAN}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}CONVERSOR DE VÍDEOS EM LOTE{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*80}{Colors.ENDC}\n")
        source_path = input(f"{Colors.YELLOW}Digite o caminho da pasta com os vídeos: {Colors.ENDC}").strip().strip('"').strip("'")
        
        if not source_path:
            print(f"{Colors.RED}Nenhum caminho fornecido. Encerrando.{Colors.ENDC}")
            return
    
    # Valida pasta de origem
    if not os.path.isdir(source_path):
        print(f"{Colors.RED}ERRO: Pasta não encontrada: {source_path}{Colors.ENDC}")
        return
    
    # Cria conversor
    converter = VideoConverter(
        source_dir=source_path,
        output_dir=args.output,
        threads=args.threads,
        delete_original=args.delete_original,
        target_bitrate=args.bitrate,
        dry_run=args.dry_run,
        min_height=args.min_height
    )
    
    # Executa conversão
    converter.run()


if __name__ == '__main__':
    main()