"""
Script de Consola: Unir Videos
==============================
Une todos los videos de una carpeta en un solo archivo.

Uso:
    python unir_videos.py
    python unir_videos.py "C:\MiCarpeta\Videos"
    python unir_videos.py "C:\MiCarpeta\Videos" "video_final.mp4"
"""

import os
import sys
from pathlib import Path

try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips
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
    print("🎬 Unir Videos")
    print("=" * 60)
    
    # Obtener carpeta
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        print("\n📁 Ingresa la ruta de la carpeta con videos:")
        folder_path = input("   > ").strip().strip('"')
    
    # Obtener nombre de salida
    if len(sys.argv) > 2:
        output_name = sys.argv[2]
    else:
        output_name = None
    
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
    
    if len(videos) < 2:
        print("⚠️ Solo hay 1 video, no hay nada que unir")
        sys.exit(1)
    
    print(f"✅ Encontrados {len(videos)} videos\n")
    
    # Mostrar lista
    print("📹 Videos a unir (en este orden):")
    print("-" * 60)
    for i, video in enumerate(videos, 1):
        print(f"   {i}. {video.name}")
    print("-" * 60)
    
    # Confirmar orden
    print("\n¿El orden es correcto? (s/n)")
    confirm = input("   > ").strip().lower()
    
    if confirm not in ['s', 'si', 'sí', 'y', 'yes', '']:
        print("\n💡 Tip: Renombra los archivos con números al inicio")
        print("   Ejemplo: 01_intro.mp4, 02_contenido.mp4, etc.")
        sys.exit(0)
    
    # Determinar nombre de salida
    if not output_name:
        default_name = f"{folder.name}_completo.mp4"
        print(f"\n📝 Nombre del archivo de salida [{default_name}]:")
        output_name = input("   > ").strip()
        if not output_name:
            output_name = default_name
    
    # Asegurar extensión .mp4
    if not output_name.endswith('.mp4'):
        output_name += '.mp4'
    
    output_path = folder / output_name
    
    # Verificar si existe
    if output_path.exists():
        print(f"\n⚠️ El archivo ya existe: {output_name}")
        print("¿Sobrescribir? (s/n)")
        overwrite = input("   > ").strip().lower()
        if overwrite not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Cancelado")
            sys.exit(0)
    
    # Cargar videos
    print("\n🎬 Cargando videos...")
    clips = []
    total_duration = 0
    
    for i, video in enumerate(videos, 1):
        print(f"   [{i}/{len(videos)}] Cargando {video.name}...", end=" ", flush=True)
        try:
            clip = VideoFileClip(str(video))
            clips.append(clip)
            total_duration += clip.duration
            print(f"✅ {format_duration(clip.duration)}")
        except Exception as e:
            print(f"❌ Error: {e}")
            # Cerrar clips abiertos
            for c in clips:
                c.close()
            sys.exit(1)
    
    print("-" * 60)
    print(f"⏱️  Duración total: {format_duration(total_duration)}")
    
    # Unir videos
    print("\n🔗 Uniendo videos...")
    try:
        final_clip = concatenate_videoclips(clips, method="compose")
        
        print(f"💾 Guardando en: {output_path}")
        print("   (esto puede tomar varios minutos...)\n")
        
        final_clip.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            verbose=False,
            logger=None
        )
        
        final_clip.close()
        
    except Exception as e:
        print(f"❌ Error uniendo videos: {e}")
        sys.exit(1)
    finally:
        # Cerrar todos los clips
        for clip in clips:
            try:
                clip.close()
            except:
                pass
    
    # Verificar resultado
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print("=" * 60)
        print("✅ ¡Videos unidos exitosamente!")
        print(f"📁 Archivo: {output_path}")
        print(f"⏱️  Duración: {format_duration(total_duration)}")
        print(f"💾 Tamaño: {size_mb:.1f} MB")
        print("=" * 60)
    else:
        print("❌ Error: El archivo no se creó correctamente")
    
    input("\nPresiona Enter para salir...")


if __name__ == "__main__":
    main()
