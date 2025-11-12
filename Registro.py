# Registro.py
# --------------------------------------------
# Registro de usuario con múltiples capturas faciales y PIN
# Guarda todo en SQLite (acceso.db):
#   - users(id, name, pin, active)
#   - faces(id, user_id, encoding_json)
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
import sqlite3
import bcrypt
from deepface import DeepFace
from liveness_interactivo import verificacion_liveness_interactiva

DB_PATH = "acceso.db"

# ---------- Base de datos ----------
def ensure_schema():
    """Crea tablas si no existen"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      pin TEXT NOT NULL,
      active INTEGER DEFAULT 1
    );
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS faces(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      encoding_json TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS events(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts DATETIME DEFAULT CURRENT_TIMESTAMP,
      device TEXT,
      user_id INTEGER,
      result TEXT,
      note TEXT
    );
    """)

    c.execute("CREATE INDEX IF NOT EXISTS idx_faces_user ON faces(user_id);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);")

    conn.commit()
    conn.close()


def insert_user(name: str, pinhash: str) -> int:
    """Inserta un nuevo usuario y retorna su ID"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO users(name, pin) VALUES(?, ?)", (name, pinhash))
    user_id = c.lastrowid
    conn.commit()
    conn.close()
    return user_id


def insert_face(user_id: int, embedding) -> None:
    """Inserta un embedding facial para un usuario"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO faces(user_id, encoding_json) VALUES(?, ?)",
        (user_id, json.dumps(list(embedding)))
    )
    conn.commit()
    conn.close()


# ---------- Captura múltiple ----------
def capturar_multiples_fotos(nombre: str, num_fotos: int = 3):
    """
    Captura múltiples fotos del usuario en diferentes poses.
    PRIMERO verifica liveness para asegurar que es una persona real.
    """
    
    # ✅ PASO 0: VERIFICACIÓN DE LIVENESS (ANTI-SPOOFING)
    print("\n" + "="*70)
    print("🛡️  PASO 1/2: VERIFICACIÓN ANTI-SPOOFING")
    print("="*70)
    print("\nAntes de registrarte, debes demostrar que eres una persona real.")
    print("Se te pedirá realizar UNA acción aleatoria.\n")
    
    try:
        # Verificar liveness con acción aleatoria
        frame_liveness = verificacion_liveness_interactiva()
        print("✅ Liveness verificado - Continuando con registro facial...\n")
    except ValueError as e:
        print(f"\n❌ No se pudo verificar que eres una persona real.")
        print(f"   Motivo: {e}")
        print("\n   El registro ha sido cancelado por seguridad.")
        raise
    except Exception as e:
        print(f"\n❌ Error durante verificación de liveness: {e}")
        raise
    
    # ✅ PASO 1: CAPTURA MÚLTIPLE DE FOTOS
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir la cámara")
    
    # Configurar resolución
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Incluir el frame de liveness como primera foto
    frames_capturados = [frame_liveness]
    
    instrucciones = [
        "📸 Foto 2: Mira de FRENTE a la cámara",
        "📸 Foto 3: Gira ligeramente a la IZQUIERDA",
        "📸 Foto 4: SONRÍE mirando al frente",
        "📸 Foto 5: Expresión NEUTRAL"
    ]
    
    print("="*70)
    print(f"🎥 PASO 2/2: CAPTURA MÚLTIPLE DE FOTOS - {nombre}")
    print("="*70)
    print(f"\nVamos a capturar {num_fotos} fotos adicionales en diferentes poses.")
    print("(Ya tenemos 1 foto de la verificación de liveness)\n")
    
    for i in range(num_fotos - 1):  # -1 porque ya tenemos una del liveness
        instruccion = instrucciones[i % len(instrucciones)]
        
        print("-" * 70)
        print(f"{instruccion}")
        print("-" * 70)
        input("Presiona ENTER cuando estés listo...")
        
        # Preview de 3 segundos con countdown
        print("Preparando captura en: ", end="", flush=True)
        for countdown in range(3, 0, -1):
            print(f"{countdown}... ", end="", flush=True)
            
            for _ in range(10):  # 10 frames por segundo
                ret, frame = cap.read()
                if ret:
                    display = frame.copy()
                    
                    # Texto con instrucción
                    cv2.putText(display, instruccion, 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                               0.6, (0, 255, 0), 2)
                    
                    # Countdown grande en el centro
                    text_size = cv2.getTextSize(str(countdown), 
                                               cv2.FONT_HERSHEY_SIMPLEX, 
                                               3, 3)[0]
                    text_x = (frame.shape[1] - text_size[0]) // 2
                    text_y = (frame.shape[0] + text_size[1]) // 2
                    cv2.putText(display, str(countdown), 
                               (text_x, text_y), 
                               cv2.FONT_HERSHEY_SIMPLEX, 
                               3, (0, 255, 255), 3)
                    
                    cv2.imshow('Registro Multiple', display)
                    cv2.waitKey(100)
        
        print("¡CAPTURANDO!")
        
        # Captura final
        ret, frame = cap.read()
        if ret:
            frames_capturados.append(frame.copy())
            
            # Mostrar frame capturado por 1 segundo
            display = frame.copy()
            cv2.putText(display, "CAPTURADO!", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 
                       1, (0, 255, 0), 2)
            cv2.imshow('Registro Multiple', display)
            cv2.waitKey(1000)
            
            print(f"   ✅ Foto {i+2}/{num_fotos} capturada correctamente\n")
        else:
            print(f"   ❌ Error al capturar foto {i+2}\n")
    
    cap.release()
    cv2.destroyAllWindows()
    
    return frames_capturados


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
        raise ValueError("No se detectó rostro en la imagen")
    return reps[0]["embedding"]


