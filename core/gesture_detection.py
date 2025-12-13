# core/gesture_detection.py
# --------------------------------------------
# Detección de gestos con MediaPipe
# --------------------------------------------

class GestureDetector:
    """Detector de gestos de mano"""  # Clase que agrupa la lógica de detección de gestos basados en landmarks

    def __init__(self):
        # Diccionario de gestos disponibles con sus descripciones legibles
        self.gestos_disponibles = {
            'pulgar_arriba': 'Pulgar arriba',
            'victoria': 'Victoria (2 dedos)',
            'ok': 'OK (circulo)',
            'mano_abierta': 'Mano abierta (5 dedos)',
            'puno': 'Puño cerrado'
        }

    def contar_dedos_levantados(self, landmarks):
        """Cuenta dedos levantados"""  # Devuelve cuántos dedos están extendidos según posiciones de landmarks
        dedos = []  # Lista para marcar cada dedo como levantado (1) o no (0)

        # Pulgar: se considera levantado si la punta (4) está a la izquierda de la articulación previa (3) en eje X
        # Nota: esto asume una mano derecha y coordenadas normalizadas, puede requerir ajustes por mano/rotación
        if landmarks[4].x < landmarks[3].x:
            dedos.append(1)  # Pulgar levantado
        else:
            dedos.append(0)  # Pulgar no levantado

        # Otros dedos: índice (8), medio (12), anular (16), meñique (20)
        tip_ids = [8, 12, 16, 20]  # IDs de las puntas de los dedos en MediaPipe
        for tip in tip_ids:
            # Un dedo está levantado si la punta (tip) está por encima de la articulación media (tip - 2) en eje Y
            # En coordenadas de imagen, menor Y usualmente significa más arriba
            if landmarks[tip].y < landmarks[tip - 2].y:
                dedos.append(1)  # Dedo levantado
            else:
                dedos.append(0)  # Dedo no levantado

        return sum(dedos)  # Retorna el total de dedos levantados

    def detectar_pulgar_arriba(self, landmarks):
        """Detecta pulgar arriba"""  # Comprueba si el gesto corresponde a "pulgar arriba"
        # Pulgar con sus segmentos ordenados verticalmente: punta (4) arriba de (3) y éste arriba de (2)
        pulgar_arriba = landmarks[4].y < landmarks[3].y < landmarks[2].y
        # Otros dedos hacia abajo: sus puntas por debajo de la articulación media
        otros_abajo = all(landmarks[i].y > landmarks[i - 2].y for i in [8, 12, 16, 20])
        return pulgar_arriba and otros_abajo  # Verdadero si pulgar arriba y resto abajo

    def detectar_victoria(self, landmarks):
        """Detecta victoria"""  # Gesto de dos dedos levantados (índice y medio)
        dedos = self.contar_dedos_levantados(landmarks)  # Cuenta dedos levantados
        indice_arriba = landmarks[8].y < landmarks[6].y  # Índice levantado
        medio_arriba = landmarks[12].y < landmarks[10].y  # Medio levantado
        return dedos == 2 and indice_arriba and medio_arriba  # Exactamente esos dos levantados

    def detectar_ok(self, landmarks):
        """Detecta OK"""  # Gesto de círculo entre pulgar e índice con otros dedos preferiblemente abiertos
        # Distancia Manhattan aproximada entre punta de pulgar (4) y punta de índice (8)
        dist = abs(landmarks[4].x - landmarks[8].x) + abs(landmarks[4].y - landmarks[8].y)
        # Considera OK si las puntas están muy cerca y hay al menos 3 dedos levantados
        return dist < 0.05 and self.contar_dedos_levantados(landmarks) >= 3

    def detectar_mano_abierta(self, landmarks):
        """Detecta mano abierta"""  # Todos los dedos levantados
        return self.contar_dedos_levantados(landmarks) == 5

    def detectar_puno(self, landmarks):
        """Detecta puño"""  # Ningún dedo levantado
        return self.contar_dedos_levantados(landmarks) == 0

    def verificar_gesto(self, gesto_solicitado, landmarks):
        """Verifica si el gesto coincide"""  # Selecciona el detector según el nombre y lo ejecuta
        metodos = {
            'pulgar_arriba': self.detectar_pulgar_arriba,  # Mapa de nombre a función detectora
            'victoria': self.detectar_victoria,
            'ok': self.detectar_ok,
            'mano_abierta': self.detectar_mano_abierta,
            'puno': self.detectar_puno
        }
        # Obtiene el método, o una función que devuelve False si no existe, y lo llama con landmarks
        return metodos.get(gesto_solicitado, lambda x: False)(landmarks)