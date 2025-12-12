# core/__init__.py
# --------------------------------------------
# Módulos core del sistema
# --------------------------------------------

from .db_manager import (
    ensure_schema,
    fetch_active_users_and_faces,
    insert_user,
    insert_face,
    log_event,
    get_recent_events,
    get_all_users,
    update_user_status,
    delete_user
)

from .face_recognition import (
    get_embedding_deepface,
    cosine_similarity,
    best_match_per_user
)

from .gesture_detection import GestureDetector

__all__ = [
    'ensure_schema',
    'fetch_active_users_and_faces',
    'insert_user',
    'insert_face',
    'log_event',
    'get_recent_events',
    'get_all_users',
    'update_user_status',
    'delete_user',
    'get_embedding_deepface',
    'cosine_similarity',
    'best_match_per_user',
    'GestureDetector'
]