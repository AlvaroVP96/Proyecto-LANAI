"""
Sistema de Liveness Anti-Spoofing Optimizado para Webcams Estándar
Solo usa las capas más confiables:
1. Detección de Movimiento (fallback robusto)
2. Detección de Moiré (pantallas LCD/LED)
3. Análisis de Reflectancia (papel vs piel)
"""

import cv2
import numpy as np
import random
import time

# ============================================================================
# CAPA 1: DETECCIÓN DE MOVIMIENTO CON ANÁLISIS DE DIRECCIÓN
# ============================================================================

def detectar_movimiento_con_direccion(frames, accion_solicitada):
    """
    Detecta movimiento Y verifica que coincide con la acción solicitada.
    
    Args:
        frames: Lista de frames capturados
        accion_solicitada: 'izquierda', 'derecha', 'arriba', 'abajo', 'sonrisa'
    
    Returns:
        tuple: (movimiento_valido: bool, score: float, detalles: dict)
    """
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    
    posiciones_rostro = []
    
    # Detectar posición del rostro en cada frame
    for frame in frames[::3]:  # Cada 3 frames para reducir procesamiento
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            centro_x = x + w // 2
            centro_y = y + h // 2
            posiciones_rostro.append((centro_x, centro_y))
    
    if len(posiciones_rostro) < 10:
        return False, 0.0, {"error": "Rostro no detectado suficientemente"}
    
    # Analizar trayectoria
    posiciones = np.array(posiciones_rostro)
    inicio = posiciones[:len(posiciones)//3]
    final = posiciones[-len(posiciones)//3:]
    
    mov_x = np.mean(final[:, 0]) - np.mean(inicio[:, 0])
    mov_y = np.mean(final[:, 1]) - np.mean(inicio[:, 1])
    
    magnitud_total = np.sqrt(mov_x**2 + mov_y**2)
    
    # Verificar dirección según acción
    movimiento_correcto = False
    
    if accion_solicitada == 'izquierda':
        # mov_x negativo (rostro se mueve a la izquierda en pantalla = derecha real)
        movimiento_correcto = mov_x < -20
    elif accion_solicitada == 'derecha':
        movimiento_correcto = mov_x > 20
    elif accion_solicitada == 'arriba':
        movimiento_correcto = mov_y < -15
    elif accion_solicitada == 'abajo':
        movimiento_correcto = mov_y > 15
    elif accion_solicitada == 'sonrisa':
        # Para sonrisa, solo verificamos que hubo movimiento general
        movimiento_correcto = magnitud_total > 10
    
    # Calcular variabilidad (persona real tiene movimiento no uniforme)
    diferencias_frame = np.diff(posiciones, axis=0)
    variabilidad = np.std(np.linalg.norm(diferencias_frame, axis=1))
    
    # Score combinado
    score = (magnitud_total / 100.0) + (variabilidad / 10.0)
    score = min(1.0, score)
    
    # Considerar válido si:
    # 1. Movimiento en dirección correcta
    # 2. Magnitud suficiente (>15 píxeles)
    # 3. Variabilidad alta (>2.0, indica movimiento orgánico)
    movimiento_valido = (movimiento_correcto and 
                        magnitud_total > 15 and 
                        variabilidad > 2.0)
    
    detalles = {
        "magnitud": float(magnitud_total),
        "mov_x": float(mov_x),
        "mov_y": float(mov_y),
        "variabilidad": float(variabilidad),
        "direccion_correcta": movimiento_correcto,
        "frames_analizados": len(posiciones_rostro)
    }
    
    return movimiento_valido, score, detalles


# ============================================================================
# CAPA 2: DETECCIÓN DE MOIRÉ MEJORADA
# ============================================================================

def detectar_pantalla_moire(frames):
    """
    Detecta si se está usando una pantalla mediante patrones Moiré.
    Analiza múltiples frames para mayor precisión.
    
    Returns:
        tuple: (es_pantalla: bool, score: float, detalles: dict)
    """
    # Analizar 5 frames distribuidos
    frames_a_analizar = [
        frames[len(frames)//4],
        frames[len(frames)//2],
        frames[3*len(frames)//4]
    ]
    
    ratios_moire = []
    num_peaks_total = []
    
    for frame in frames_a_analizar:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # FFT 2D
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude = np.abs(f_shift)
        
        h, w = magnitude.shape
        center_y, center_x = h // 2, w // 2
        
        # Máscara para altas frecuencias
        radius_inner = min(h, w) // 4
        radius_outer = min(h, w) // 2
        
        y, x = np.ogrid[:h, :w]
        distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        mask_high_freq = (distance > radius_inner) & (distance < radius_outer)
        
        # Energía en altas frecuencias
        high_freq_energy = np.sum(magnitude[mask_high_freq])
        total_energy = np.sum(magnitude)
        moire_ratio = high_freq_energy / (total_energy + 1e-10)
        
        # Picos periódicos
        high_freq_region = magnitude[mask_high_freq]
        mean_high = np.mean(high_freq_region)
        std_high = np.std(high_freq_region)
        peaks = high_freq_region[high_freq_region > mean_high + 2*std_high]
        
        ratios_moire.append(moire_ratio)
        num_peaks_total.append(len(peaks))
    
    # Promedios
    moire_avg = np.mean(ratios_moire)
    peaks_avg = np.mean(num_peaks_total)
    
    # Pantalla LCD: moire_ratio > 0.18 O muchos picos (>80)
    es_pantalla = (moire_avg > 0.18 or peaks_avg > 80)
    
    detalles = {
        "moire_ratio": float(moire_avg),
        "num_peaks": int(peaks_avg),
        "umbral_ratio": 0.18,
        "umbral_peaks": 80
    }
    
    return es_pantalla, moire_avg, detalles


# ============================================================================
# CAPA 3: ANÁLISIS DE TEXTURA Y REFLECTANCIA
# ============================================================================

def analizar_textura_piel(frames):
    """
    Analiza textura para diferenciar piel real de papel/foto.
    
    Principio:
    - Piel real: Textura irregular, microporos, variabilidad
    - Foto/Papel: Textura uniforme, plana
    
    Returns:
        tuple: (es_piel: bool, score: float, detalles: dict)
    """
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    
    texturas_locales = []
    gradientes = []
    
    # Analizar 10 frames
    for frame in frames[::len(frames)//10]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            continue
        
        (x, y, w, h) = faces[0]
        
        # Región de la mejilla (mejor textura que frente)
        mejilla_y = y + int(h * 0.4)
        mejilla_h = int(h * 0.3)
        mejilla_x = x + int(w * 0.6)
        mejilla_w = int(w * 0.3)
        
        mejilla_roi = gray[mejilla_y:mejilla_y+mejilla_h, 
                          mejilla_x:mejilla_x+mejilla_w]
        
        if mejilla_roi.size == 0:
            continue
        
        # 1. Análisis de textura con LBP (Local Binary Pattern) simplificado
        # Calcular varianza local en ventanas pequeñas
        kernel_size = 8
        texturas = []
        for i in range(0, mejilla_roi.shape[0] - kernel_size, kernel_size//2):
            for j in range(0, mejilla_roi.shape[1] - kernel_size, kernel_size//2):
                patch = mejilla_roi[i:i+kernel_size, j:j+kernel_size]
                texturas.append(np.var(patch))
        
        if texturas:
            texturas_locales.append(np.mean(texturas))
        
        # 2. Análisis de gradientes (bordes)
        # Piel real tiene gradientes suaves, foto tiene bordes más marcados
        sobelx = cv2.Sobel(mejilla_roi, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(mejilla_roi, cv2.CV_64F, 0, 1, ksize=3)
        gradiente = np.sqrt(sobelx**2 + sobely**2)
        gradientes.append(np.mean(gradiente))
    
    if len(texturas_locales) < 3:
        return False, 0.0, {"error": "Datos insuficientes"}
    
    # Promedios
    textura_promedio = np.mean(texturas_locales)
    gradiente_promedio = np.mean(gradientes)
    
    # Piel real:
    # - Textura media-alta (50-150)
    # - Gradientes suaves (10-30)
    # Foto/Papel:
    # - Textura baja (<40) o muy alta (>200, por artefactos de impresión)
    # - Gradientes altos (>40, bordes marcados)
    
    es_piel = (50 < textura_promedio < 150 and gradiente_promedio < 35)
    
    # Score normalizado
    score_textura = min(1.0, textura_promedio / 100.0)
    score_gradiente = max(0.0, 1.0 - gradiente_promedio / 50.0)
    score = (score_textura + score_gradiente) / 2
    
    detalles = {
        "textura": float(textura_promedio),
        "gradiente": float(gradiente_promedio),
        "umbral_textura_min": 50,
        "umbral_textura_max": 150,
        "umbral_gradiente": 35
    }
    
    return es_piel, score, detalles


# ============================================================================
# SISTEMA INTEGRADO - 3 CAPAS
# ============================================================================

def verificacion_liveness_optimizada(verbose=True):
    """
    Sistema optimizado de 3 capas para webcams estándar.
    
    Capas:
    1. Movimiento direccional (con challenge-response)
    2. Detección de pantallas (Moiré)
    3. Análisis de textura de piel
    
    Score mínimo: 2/3 capas
    
    Returns:
        np.ndarray: Frame final si pasa verificación
        
    Raises:
        ValueError: Si falla la verificación
    """
    if verbose:
        print("\n" + "="*70)
        print("🛡️  SISTEMA ANTI-SPOOFING OPTIMIZADO")
        print("="*70)
    
    # Seleccionar acción aleatoria
    acciones = [
        ("izquierda", "Mueve tu cabeza lentamente hacia TU DERECHA"),
        ("derecha", "Mueve tu cabeza lentamente hacia TU IZQUIERDA"),
        ("sonrisa", "Sonríe y luego pon cara seria")
    ]
    
    accion_id, accion_texto = random.choice(acciones)
    
    if verbose:
        print(f"\n📋 Instrucción: {accion_texto}")
        print(f"⏱️  Duración: 5 segundos")
        input("\n   Presiona ENTER cuando estés listo...")
    
    # Capturar video
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir la cámara")
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    frames = []
    duracion = 10
    start_time = time.time()
    
    if verbose:
        print("\n📹 Capturando... ", end="", flush=True)
    
    while time.time() - start_time < duracion:
        ret, frame = cap.read()
        if ret:
            frames.append(frame.copy())
            
            display = frame.copy()
            tiempo_restante = int(duracion - (time.time() - start_time))
            cv2.putText(display, accion_texto, 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, (0, 255, 0), 1)
            cv2.putText(display, f"{tiempo_restante}s", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 
                       2, (0, 255, 255), 2)
            
            cv2.imshow('Verificacion Anti-Spoofing', display)
            cv2.waitKey(1)
    
    cap.release()
    cv2.destroyAllWindows()
    
    if verbose:
        print(f"✅ ({len(frames)} frames)\n")
    
    if len(frames) < 60:
        raise RuntimeError("No se capturaron suficientes frames")
    
    # ANÁLISIS DE 3 CAPAS
    score_total = 0
    max_score = 3
    resultados = {}
    
    # CAPA 1: Movimiento Direccional
    if verbose:
        print("🔬 Capa 1: Análisis de Movimiento...", end=" ")
    
    mov_valido, score_mov, det_mov = detectar_movimiento_con_direccion(frames, accion_id)
    resultados["movimiento"] = det_mov
    
    if mov_valido:
        score_total += 1
        if verbose:
            print(f"✅ (mag: {det_mov['magnitud']:.1f}px, var: {det_mov['variabilidad']:.1f})")
    else:
        if verbose:
            print(f"❌ FALLO (mag: {det_mov.get('magnitud', 0):.1f}px)")
    
    # CAPA 2: Detección de Pantallas
    if verbose:
        print("🔬 Capa 2: Detección de Pantallas...", end=" ")
    
    es_pantalla, score_pantalla, det_pantalla = detectar_pantalla_moire(frames)
    resultados["pantalla"] = det_pantalla
    
    if not es_pantalla:  # NO debe ser pantalla
        score_total += 1
        if verbose:
            print(f"✅ (ratio: {det_pantalla['moire_ratio']:.3f})")
    else:
        if verbose:
            print(f"❌ PANTALLA DETECTADA (ratio: {det_pantalla['moire_ratio']:.3f})")
    
    # CAPA 3: Textura de Piel
    if verbose:
        print("🔬 Capa 3: Análisis de Textura...", end=" ")
    
    es_piel, score_piel, det_piel = analizar_textura_piel(frames)
    resultados["textura"] = det_piel
    
    if es_piel:
        score_total += 1
        if verbose:
            print(f"✅ (tex: {det_piel['textura']:.1f}, grad: {det_piel['gradiente']:.1f})")
    else:
        if verbose:
            print(f"❌ FALLO (tex: {det_piel.get('textura', 0):.1f})")
    
    # DECISIÓN FINAL
    if verbose:
        print("\n" + "="*70)
        print(f"📊 Score Total: {score_total}/{max_score}")
        print("="*70)
    
    # Requiere 2/3 capas
    if score_total < 2:
        if verbose:
            print("❌ VERIFICACIÓN FALLIDA - Posible spoofing")
            print("\nMotivos:")
            if not mov_valido:
                print("   • Movimiento insuficiente o incorrecto (foto estática)")
            if es_pantalla:
                print("   • Patrón de pantalla detectado")
            if not es_piel:
                print("   • Textura anormal (foto impresa)")
        raise ValueError(f"liveness_failed_score_{score_total}_of_{max_score}")
    
    if verbose:
        print("✅ PERSONA REAL VERIFICADA")
        print("="*70 + "\n")
    
    return frames[-1]


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("🧪 Probando sistema optimizado de 3 capas...\n")
    
    try:
        frame = verificacion_liveness_optimizada(verbose=True)
        cv2.imwrite("test_optimizado_ok.jpg", frame)
        print("\n✅ Test exitoso - Frame guardado")
    except ValueError as e:
        print(f"\n❌ Verificación fallida: {e}")
    except KeyboardInterrupt:
        print("\n⚠️  Test cancelado")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()