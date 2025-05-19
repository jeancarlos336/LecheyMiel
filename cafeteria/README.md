# LecheyMiel

Sistema de Punto de Venta (POS) desarrollado con **Python**, **Django** y **PostgreSQL**.

Ideal para cafeterías, Restaurantes que necesiten una gestión eficiente de pedidos, productos, ventas y reportes.

---

## 🚀 Tecnologías utilizadas

- Django (backend y panel administrativo)
- PostgreSQL (base de datos)
- Bootstrap 5 (interfaz web)
- JavaScript (carrito, AJAX, búsqueda dinámica)
- HTML5 y CSS3

---

## ⚙️ Instalación local

### 1. Clonar el repositorio
```bash
git clone https://github.com/jeancarlos336/LecheyMiel.git
cd LecheyMiel
```

### 2. Crear entorno virtual
```bash
python -m venv env
source env/bin/activate  # En Windows: env\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Crear archivo `.env`
Copia el archivo `.env.example` y renómbralo a `.env`, luego completa los datos reales:
```bash
cp .env.example .env  # O copiar manualmente
```

### 5. Configurar la base de datos PostgreSQL
Asegúrate de tener PostgreSQL instalado y crea una base de datos. Luego actualiza los datos en el archivo `.env`.

### 6. Migraciones y usuario admin
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 7. Ejecutar el servidor
```bash
python manage.py runserver
```
Visita: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 📁 Estructura básica del proyecto

```
LecheyMiel/
├── pos_system/         # Configuración principal del proyecto
├── ventas/             # App principal (productos, ventas, etc.)
├── templates/          # Plantillas HTML
├── static/             # Archivos estáticos (CSS, JS, imágenes)
├── media/              # Archivos subidos por usuarios
├── requirements.txt
├── .env.example
└── manage.py
```

---

## 🛡️ Seguridad

- Las variables sensibles se mantienen en el archivo `.env` (no se sube al repositorio)
- Usa HTTPS y configura adecuadamente `ALLOWED_HOSTS` para producción

---

## ✨ Créditos
Desarrollado por [Jean Carlos](https://github.com/jeancarlos336) — Proyecto personal para cafetería **Leche y Miel** ☕

---

## 📄 Licencia
Este proyecto está bajo la licencia MIT. Puedes modificarlo y usarlo libremente.