#!/usr/bin/env python3
"""
Script para descargar todos los recursos externos del proyecto Django
y configurarlos para uso local sin internet.
"""

import os
import requests
import urllib.parse
from pathlib import Path

def create_directories():
    """Crear directorios necesarios para los archivos estáticos"""
    directories = [
        'cafeteria/static/css',
        'cafeteria/static/js',
        'cafeteria/static/fonts',
        'cafeteria/static/img',
        'cafeteria/static/webfonts'  # Agregada para Font Awesome
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directorio creado: {directory}")

def download_file(url, local_path):
    """Descargar un archivo desde una URL"""
    try:
        print(f"📥 Descargando: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Guardado en: {local_path}")
        return True
    except Exception as e:
        print(f"❌ Error descargando {url}: {e}")
        return False

def main():
    """Función principal para descargar todos los recursos"""
    
    # Crear directorios
    create_directories()
    
    # URLs de los recursos a descargar
    resources = {
        # Bootstrap CSS
        'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css': 'cafeteria/static/css/bootstrap.min.css',
        
        # Bootstrap JS
        'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js': 'cafeteria/static/js/bootstrap.bundle.min.js',
        
        # Bootstrap Icons CSS
        'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css': 'cafeteria/static/css/bootstrap-icons.css',
        
        # Font Awesome CSS
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css': 'cafeteria/static/css/fontawesome.min.css',
        
        # Toastr CSS
        'https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/toastr.min.css': 'cafeteria/static/css/toastr.min.css',
        
        # jQuery
        'https://code.jquery.com/jquery-3.6.0.min.js': 'cafeteria/static/js/jquery.min.js',
        
        # Toastr JS
        'https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/toastr.min.js': 'cafeteria/static/js/toastr.min.js',
        
        # Font Awesome Fonts
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.woff2': 'cafeteria/static/webfonts/fa-solid-900.woff2',
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.woff': 'cafeteria/static/webfonts/fa-solid-900.woff',
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-regular-400.woff2': 'cafeteria/static/webfonts/fa-regular-400.woff2',
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-regular-400.woff': 'cafeteria/static/webfonts/fa-regular-400.woff',
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-brands-400.woff2': 'cafeteria/static/webfonts/fa-brands-400.woff2',
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-brands-400.woff': 'cafeteria/static/webfonts/fa-brands-400.woff',
        
        # Bootstrap Icons Fonts
        'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/fonts/bootstrap-icons.woff2': 'cafeteria/static/fonts/bootstrap-icons.woff2',
        'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/fonts/bootstrap-icons.woff': 'cafeteria/static/fonts/bootstrap-icons.woff',
    }
    
    print("🚀 Iniciando descarga de recursos...")
    
    success_count = 0
    total_count = len(resources)
    
    for url, local_path in resources.items():
        if download_file(url, local_path):
            success_count += 1
    
    print(f"\n📊 Resumen:")
    print(f"✅ Archivos descargados exitosamente: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 ¡Todos los recursos descargados correctamente!")
        print("\n📝 Próximos pasos:")
        print("1. Actualiza el CSS de Font Awesome para usar rutas locales")
        print("2. Reemplaza tu base.html con la versión local")
        print("3. Ejecuta: python manage.py collectstatic")
        print("4. Reinicia tu servidor Django")
    else:
        print("⚠️ Algunos archivos no se descargaron. Revisa los errores arriba.")

if __name__ == "__main__":
    main()