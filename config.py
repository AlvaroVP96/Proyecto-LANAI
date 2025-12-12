# config.py
# --------------------------------------------
# Configuración global del sistema
# --------------------------------------------

# Base de datos
DB_PATH = "acceso.db"
DEVICE_NAME = "demo-door-1"

# Cámara
CAMERA_ID = 1
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Reconocimiento facial
FACE_THRESHOLD = 0.70  # Umbral de similitud
FACE_MODEL = "ArcFace"
FACE_DETECTOR = "opencv"

# Gestos
GESTURE_TIMEOUT = 15  # segundos
GESTURE_FRAMES_REQUIRED = 30  # frames consecutivos

# Administrador
ADMIN_PIN_HASH = None  # Se configurará en primera ejecución

# Colores GUI
COLOR_BG = "#2C3E50"
COLOR_PANEL = "#34495E"
COLOR_SUCCESS = "#27AE60"
COLOR_ERROR = "#E74C3C"
COLOR_WARNING = "#E67E22"
COLOR_INFO = "#3498DB"
COLOR_TEXT = "#ECF0F1"
COLOR_TEXT_SECONDARY = "#BDC3C7"