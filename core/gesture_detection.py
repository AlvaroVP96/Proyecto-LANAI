# core/gesture_detection.py
# --------------------------------------------
# Detección de gestos con MediaPipe
# --------------------------------------------

class GestureDetector:
    """Detector de gestos de mano"""
    
    def __init__(self):
        self.gestos_disponibles = {
            'pulgar_arriba': 'Pulgar arriba',
            'victoria': 'Victoria (2 dedos)',
            'ok': 'OK (circulo)',
            'mano_abierta': 'Mano abierta (5 dedos)',
            'puno': 'Puño cerrado'
        }
    
    def contar_dedos_levantados(self, landmarks):
        """Cuenta dedos levantados"""
        dedos = []
        
        # Pulgar
        if landmarks[4].x < landmarks[3].x:
            dedos.append(1)
        else:
            dedos.append(0)
        
        # Otros dedos
        tip_ids = [8, 12, 16, 20]
        for tip in tip_ids:
            if landmarks[tip].y < landmarks[tip - 2].y:
                dedos.append(1)
            else:
                dedos.append(0)
        
        return sum(dedos)
    
    def detectar_pulgar_arriba(self, landmarks):
        """Detecta pulgar arriba"""
        pulgar_arriba = landmarks[4].y < landmarks[3].y < landmarks[2].y
        otros_abajo = all(landmarks[i].y > landmarks[i-2].y for i in [8, 12, 16, 20])
        return pulgar_arriba and otros_abajo
    
    def detectar_victoria(self, landmarks):
        """Detecta victoria"""
        dedos = self.contar_dedos_levantados(landmarks)
        indice_arriba = landmarks[8].y < landmarks[6].y
        medio_arriba = landmarks[12].y < landmarks[10].y
        return dedos == 2 and indice_arriba and medio_arriba
    
    def detectar_ok(self, landmarks):
        """Detecta OK"""
        dist = abs(landmarks[4].x - landmarks[8].x) + abs(landmarks[4].y - landmarks[8].y)
        return dist < 0.05 and self.contar_dedos_levantados(landmarks) >= 3
    
    def detectar_mano_abierta(self, landmarks):
        """Detecta mano abierta"""
        return self.contar_dedos_levantados(landmarks) == 5
    
    def detectar_puno(self, landmarks):
        """Detecta puño"""
        return self.contar_dedos_levantados(landmarks) == 0
    
    def verificar_gesto(self, gesto_solicitado, landmarks):
        """Verifica si el gesto coincide"""
        metodos = {
            'pulgar_arriba': self.detectar_pulgar_arriba,
            'victoria': self.detectar_victoria,
            'ok': self.detectar_ok,
            'mano_abierta': self.detectar_mano_abierta,
            'puno': self.detectar_puno
        }
        return metodos.get(gesto_solicitado, lambda x: False)(landmarks)