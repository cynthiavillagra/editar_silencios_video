"""
Script de Consola: Calculador de Duración de Videos
====================================================
Calcula la duración total de todos los videos en una carpeta.

Uso:
    python duracion_videos.py
    python duracion_videos.py "C:\MiCarpeta\Videos"
"""

import os
import sys
from pathlib import Path

try:
    from moviepy.editor import VideoFileClip
except ImportError:
    print("❌ Error: moviepy no está instalado")
    print("   Ejecuta: pip install moviepy")
    sys.exit(1)

# Extensiones de video soportadas
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.wmv', '.flv', '.m4v'}


def format_duration(seconds):
    """Formatea segundos a HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def get_video_duration(filepath):
    """Obtiene la duración de un video en segundos."""
    try:
        with VideoFileClip(str(filepath)) as clip:
            return clip.duration
    except Exception as e:
        print(f"  ⚠️ Error leyendo {filepath.name}: {e}")
        return 0


def find_videos(folder_path):
    """Encuentra todos los videos en una carpeta."""
    folder = Path(folder_path)
    videos = []
    
    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in VIDEO_EXTENSIONS:
            videos.append(file)
    
    return sorted(videos, key=lambda x: x.name.lower())


def main():
    print("=" * 60)
    print("🎬 Calculador de Duración de Videos")
    print("=" * 60)
    
    # Obtener carpeta
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        print("\n📁 Ingresa la ruta de la carpeta con videos:")
        folder_path = input("   > ").strip().strip('"')
    
    # Validar carpeta
    if not folder_path:
        print("❌ No se especificó carpeta")
        sys.exit(1)
    
    folder = Path(folder_path)
    if not folder.exists():
        print(f"❌ La carpeta no existe: {folder_path}")
        sys.exit(1)
    
    if not folder.is_dir():
        print(f"❌ No es una carpeta: {folder_path}")
        sys.exit(1)
    
    # Buscar videos
    print(f"\n🔍 Buscando videos en: {folder}")
    videos = find_videos(folder)
    
    if not videos:
        print("❌ No se encontraron videos en la carpeta")
        print(f"   Formatos soportados: {', '.join(VIDEO_EXTENSIONS)}")
        sys.exit(1)
    
    print(f"✅ Encontrados {len(videos)} videos\n")
    
    # Calcular duraciones
    print("📊 Analizando duración de cada video...")
    print("-" * 60)
    
    total_seconds = 0
    video_data = []
    
    for i, video in enumerate(videos, 1):
        print(f"   [{i}/{len(videos)}] {video.name}...", end=" ", flush=True)
        duration = get_video_duration(video)
        total_seconds += duration
        video_data.append((video.name, duration))
        print(f"✅ {format_duration(duration)}")
    
    # Mostrar resumen
    print("-" * 60)
    print("\n📋 RESUMEN")
    print("=" * 60)
    
    # Lista de videos
    print("\n📹 Videos encontrados:\n")
    for name, duration in video_data:
        duration_str = format_duration(duration)
        # Truncar nombre si es muy largo
        display_name = name[:45] + "..." if len(name) > 48 else name
        print(f"   {display_name:<50} {duration_str:>10}")
    
    print("-" * 60)
    
    # Totales
    total_minutes = total_seconds / 60
    total_hours = total_seconds / 3600
    
    print(f"\n🎯 TOTAL: {len(videos)} videos")
    print(f"⏱️  Duración total: {format_duration(total_seconds)}")
    print(f"   ({total_minutes:.1f} minutos / {total_hours:.2f} horas)")
    
    # Promedio
    avg_duration = total_seconds / len(videos) if videos else 0
    print(f"📊 Duración promedio: {format_duration(avg_duration)}")
    
    print("\n" + "=" * 60)
    input("\nPresiona Enter para salir...")


if __name__ == "__main__":
    main()
