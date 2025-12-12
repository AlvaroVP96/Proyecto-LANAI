# core/face_recognition.py
# --------------------------------------------
# Reconocimiento facial con DeepFace
# --------------------------------------------

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

import math
from deepface import DeepFace
from config import FACE_MODEL, FACE_DETECTOR


def get_embedding_deepface(frame_bgr):
    """
    Obtiene el embedding facial con DeepFace.
    
    Args:
        frame_bgr: Frame en formato BGR de OpenCV
        
    Returns:
        list: Embedding facial
        
    Raises:
        ValueError: Si no se detecta rostro
    """
    reps = DeepFace.represent(
        img_path=frame_bgr,
        model_name=FACE_MODEL,
        detector_backend=FACE_DETECTOR,
        enforce_detection=True
    )
    if not reps:
        raise ValueError("No se detectó rostro en la imagen")
    return reps[0]["embedding"]


def cosine_similarity(a, b):
    """Similitud coseno entre dos embeddings"""
    num = sum(x * y for x, y in zip(a, b))
    den = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return (num / den) if den else 0.0


def best_match_per_user(query_emb, faces_by_user):
    """
    Encuentra el mejor match entre usuarios.
    
    Returns:
        tuple: (best_user_id, best_score)
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