# ---------- Main ----------
def main():
    ensure_schema()

    print("\n" + "="*70)
    print("👤 REGISTRO DE NUEVO USUARIO - Sistema Multipose")
    print("="*70)
    
    # Solicitar datos del usuario
    name = input("\n📝 Nombre del usuario: ").strip()
    if not name:
        print("❌ Nombre vacío. Cancelando registro.")
        return

    pin = input("🔑 PIN (4-6 dígitos recomendado): ").strip()
    if not pin:
        print("❌ PIN vacío. Cancelando registro.")
        return
    
    # Confirmar PIN
    pin_confirm = input("🔑 Confirma el PIN: ").strip()
    if pin != pin_confirm:
        print("❌ Los PINs no coinciden. Cancelando registro.")
        return
    
    # Hash del PIN
    pinhash = bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()

    # Capturar múltiples fotos
    try:
        num_capturas = 3  # Puedes cambiar a 5 para más precisión
        frames = capturar_multiples_fotos(name, num_fotos=num_capturas)
        
        if len(frames) < 2:
            print("\n❌ Se necesitan al menos 2 fotos válidas para el registro.")
            return
        
    except Exception as e:
        print(f"\n❌ Error durante la captura: {e}")
        return

    # Extraer embeddings de cada foto
    print("\n" + "="*70)
    print("🔍 PROCESANDO IMÁGENES")
    print("="*70)
    
    embeddings = []
    for i, frame in enumerate(frames):
        try:
            print(f"\nProcesando foto {i+1}/{len(frames)}...", end=" ")
            embedding = get_embedding_deepface(frame)
            embeddings.append(embedding)
            print("✅ OK")
        except Exception as e:
            print(f"⚠️  Error: {e}")
            continue
    
    if len(embeddings) < 2:
        print("\n❌ Se necesitan al menos 2 embeddings válidos.")
        print("   Intenta registrarte de nuevo con mejor iluminación.")
        return

    # Guardar en base de datos
    print(f"\n💾 Guardando usuario en base de datos...")
    try:
        user_id = insert_user(name, pinhash)
        
        for emb in embeddings:
            insert_face(user_id, emb)
        
        print("\n" + "="*70)
        print("✅ REGISTRO COMPLETADO EXITOSAMENTE")
        print("="*70)
        print(f"   👤 Usuario: {name}")
        print(f"   🆔 ID: {user_id}")
        print(f"   📸 Fotos registradas: {len(embeddings)}/{len(frames)}")
        print(f"   🔐 PIN: {'*' * len(pin)}")
        print("\n   El usuario ya puede verificar su acceso con: python verificar.py")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error al guardar en base de datos: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Registro cancelado por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
