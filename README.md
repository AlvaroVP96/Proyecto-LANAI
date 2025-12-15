# 🔐 Sistema de Control de Acceso Multimodal

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

**Sistema avanzado de control de acceso que combina reconocimiento facial, detección de gestos y autenticación por PIN**

[Características](#-características) •
[Instalación](#-instalación) •
[Uso](#-uso) •
[Arquitectura](#-arquitectura) •
[API](#-api)

</div>

---

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Configuración](#️-configuración)
- [Uso](#-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Arquitectura](#-arquitectura)
- [Seguridad](#-seguridad)
- [Troubleshooting](#-troubleshooting)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)
- [Autores](#-autores)

---

## 📝 Descripción

Sistema de control de acceso de triple factor de autenticación que combina:

1. **🤚 Verificación de Gestos**: Detección en tiempo real con MediaPipe
2. **👤 Reconocimiento Facial**: Usando DeepFace con modelo ArcFace
3. **🔢 PIN de Seguridad**: Autenticación numérica encriptada con bcrypt

Ideal para entornos que requieren alta seguridad como laboratorios, oficinas, áreas restringidas, etc.

---

## ✨ Características

### 🔒 Seguridad Multicapa
- ✅ Triple factor de autenticación
- ✅ Encriptación de PINs con bcrypt
- ✅ Detección de intentos fallidos
- ✅ Registro completo de eventos (logs)

### 🎯 Reconocimiento Facial
- ✅ Modelo ArcFace de última generación
- ✅ Múltiples rostros por usuario
- ✅ Tolerancia a variaciones de iluminación
- ✅ Detección de rostros en tiempo real

### 🤲 Detección de Gestos
- ✅ 5 gestos predefinidos:
  - 👍 Pulgar arriba
  - ✌️ Victoria (2 dedos)
  - 👌 OK (círculo)
  - 🖐️ Mano abierta
  - ✊ Puño cerrado
- ✅ Selección aleatoria para mayor seguridad
- ✅ Feedback visual en tiempo real

### 🖥️ Interfaz Gráfica
- ✅ GUI moderna y responsive con Tkinter
- ✅ Panel de administración completo
- ✅ Vista previa en vivo de cámara
- ✅ Indicadores de estado en tiempo real

### 📊 Gestión y Administración
- ✅ CRUD completo de usuarios
- ✅ Registro múltiple de rostros
- ✅ Historial de eventos
- ✅ Exportación a CSV
- ✅ Estadísticas por usuario

---

## 💻 Requisitos

### Hardware
- 🎥 **Cámara web** (resolución mínima 640x480)
- 💾 **RAM**: Mínimo 4GB (recomendado 8GB)
- 🖥️ **CPU**: Intel i5 o superior
- 💿 **Espacio en disco**: 2GB libres

### Software
- 🐍 **Python**: 3.11 (recomendado)
- 🪟 **Sistema Operativo**: Windows 10/11 (desarrollo y pruebas)
- 📦 **pip**: Gestor de paquetes de Python

---

## 🚀 Instalación

### 1️⃣ Clonar o Descargar el Proyecto

```bash
cd d:\Master\LANAI
```

### 2️⃣ Crear Entorno Virtual (Recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Dependencias instaladas:**
- `opencv-python` - Procesamiento de imágenes y video
- `deepface` - Reconocimiento facial
- `mediapipe` - Detección de gestos
- `bcrypt` - Encriptación de contraseñas
- `Pillow` - Manipulación de imágenes
- `tensorflow` - Backend de DeepFace

### 4️⃣ Verificar Instalación

```bash
python -c "import cv2, deepface, mediapipe; print('✅ Todas las dependencias instaladas correctamente')"
```

### ⚡ Instalación rápida (Windows, Python 3.11)

```powershell
py --version
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si PowerShell bloquea scripts:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```


## ⚙️ Configuración

### Configuración Inicial

El archivo `config.py` contiene todas las configuraciones del sistema:

```python
# Base de datos
DB_PATH = "acceso.db"
DEVICE_NAME = "demo-door-1"

# Cámara
CAMERA_ID = 1  # Cambiar si tienes múltiples cámaras
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Reconocimiento facial
FACE_THRESHOLD = 0.70  # Umbral de similitud (0.5 - 0.9)
FACE_MODEL = "ArcFace"
FACE_DETECTOR = "opencv"

# Gestos
GESTURE_TIMEOUT = 15  # Segundos para realizar el gesto
GESTURE_FRAMES_REQUIRED = 30  # Frames consecutivos necesarios

# Colores de la interfaz (personalizable)
COLOR_BG = "#2C3E50"
COLOR_SUCCESS = "#27AE60"
COLOR_ERROR = "#E74C3C"
```

### Configuración de Cámara

Si tienes múltiples cámaras, identifica la correcta:

```python
# Probar cámaras disponibles
import cv2

for i in range(3):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"✅ Cámara {i} disponible")
        cap.release()
    else:
        print(f"❌ Cámara {i} no disponible")
```

---

## 📖 Uso

### Iniciar la Aplicación

```bash
python main.py
```

### 1️⃣ Primera Configuración

Al abrir el **Panel de Administración** por primera vez:

1. Se solicitará crear un **PIN de administrador** (4 dígitos)
2. Este PIN será necesario para acceder al panel en el futuro
3. El PIN se guarda encriptado en `admin_config.json`

### 2️⃣ Agregar Usuarios

**Desde el Panel de Administración > Pestaña "👥 Usuarios":**

1. Click en **"➕ Nuevo Usuario"**
2. Ingresar:
   - Nombre completo
   - PIN de 4 dígitos
   - Confirmar PIN
3. Click en **"✓ Crear Usuario"**

### 3️⃣ Registrar Rostros

**Desde el Panel de Administración > Pestaña "📸 Registro de Rostros":**

1. Click en **"▶️ Iniciar Registro de Rostros"**
2. Seleccionar usuario de la lista
3. Asegurar buena iluminación
4. Capturar **3-5 fotos** desde diferentes ángulos:
   - De frente
   - Girado ligeramente a la izquierda
   - Girado ligeramente a la derecha
   - Con diferentes expresiones
5. Click en **"💾 Guardar Rostros"**

### 4️⃣ Verificar Acceso

**Desde la Ventana Principal:**

1. Click en **"🔐 VERIFICAR ACCESO"**
2. Proceso de verificación (4 pasos):

   **Paso 1: Gesto**
   - Se muestra un gesto aleatorio en pantalla
   - Realizar el gesto frente a la cámara
   - Mantener el gesto hasta que la barra llegue al 100%

   **Paso 2: Captura Facial**
   - Esperar 1 segundo
   - El sistema captura automáticamente

   **Paso 3: Reconocimiento**
   - El sistema analiza el rostro
   - Compara con la base de datos
   - Muestra el usuario identificado

   **Paso 4: PIN**
   - Ingresar PIN de 4 dígitos
   - Presionar Enter o "Confirmar"

3. **Resultado:**
   - ✅ **Acceso Permitido**: Si todos los pasos son correctos
   - ❌ **Acceso Denegado**: Si falla algún paso

### 5️⃣ Ver Historial

**Desde el Panel de Administración > Pestaña "📊 Historial":**

- Ver todos los intentos de acceso
- Filtrar por cantidad de eventos
- Exportar a CSV
- Identificar patrones de uso

---

## 📁 Estructura del Proyecto

```
LANAI/
│
├── 📄 main.py                      # ⭐ Punto de entrada
├── 📄 config.py                    # Configuración global
├── 📄 requirements.txt             # Dependencias
├── 📄 README.md                    # Este archivo
├── 🗄️ acceso.db                    # Base de datos SQLite
├── 🔐 admin_config.json            # Configuración admin
│
├── 📂 core/                        # Lógica del sistema
│   ├── __init__.py
│   ├── db_manager.py              # Gestión de BD
│   ├── face_recognition.py        # Reconocimiento facial
│   └── gesture_detection.py       # Detección de gestos
│
├── 📂 gui/                         # Interfaces gráficas
│   ├── __init__.py
│   ├── access_window.py           # Ventana de acceso
│   └── admin_window.py            # Panel de administración
│
├── 📂 dialogs/                     # Diálogos modales
│   ├── __init__.py
│   ├── add_user_dialog.py         # Añadir usuario
│   └── register_faces_dialog.py   # Registrar rostros
│
└── 📂 utils/                       # Utilidades
    ├── __init__.py
    └── admin_auth.py              # Autenticación admin
```

---

## 🏗️ Arquitectura

### Diagrama de Flujo - Verificación de Acceso

```
┌─────────────────────────────────────────────────────────┐
│                    INICIAR VERIFICACIÓN                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   PASO 1: GESTO       │
         │  - Gesto aleatorio    │
         │  - Detección MediaPipe│
         │  - 30 frames correctos│
         └───────────┬───────────┘
                     │
                ✅ Éxito│❌ Fallo
                     │
                     ▼
         ┌───────────────────────┐
         │ PASO 2: CAPTURA FACIAL│
         │  - Captura con OpenCV │
         │  - Flip horizontal    │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │PASO 3: RECONOCIMIENTO │
         │  - Embedding DeepFace │
         │  - Comparar con BD    │
         │  - Mejor score > 0.70 │
         └───────────┬───────────┘
                     │
                ✅ Match│❌ No Match
                     │
                     ▼
         ┌───────────────────────┐
         │   PASO 4: PIN         │
         │  - Solicitar PIN      │
         │  - Verificar bcrypt   │
         └───────────┬───────────┘
                     │
            ✅ Correcto│❌ Incorrecto
                     │
                     ▼
         ┌───────────────────────┐
         │   ACCESO PERMITIDO    │
         │  - Log evento         │
         │  - Mostrar bienvenida │
         └───────────────────────┘
```

### Base de Datos

**Esquema SQLite:**

```sql
-- Tabla de usuarios
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    pin TEXT NOT NULL,              -- Hash bcrypt
    active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de rostros (embeddings)
CREATE TABLE faces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    encoding_json TEXT NOT NULL,    -- Array JSON de 512 floats
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Tabla de eventos (logs)
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP,
    device TEXT,
    user_id INTEGER,
    result TEXT,                    -- valores habituales: 'Entrada Permitida', 'Entrada Denegada', 'salida'
    note TEXT
);
```

---

## 🔐 Seguridad

### Encriptación

- **PINs de usuarios**: Hasheados con **bcrypt** (salt rounds automáticos)
- **PIN de admin**: Almacenado en `admin_config.json` con hash bcrypt

```python
# Ejemplo de hash
import bcrypt
pin = "1234"
hashed = bcrypt.hashpw(pin.encode(), bcrypt.gensalt())
# Resultado: $2b$12$KIX...
```

### Umbral de Similitud Facial

El sistema usa **similitud coseno** para comparar embeddings:

```python
score = cosine_similarity(embedding_query, embedding_bd)
# score ∈ [0, 1]
# Acceso permitido si score >= FACE_THRESHOLD (default 0.70)
```

**Ajustar umbral:**
- 🔴 **0.50 - 0.60**: Muy permisivo (menos seguro)
- 🟡 **0.65 - 0.75**: Balanceado (recomendado)
- 🟢 **0.80 - 0.90**: Muy restrictivo (más seguro, puede generar falsos negativos)

### Recomendaciones de Seguridad

1. ✅ Cambiar el PIN de admin regularmente
2. ✅ Registrar al menos 3 rostros por usuario
3. ✅ Asegurar buena iluminación en el área de captura
4. ✅ Revisar logs periódicamente
5. ✅ Hacer backups de `acceso.db`

---

## 🛠️ Troubleshooting

### Problema: Cámara no detectada

```bash
# Verificar cámaras disponibles
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"

# Solución:
# 1. Cambiar CAMERA_ID en config.py
# 2. Verificar permisos de cámara en Windows
# 3. Desactivar otras apps que usen la cámara
```

### Problema: Error al importar TensorFlow

```bash
# Error: DLL load failed
# Solución: Instalar Visual C++ Redistributable
# https://aka.ms/vs/17/release/vc_redist.x64.exe
```

### Problema: Reconocimiento facial lento

```python
# En config.py, cambiar detector:
FACE_DETECTOR = "opencv"  # Más rápido
# FACE_DETECTOR = "retinaface"  # Más preciso pero lento
```

### Problema: Muchos falsos positivos/negativos

```python
# Ajustar umbral en config.py:
FACE_THRESHOLD = 0.75  # Aumentar para más seguridad
FACE_THRESHOLD = 0.65  # Disminuir para más tolerancia
```

### Problema: Gestos no se detectan

1. Verificar iluminación
2. Asegurar que la mano esté completamente visible
3. Mantener la mano en el centro del marco
4. Realizar el gesto de forma clara

### Logs de Errores

Los errores se muestran en consola. Para debugging:

```python
# En main.py, agregar:
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📊 API / Funciones Principales

### Core - DB Manager

```python
from core import insert_user, insert_face, log_event

# Crear usuario
user_id = insert_user("Juan Pérez", pin_hash)

# Registrar rostro
insert_face(user_id, embedding)

# Log evento
log_event(user_id, "granted", "score=0.85")
```

### Core - Face Recognition

```python
from core import get_embedding_deepface, best_match_per_user

# Obtener embedding de un frame
embedding = get_embedding_deepface(frame_bgr)

# Buscar mejor match
user_id, score = best_match_per_user(embedding, faces_dict)
```

### Core - Gesture Detection

```python
from core import GestureDetector

detector = GestureDetector()
is_correct = detector.verificar_gesto('pulgar_arriba', landmarks)
```

---

## 🤝 Contribuir

### Cómo Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Ideas para Mejoras

- [ ] Soporte para múltiples cámaras
- [ ] Reconocimiento de voz como 4to factor
- [ ] Dashboard web con Flask
- [ ] Integración con hardware de control de puertas
- [ ] App móvil complementaria
- [ ] Modo "visitante temporal"
- [ ] Notificaciones por email/SMS
- [ ] Reconocimiento de matrículas vehiculares

---

## 📝 Changelog

### [1.0.0] - 2024-12-04

#### Añadido
- ✨ Sistema completo de verificación de acceso
- ✨ Panel de administración
- ✨ Reconocimiento facial con DeepFace
- ✨ Detección de 5 gestos
- ✨ Base de datos SQLite
- ✨ Exportación de logs a CSV
- ✨ Estadísticas por usuario

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

```
MIT License

Copyright (c) 2024 LANAI Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

## 👥 Autores

- **Nombre del Estudiante** - *Desarrollo Principal* - [Tu GitHub](https://github.com/AlvaroVP96/Proyecto-LANAI.git)
- **Profesor/Tutor** - *Supervisión*

---

## 🙏 Agradecimientos

- **DeepFace** - Framework de reconocimiento facial
- **MediaPipe** - Detección de gestos en tiempo real
- **OpenCV** - Procesamiento de video e imágenes
- **TensorFlow** - Backend de deep learning
- **bcrypt** - Seguridad de contraseñas

---

## 🌟 Demo

### Pantalla Principal
```
┌─────────────────────────────────────────────────────┐
│        SISTEMA DE CONTROL DE ACCESO                 │
├─────────────────────┬───────────────────────────────┤
│                     │  Panel de Control             │
│   Vista en Vivo     │                               │
│   ┌─────────────┐   │  🔐 VERIFICAR ACCESO          │
│   │             │   │                               │
│   │   CAMERA    │   │  Estado: Esperando...         │
│   │             │   │                               │
│   └─────────────┘   │  Usuarios activos: 5          │
│                     │                               │
│                     │  ⚙️ Panel Admin               │
└─────────────────────┴───────────────────────────────┘
```

---

<div align="center">

**⭐ Si te gusta este proyecto, dale una estrella en GitHub ⭐**

[⬆ Volver arriba](#-sistema-de-control-de-acceso-multimodal)

Made with ❤️ by LANAI Team

</div>