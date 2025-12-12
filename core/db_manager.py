# core/db_manager.py
# --------------------------------------------
# Gestión de base de datos
# --------------------------------------------

import sqlite3
import json
from collections import defaultdict
from config import DB_PATH, DEVICE_NAME


def ensure_schema():
    """Crea tablas si no existen"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      pin TEXT NOT NULL,
      active INTEGER DEFAULT 1,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS faces(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      encoding_json TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
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


def fetch_active_users_and_faces():
    """
    Devuelve:
      users: dict user_id -> {"name": str, "pin": str}
      faces: dict user_id -> [embedding_list, ...]
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT id, name, pin FROM users WHERE active=1")
    users_rows = c.fetchall()
    users = {uid: {"name": name, "pin": pin} for uid, name, pin in users_rows}

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


def get_all_users():
    """Obtiene todos los usuarios (activos e inactivos)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, name, active, created_at,
               (SELECT COUNT(*) FROM faces WHERE user_id = users.id) as face_count
        FROM users
        ORDER BY created_at DESC
    """)
    users = c.fetchall()
    conn.close()
    return users


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


def update_user_status(user_id: int, active: bool):
    """Activa o desactiva un usuario"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET active=? WHERE id=?", (1 if active else 0, user_id))
    conn.commit()
    conn.close()


def delete_user(user_id: int):
    """Elimina un usuario y todos sus rostros"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def log_event(user_id, result, note=""):
    """Registra un evento de acceso"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO events(device, user_id, result, note) VALUES(?,?,?,?)",
        (DEVICE_NAME, user_id, result, note)
    )
    conn.commit()
    conn.close()


def get_recent_events(limit=50):
    """Obtiene los eventos más recientes"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT e.id, e.ts, e.device, u.name, e.result, e.note 
        FROM events e
        LEFT JOIN users u ON e.user_id = u.id
        ORDER BY e.ts DESC
        LIMIT ?
    """, (limit,))
    events = c.fetchall()
    conn.close()
    return events


def get_user_stats(user_id: int):
    """Obtiene estadísticas de un usuario"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Total de accesos
    c.execute("""
        SELECT COUNT(*) FROM events 
        WHERE user_id = ? AND result = 'granted'
    """, (user_id,))
    total_accesos = c.fetchone()[0]
    
    # Accesos denegados
    c.execute("""
        SELECT COUNT(*) FROM events 
        WHERE user_id = ? AND result = 'denied'
    """, (user_id,))
    accesos_denegados = c.fetchone()[0]
    
    # Último acceso
    c.execute("""
        SELECT ts FROM events 
        WHERE user_id = ? AND result = 'granted' 
        ORDER BY ts DESC LIMIT 1
    """, (user_id,))
    row = c.fetchone()
    ultimo_acceso = row[0] if row else "Nunca"
    
    # Número de rostros registrados
    c.execute("""
        SELECT COUNT(*) FROM faces WHERE user_id = ?
    """, (user_id,))
    num_rostros = c.fetchone()[0]
    
    conn.close()
    
    return {
        'total_accesos': total_accesos,
        'accesos_denegados': accesos_denegados,
        'ultimo_acceso': ultimo_acceso,
        'num_rostros': num_rostros
    }