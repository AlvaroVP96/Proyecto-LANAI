# verificar.py
# --------------------------------------------
# Verifica acceso con DeepFace:
#  - Captura tu cara desde la webcam
#  - Calcula embedding
#  - Compara contra embeddings guardados en la BD
#  - Si hay match, pide PIN y decide
#  - Registra el resultado en 'events'
# --------------------------------------------

# ✅ SUPRIMIR MENSAJES DE TENSORFLOW
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

import cv2
import json
import math
import sqlite3
from collections import defaultdict
from deepface import DeepFace
import bcrypt

DB_PATH = "acceso.db"
DEVICE_NAME = "demo-door-1"

# ---------- Utilidades BD ----------
def fetch_active_users_and_faces():
    """
    Devuelve:
      users: dict user_id -> {"name": str, "pin": str}
      faces: dict user_id -> [embedding_list, ...]
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Usuarios activos
    c.execute("SELECT id, name, pin FROM users WHERE active=1")
    users_rows = c.fetchall()
    users = {uid: {"name": name, "pin": pin} for uid, name, pin in users_rows}

    # Embeddings
    c.execute("SELECT user_id, encoding_json FROM faces")
    faces_rows = c.fetchall()
    faces = defaultdict(list)
    for user_id, enc_json in faces_rows:
        try:
            emb = json.loads(enc_json)
            faces[user_id].append(emb)
        except Exception:
            continue

    conn.close()
    return users, faces


def event_shown():
    """Muestra el último evento registrado"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM events ORDER BY id DESC LIMIT 1;")
    event = c.fetchone()
    if event:
        print(f"\n📋 Evento registrado: {event}")
    conn.close()


def log_event(user_id, result, note=""):
    """Registra un evento de acceso en la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO events(device, user_id, result, note) VALUES(?,?,?,?)",
        (DEVICE_NAME, user_id, result, note)
    )
    conn.commit()
    conn.close()


# ---------- Captura simple ----------
def captura_simple():
    """Captura un frame de la webcam con preview"""
    cap = cv2.VideoCapture(0,cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir la cámara")
    
    # Configurar resolución
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("📸 Posiciona tu rostro frente a la cámara...")
    print("   Capturando en: ", end="", flush=True)
    
    # Countdown de 3 segundos
    for countdown in range(3, 0, -1):
        print(f"{countdown}... ", end="", flush=True)
        
        for _ in range(10):  # 10 frames por segundo
            ret, frame = cap.read()
            if ret:
                display = frame.copy()
                
                # Countdown en pantalla
                text_size = cv2.getTextSize(str(countdown), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 
                                           3, 3)[0]
                text_x = (frame.shape[1] - text_size[0]) // 2
                text_y = (frame.shape[0] + text_size[1]) // 2
                cv2.putText(display, str(countdown), 
                           (text_x, text_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 
                           3, (0, 255, 0), 3)
                
                cv2.imshow('Captura Facial', display)
                cv2.waitKey(100)
    
    print("¡CAPTURANDO!")
    
    # Captura final
    ret, frame = cap.read()
    cap.release()
    cv2.destroyAllWindows()
    
    if not ret:
        raise RuntimeError("Error al capturar imagen")
    
    print("   ✅ Imagen capturada\n")
    return frame


# ---------- Embeddings y comparación ----------
def get_embedding_deepface(frame_bgr):
    """
    Obtiene el embedding facial con DeepFace (ArcFace).
    """
    reps = DeepFace.represent(
        img_path=frame_bgr,
        model_name="ArcFace",
        detector_backend="opencv",
        enforce_detection=True
    )
    if not reps:
        raise ValueError("No se detectó rostro.")
    return reps[0]["embedding"]


def cosine_similarity(a, b):
    """Similitud coseno entre dos listas de floats."""
    num = sum(x * y for x, y in zip(a, b))
    den = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return (num / den) if den else 0.0


def best_match_per_user(query_emb, faces_by_user):
    """
    Calcula, por cada usuario, el mejor score (máxima similitud coseno)
    entre el embedding de consulta y sus múltiples embeddings guardados.
    """
    best_user, best_score = None, 0.0
    for uid, emb_list in faces_by_user.items():
        if not emb_list:
            continue
        score = max(cosine_similarity(query_emb, e) for e in emb_list)
        if score > best_score:
            best_score = score
            best_user = uid
    return best_user, best_score


# ---------- Main ----------
def main():
    print("\n" + "="*70)
    print("🔐 SISTEMA DE CONTROL DE ACCESO - VERIFICACIÓN")
    print("="*70)
    
    # Carga datos de usuarios registrados
    users, faces = fetch_active_users_and_faces()
    if not users or not any(faces.values()):
        print("\n❌ No hay usuarios/caras enrolados.")
        print("   Ejecuta primero: python Registro.py")
        return

    print(f"\n👥 Usuarios activos: {len(users)}")
    print(f"📸 Total de rostros registrados: {sum(len(f) for f in faces.values())}")

    # PASO 1: Captura facial
    print("\n" + "-"*70)
    print("PASO 1: Captura Facial")
    print("-"*70 + "\n")
    
    try:
        frame = captura_simple()
    except Exception as e:
        print(f"❌ Error durante captura: {e}")
        log_event(None, "denied", "capture_error")
        return

    # PASO 2: Reconocimiento facial
    print("-"*70)
    print("PASO 2: Reconocimiento Facial")
    print("-"*70)
    
    try:
        print("🔍 Extrayendo características faciales...", end=" ")
        query_emb = get_embedding_deepface(frame)
        print("✅")
    except Exception as e:
        print(f"\n❌ No se pudo obtener embedding: {e}")
        log_event(None, "denied", "no_face_or_embedding")
        return

    print("🔎 Comparando con base de datos...", end=" ")
    best_uid, best_score = best_match_per_user(query_emb, faces)
    print("✅")

    THRESHOLD = 0.85
    if best_uid is None or best_score < THRESHOLD:
        print("\n" + "="*70)
        print("❌ ACCESO DENEGADO")
        print("="*70)
        print(f"   Rostro no reconocido")
        print(f"   Score: {best_score:.3f} (mínimo: {THRESHOLD})")
        print("="*70 + "\n")
        log_event(None, "denied", f"low_score={best_score:.3f}")
        return

    # PASO 3: Verificación de PIN
    print("\n" + "-"*70)
    print("PASO 3: Verificación de PIN")
    print("-"*70)
    
    user = users.get(best_uid)
    print(f"\n👤 Usuario identificado: {user['name']}")
    print(f"   Similitud facial: {best_score:.3f}")
    
    pin_try = input("\n🔑 Introduce tu PIN: ").strip()

    if bcrypt.checkpw(pin_try.encode(), user["pin"].encode()):
        print("\n" + "="*70)
        print("✅ ACCESO PERMITIDO")
        print("="*70)
        print(f"   ¡Bienvenido, {user['name']}!")
        print("="*70 + "\n")
        log_event(best_uid, "granted", f"score={best_score:.3f}")
        event_shown()
    else:
        print("\n" + "="*70)
        print("❌ ACCESO DENEGADO")
        print("="*70)
        print(f"   PIN incorrecto")
        print("="*70 + "\n")
        log_event(best_uid, "denied", "pin_bad")
        event_shown()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()