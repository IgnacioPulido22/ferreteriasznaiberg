# Guía de Colaboración — Ferretería Sznaiberg

Sitio web: **ferreteriasz.com**  
Repositorio: **github.com/IgnacioPulido22/ferreteriasznaiberg**

---

## Configuración inicial (solo la primera vez)

### 1. Instalar Git
Descargar desde: https://git-scm.com/download/win  
Instalarlo con todas las opciones por defecto.

### 2. Clonar el repositorio
Abrir una terminal (CMD o PowerShell) y correr:
```bash
git clone https://github.com/IgnacioPulido22/ferreteriasznaiberg.git
cd ferreteriasznaiberg
```

### 3. Configurar tu nombre en Git (solo la primera vez)
```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"
```

---

## Flujo de trabajo diario

### Antes de empezar SIEMPRE
```bash
git pull origin main
```
Esto trae los cambios del otro colaborador. Nunca editar sin hacer esto primero.

### Después de terminar los cambios
```bash
git add build.py index.html
git commit -m "descripcion breve de lo que cambiaste"
git push origin main
```

Vercel despliega automáticamente en 1-2 minutos tras el push.

### Coordinación
Avisar por WhatsApp antes de empezar a editar: *"voy a hacer cambios"*.  
Avisar cuando terminás: *"listo, ya subí"*, para que el otro pueda hacer `git pull`.

---

## Cómo hacer cambios en la web

### Todos los cambios se hacen en `build.py`

Abrir `build.py` con cualquier editor de texto (Notepad++, VS Code, etc.).  
Después de editar, correr en la terminal:
```bash
python build.py
```
Esto genera el archivo `index.html` actualizado.

---

## Cambios frecuentes

### Cambiar teléfono de contacto
Buscar en `build.py` el texto `+54 9 11 0000-0000` y reemplazarlo por el número real.  
Aparece en 3 lugares: topbar, botón WhatsApp del modal, y el checkout.

### Cambiar horarios de atención
Buscar `Lun–Vie 8:00–18:00` y `Sáb 9:00–14:00` y editar según corresponda.

### Cambiar dirección
Buscar `Buenos Aires, Argentina` en el topbar y el footer.

### Cambiar el email de contacto
Buscar `ventas@sznaiberg.com.ar` en el footer.

### Cambiar el texto del hero (banner principal)
Buscar `Todo lo que necesitás` — es el título grande de la página principal.  
Buscar `Miles de productos` — es el subtítulo debajo.

---

## Cómo editar productos (precios, nombres, categorías)

### Opción A — Panel admin (sin código, desde el browser)
Entrar a: **ferreteriasz.com/admin**  
Permite editar el catálogo directamente sin tocar ningún archivo.

### Opción B — Editar products.json directamente
El archivo `products.json` contiene los 4.000+ productos. Cada producto tiene esta estructura:
```json
{
  "id": 1,
  "name": "NOMBRE DEL PRODUCTO",
  "cat": "Herramientas",
  "price": 1500,
  "price_old": 0,
  "description": "",
  "badge": "",
  "img": "https://..."
}
```

Campos principales:
- `name` — nombre del producto (en mayúsculas)
- `cat` — categoría (debe coincidir exactamente con las de abajo)
- `price` — precio actual en pesos
- `price_old` — precio tachado (poner 0 si no hay)
- `badge` — etiqueta especial: `"NUEVO"`, `"OFERTA"`, etc. (dejar vacío si no hay)
- `description` — descripción breve (puede quedar vacío)

Categorías válidas:
```
Herramientas
Electricidad e Iluminacion
Plomeria y Sanitarios
Pinturas y Accesorios
Ferreteria y Fijacion
Adhesivos y Selladores
Cerraduras y Herrajes
Construccion
Materiales Generales
Lubricantes
Control de Plagas
Seguridad Industrial
Jardin y Exterior
```

Después de editar `products.json`, hay que subirlo a Supabase corriendo:
```bash
python subir_productos.py
```
*(o usar el panel admin que lo hace automáticamente)*

---

## Estructura de archivos

```
ferreteriasznaiberg/
├── build.py              ← ARCHIVO PRINCIPAL: toda la web está acá
├── index.html            ← Generado por build.py (no editar directo)
├── products.json         ← Catálogo de productos
├── scrape_images.py      ← Script para buscar imágenes en ferriplast
├── api/
│   ├── auth.js           ← Autenticación del panel admin
│   └── save.js           ← Guardado del catálogo desde el admin
├── vercel.json           ← Configuración de Vercel
└── package.json          ← Configuración Node.js para Vercel
```

---

## Si hay un conflicto de Git

Cuando dos personas editan el mismo archivo al mismo tiempo, Git avisa con un error al hacer `git push`. Para resolverlo:

```bash
git pull origin main
```

Git va a marcar el conflicto dentro del archivo así:
```
<<<<<<< HEAD
tu versión del texto
=======
versión del otro colaborador
>>>>>>> origin/main
```

Editar el archivo a mano dejando la versión correcta y borrando esas marcas.  
Después:
```bash
git add build.py
git commit -m "resolver conflicto"
git push origin main
```

---

## Stack tecnológico (referencia rápida)

| Componente | Tecnología |
|------------|------------|
| Frontend | HTML/CSS/JS estático generado por `build.py` |
| Hosting | Vercel (deploy automático con cada push a main) |
| Base de datos | Supabase (PostgreSQL) |
| Dominio | ferreteriasz.com (GoDaddy → Vercel) |
| Imágenes | Servidas desde ferriplast.com.ar (sin descarga) |
| Admin | ferreteriasz.com/admin |

---

## Contacto y accesos

- **Repositorio GitHub**: github.com/IgnacioPulido22/ferreteriasznaiberg
- **Panel Vercel**: vercel.com (cuenta del dueño del proyecto)
- **Panel Supabase**: supabase.com (cuenta del dueño del proyecto)
- **Panel admin web**: ferreteriasz.com/admin
