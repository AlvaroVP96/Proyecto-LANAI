# gui/access_window.py
# --------------------------------------------
# Ventana principal de acceso
# --------------------------------------------

import tkinter as tk                # Importa Tkinter base
from tkinter import ttk, messagebox # Importa widgets y cuadros de diálogo
import threading                    # Para ejecutar tareas en segundo plano
import cv2                          # OpenCV para manejo de cámara y video
from PIL import Image, ImageTk      # Para convertir imágenes a formato Tkinter
import random                       # Selección aleatoria de gestos
import time                         # Tiempos y esperas
import bcrypt                       # Verificación segura de PINs

from config import *                # Configuración general (colores, tamaños, thresholds)
# Importa funciones y clases esenciales desde el módulo 'core':
from core import (
    fetch_active_users_and_faces,   # Obtiene usuarios activos y sus embeddings faciales
    log_event,                      # Registra eventos (entradas/salidas, errores, etc.)
    get_embedding_deepface,         # Genera el embedding del rostro usando DeepFace
    best_match_per_user,            # Encuentra el mejor usuario que coincide con el embedding
    GestureDetector                 # Clase para detectar y verificar gestos de mano
)

import mediapipe as mp              # MediaPipe para detección de manos

class VentanaAcceso:
    def __init__(self, root):
        self.root = root                                    # Guarda la ventana raíz
        self.root.title("Sistema de Control de Acceso")     # Título de ventana
        self.root.geometry("1400x900")                      # Tamaño inicial
        self.root.configure(bg=COLOR_BG)                    # Color de fondo
        
        # Variables de estado
        self.cap = None                                     # Capturador de cámara
        self.verificando = False                            # Flag de proceso de verificación en curso
        self.detector = GestureDetector()                   # Instancia del detector de gestos
        self.camara_activa = False                          # Flag para saber si la cámara está activa
        
        self.frames_correctos = 0                           # Contador de frames válidos del gesto
        self.frames_necesarios = 30                         # Frames consecutivos requeridos para validar gesto
        self.gesto_actual = None                            # Identificador del gesto solicitado
        self.gesto_objetivo = None                          # No usado (reservado)
        self.usuario_verificando = None                     # No usado (reservado)
        
        self.mp_hands = mp.solutions.hands                  # Referencia al módulo de manos
        self.hands = self.mp_hands.Hands(                   # Inicializa el modelo de manos
            static_image_mode=False,                        # Modo video (seguimiento)
            max_num_hands=2,                                # Máximo manos detectables
            min_detection_confidence=0.5,                   # Confianza mínima detección
            min_tracking_confidence=0.5                     # Confianza mínima seguimiento
        )
        self.mp_drawing = mp.solutions.drawing_utils        # Utilidad para dibujar landmarks
        
        self.setup_ui()                                     # Construye la interfaz
        self.iniciar_video()                                # Arranca la cámara
    
    def setup_ui(self):
        """Configura todos los elementos de la interfaz"""
        
        # Título superior
        titulo = tk.Label(
            self.root,
            text="SISTEMA DE CONTROL DE ACCESO",
            font=("Arial", 24, "bold"),
            bg=COLOR_BG,
            fg=COLOR_TEXT
        )
        titulo.pack(pady=20)                                # Añade el título con espacio
        
        # Frame principal que contendrá cámara y controles
        frame_principal = tk.Frame(self.root, bg=COLOR_BG)
        frame_principal.pack(expand=True, fill="both", padx=20, pady=10)
        
        # Panel izquierdo: muestra la cámara
        frame_camara = tk.Frame(frame_principal, bg=COLOR_PANEL, relief="raised", bd=3)
        frame_camara.pack(side="left", padx=10, fill="both", expand=True)
        
        tk.Label(
            frame_camara,
            text="Vista en Vivo",
            font=("Arial", 14, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT
        ).pack(pady=10)                                      # Etiqueta del panel de cámara
        
        # Canvas donde se pinta el frame de video
        self.canvas_video = tk.Canvas(
            frame_camara,
            width=CAMERA_WIDTH,
            height=CAMERA_HEIGHT,
            bg="#000000"
        )
        self.canvas_video.pack(pady=10, padx=10)
        
        # Panel derecho: controles y estados
        frame_controles = tk.Frame(frame_principal, bg=COLOR_PANEL, relief="raised", bd=3)
        frame_controles.pack(side="right", padx=10, fill="both")
        
        tk.Label(
            frame_controles,
            text="Panel de Control",
            font=("Arial", 14, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT
        ).pack(pady=20)                                      # Título del panel de control
        
        # Botón principal para iniciar verificación
        self.btn_verificar = tk.Button(
            frame_controles,
            text="🔐 VERIFICAR ACCESO",
            font=("Arial", 16, "bold"),
            bg=COLOR_SUCCESS,
            fg="white",
            activebackground="#229954",
            command=self.iniciar_verificacion,               # Llama al proceso de verificación
            width=20,
            height=3
        )
        self.btn_verificar.pack(pady=20, padx=20)
        
        # Estado actual del sistema
        tk.Label(
            frame_controles,
            text="Estado:",
            font=("Arial", 12, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT
        ).pack(pady=(30, 5))
        
        self.label_estado = tk.Label(
            frame_controles,
            text="Esperando...",
            font=("Arial", 11),
            bg=COLOR_PANEL,
            fg=COLOR_WARNING,
            wraplength=200
        )
        self.label_estado.pack(pady=5)
        
        # Separador visual
        ttk.Separator(frame_controles, orient="horizontal").pack(fill="x", pady=20, padx=20)
        
        # Bloque de información del sistema
        info_frame = tk.Frame(frame_controles, bg=COLOR_PANEL)
        info_frame.pack(pady=10, padx=20)
        
        tk.Label(
            info_frame,
            text="Usuarios activos:",
            font=("Arial", 10),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT_SECONDARY
        ).grid(row=0, column=0, sticky="w", pady=2)
        
        self.label_usuarios = tk.Label(
            info_frame,
            text="0",
            font=("Arial", 10, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT
        )
        self.label_usuarios.grid(row=0, column=1, sticky="e", pady=2)
        
        # Botón para abrir el panel de administración
        self.btn_admin = tk.Button(
            frame_controles,
            text="⚙️ Panel Admin",
            font=("Arial", 10),
            bg=COLOR_INFO,
            fg="white",
            command=self.abrir_admin,                         # Abre panel admin
            width=20
        )
        self.btn_admin.pack(side="bottom", pady=20)
        
        # Carga número de usuarios activos
        self.actualizar_info_sistema()
        
    def iniciar_video(self):
        """Inicia la captura de video"""
        if not self.cap or not self.cap.isOpened():                      # Si no hay cámara activa
            self.cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_DSHOW)        # Abre cámara DirectShow (Windows)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)         # Ajusta ancho
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)       # Ajusta alto
        self.camara_activa = True                                        # Marca cámara como activa
        self.actualizar_video()                                          # Empieza el loop de actualización
    
    def pausar_camara(self):  
        """Pausa la cámara sin liberarla"""
        self.camara_activa = False                                       # Detiene el loop de actualización
        if self.cap and self.cap.isOpened():
            self.cap.release()                                           # Libera el dispositivo de cámara
            self.cap = None
        # Muestra mensaje de pausa en el canvas
        self.canvas_video.delete("all")                                  # Limpia el canvas
        self.canvas_video.create_text(
            CAMERA_WIDTH // 2,
            CAMERA_HEIGHT // 2,
            text="⏸️ CÁMARA PAUSADA\n\n(Panel de administración abierto)",
            font=("Arial", 20, "bold"),
            fill=COLOR_WARNING
        )
    
    def reanudar_camara(self): 
        """Reanuda la cámara"""
        if not self.camara_activa:                                       # Solo si está pausada
            self.iniciar_video()                                         # Reinicia cámara y loop
    
    def actualizar_video(self):
        """Actualiza el video en tiempo real"""
        if not self.camara_activa:                                       # Si está pausada, no continúa
            return
        
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()                                 # Lee un frame de la cámara
            if ret:
                if self.verificando:                                     # Si está verificando gesto
                    frame = self.procesar_frame_gestos(frame)            # Procesa y dibuja overlay de gestos
                else:
                    frame = cv2.flip(frame, 1)                           # Esp espejo para vista normal
                
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)       # Convierte a RGB para PIL
                img = Image.fromarray(frame_rgb)                         # Crea imagen PIL
                img_tk = ImageTk.PhotoImage(image=img)                   # Convierte a objeto Tkinter
                
                self.canvas_video.create_image(0, 0, anchor="nw", image=img_tk) # Pinta en canvas
                self.canvas_video.image = img_tk                         # Referencia para evitar GC
        
        if self.camara_activa:                                           # Reprograma el próximo frame
            self.root.after(30, self.actualizar_video)                   # ~33 FPS aprox.
    
    def procesar_frame_gestos(self, frame):
        """Procesa frame para gestos"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)               # Prepara frame para MediaPipe
        results = self.hands.process(frame_rgb)                          # Ejecuta detección de manos
        
        gesto_correcto = False                                           # Flag del estado del gesto actual
        
        cv2.putText(frame, f"Gesto: {self.gesto_nombre}",                # Dibuja nombre del gesto solicitado
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if results.multi_hand_landmarks:                                 # Si hay manos detectadas
            for hand_landmarks in results.multi_hand_landmarks:          # Itera por cada mano
                self.mp_drawing.draw_landmarks(                          # Dibuja landmarks y conexiones
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0,255,0), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(0,255,255), thickness=2)
                )
                
                if self.detector.verificar_gesto(self.gesto_actual, hand_landmarks.landmark):
                    gesto_correcto = True                                # Marca gesto correcto
                    self.frames_correctos += 1                           # Suma frame válido
        
        if not gesto_correcto:
            self.frames_correctos = max(0, self.frames_correctos - 1)    # Penaliza si no coincide
        
        progreso = min(int((self.frames_correctos / self.frames_necesarios) * 100), 100) # % progreso
        
        cv2.rectangle(frame, (10, 450), (630, 470), (50, 50, 50), -1)    # Barra de fondo
        if progreso > 0:
            color = (0, 255, 0) if gesto_correcto else (255, 165, 0)     # Verde si va bien, naranja si no
            cv2.rectangle(frame, (10, 450), (10 + int(progreso * 6.2), 470), color, -1) # Barra progreso
        
        cv2.putText(frame, f"{progreso}%", (540, 465),                   # Texto del porcentaje
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame                                                     # Devuelve frame con overlay
    
    def verificacion_gesto_gui(self, timeout=GESTURE_TIMEOUT):
        """Verificación de gesto"""
        self.gesto_actual = random.choice(list(self.detector.gestos_disponibles.keys())) # Elige gesto aleatorio
        self.gesto_nombre = self.detector.gestos_disponibles[self.gesto_actual]          # Nombre legible
        self.frames_correctos = 0                                                        # Reinicia contador
        self.modo_normal = False                                                         # Activa modo verificación
        
        start_time = time.time()                                                         # Marca inicio
        
        while True:
            if time.time() - start_time > timeout:                                       # Si expira tiempo
                self.modo_normal = True
                self.gesto_actual = None
                raise TimeoutError("Tiempo agotado")                                     # Notifica timeout
            
            if self.frames_correctos >= self.frames_necesarios:                          # Si cumple frames
                time.sleep(0.5)                                                          # Pequeña espera
                self.modo_normal = True
                self.gesto_actual = None
                return True                                                              # Gesto validado
            
            time.sleep(0.1)                                                              # Evita busy-wait
            self.root.update()                                                           # Refresca GUI
    
    def actualizar_info_sistema(self):
        """Actualiza info del sistema"""
        users, faces = fetch_active_users_and_faces()           # Obtiene usuarios y embeddings
        self.label_usuarios.config(text=str(len(users)))        # Muestra cantidad de usuarios activos
        
    def cambiar_estado(self, texto, color=COLOR_WARNING):
        """Cambia estado"""
        self.label_estado.config(text=texto, fg=color)          # Actualiza texto y color del estado
        self.root.update()                                      # Refresca GUI
        
    def iniciar_verificacion(self):
        """Inicia verificación"""
        if self.verificando:                                    # Evita múltiples verificaciones simultáneas
            messagebox.showwarning("Aviso", "Verificación en curso")
            return
        
        self.btn_verificar.config(state="disabled", bg="#95A5A6") # Deshabilita botón mientras procesa
        self.verificando = True                                    # Marca estado verificando
        
        thread = threading.Thread(target=self.proceso_verificacion, daemon=True) # Hilo en segundo plano
        thread.start()                                              # Inicia hilo
    
    def proceso_verificacion(self):
        """Proceso de verificación completo"""
        try:
            self.cambiar_estado("Cargando...", COLOR_INFO)         # Estado: cargando
            users, faces = fetch_active_users_and_faces()          # Carga usuarios y embeddings
            
            if not users:                                          # Si no hay usuarios activos
                messagebox.showerror("Error", "No hay usuarios")
                return
            
            # Paso 1: Gesto
            self.cambiar_estado("Paso 1/4: Gesto", COLOR_WARNING)  # Indica paso
            try:
                if not self.verificacion_gesto_gui():              # Ejecuta verificación de gesto
                    log_event(None, "Entrada Denegada", "Gesto fallido")
                    messagebox.showerror("Denegado", "Gesto fallido")
                    return
            except TimeoutError:
                log_event(None, "Entrada Denegada", "Tiempo para gesto agotado")
                messagebox.showerror("Error", "Tiempo agotado")
                return
            
            # Paso 2: Captura de frame
            self.cambiar_estado("Paso 2/4: Captura", COLOR_WARNING)
            time.sleep(1)                                          # Pequeña espera
            ret, frame = self.cap.read()                           # Captura un frame
            if not ret:
                messagebox.showerror("Error", "Captura fallida")
                return
            frame = cv2.flip(frame, 1)                             # Voltea para vista natural
            
            # Paso 3: Reconocimiento facial
            self.cambiar_estado("Paso 3/4: Reconociendo", COLOR_WARNING)
            try:
                query_emb = get_embedding_deepface(frame)          # Obtiene embedding del rostro
            except:
                log_event(None, "Entrada Denegada", "No se detecto Rostro")
                messagebox.showerror("Error", "Sin rostro")
                return
            
            best_uid, best_score = best_match_per_user(query_emb, faces) # Busca mejor coincidencia
            
            if best_uid is None or best_score < FACE_THRESHOLD:     # Comprueba umbral de similitud
                log_event(None, "Entrada Denegada", f"No reconocido: {best_score:.3f}")
                messagebox.showerror("Denegado", f"Desconocido\nScore: {best_score:.3f}")
                return
            
            # Paso 4: PIN del usuario reconocido
            try:
                user = users.get(best_uid)
                print(best_uid)                          # Datos del usuario
                self.cambiar_estado(f"Usuario: {user['name']}", COLOR_INFO)
            except Exception as e:
                messagebox.showerror("NONE",str(e))
            
            try:
                pin = self.solicitar_pin(user['name'])  # Pide PIN
            except Exception as e:
                messagebox.showerror("NONE",str(e))
                            
            if not pin:
                return                                              # Cancelado
            
            if bcrypt.checkpw(pin.encode(), user["pin"].encode()):  # Verifica PIN contra hash
                self.cambiar_estado("PERMITIDO", COLOR_SUCCESS)     # Estado permitido
                log_event(best_uid, "Entrada Permitida",
                          f"Acceso Permitido: {user['name']} || score={best_score:.3f}")
                VentanaSalida(self.root, user['name'], best_uid)    # Abre ventana de salida
            else:
                log_event(best_uid, "Entrada Denegada", "Pin Incorrecto")
                messagebox.showerror("Denegado", "PIN incorrecto")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))                   # Muestra cualquier error inesperado
        finally:
            self.verificando = False                                 # Resetea flags
            self.modo_normal = True
            self.gesto_actual = None
            self.btn_verificar.config(state="normal", bg=COLOR_SUCCESS) # Rehabilita botón
            self.cambiar_estado("Esperando...", COLOR_WARNING)       # Estado por defecto
    
    def solicitar_pin(self, nombre):
        """Diálogo PIN"""
        dialog = tk.Toplevel(self.root)                              # Crea ventana secundaria
        dialog.title("PIN")
        dialog.geometry("350x200")
        dialog.configure(bg=COLOR_PANEL)
        dialog.transient(self.root)                                  # Se muestra sobre la principal
        dialog.grab_set()                                            # Bloquea interacción con la raíz
        
        dialog.geometry("+%d+%d" % (self.root.winfo_x() + 275, self.root.winfo_y() + 250)) # Posición
        
        resultado = {"pin": None}                                    # Contenedor para resultado
        
        tk.Label(dialog, text=f"Usuario: {nombre}", font=("Arial", 12, "bold"),
                bg=COLOR_PANEL, fg=COLOR_TEXT).pack(pady=20)         # Muestra nombre
        
        tk.Label(dialog, text="PIN:", font=("Arial", 10),
                bg=COLOR_PANEL, fg=COLOR_TEXT_SECONDARY).pack(pady=5) # Etiqueta PIN
        
        entry_pin = tk.Entry(dialog, show="*", font=("Arial", 14), width=15) # Campo PIN
        entry_pin.pack(pady=10)
        entry_pin.focus()                                             # Foco para escribir
        
        def confirmar():
            resultado["pin"] = entry_pin.get()                        # Guarda el PIN
            dialog.destroy()                                          # Cierra diálogo
        
        frame_btns = tk.Frame(dialog, bg=COLOR_PANEL)                 # Contenedor botones
        frame_btns.pack(pady=20)
        
        tk.Button(frame_btns, text="OK", command=confirmar,           # Botón aceptar
                 bg=COLOR_SUCCESS, fg="white", width=10).pack(side="left", padx=5)
        tk.Button(frame_btns, text="Cancelar", command=dialog.destroy,# Botón cancelar
                 bg=COLOR_ERROR, fg="white", width=10).pack(side="left", padx=5)
        
        entry_pin.bind("<Return>", lambda e: confirmar())             # Enter confirma
        
        dialog.wait_window()                                          # Espera cierre
        return resultado["pin"]                                       # Devuelve el PIN
    
    def abrir_admin(self):
        """Abre panel admin"""
        self.abrir_panel_admin()                                      # Delegado
    
    def abrir_panel_admin(self):
        """Abre el panel de administración"""
        # PAUSAR CÁMARA ANTES DE ABRIR
        self.pausar_camara()                                          # Detiene cámara
        
        from gui.admin_window import VentanaAdmin                     # Importa clase del panel
        admin_window = VentanaAdmin(self.root)                        # Instancia panel admin
        
        # Esperar a que se cierre el panel admin
        if admin_window.window:
            admin_window.window.wait_window()                         # Espera cierre de ventana
        
        # REANUDAR CÁMARA AL CERRAR
        self.reanudar_camara()                                        # Reinicia cámara
    
    def cerrar(self):
        """Cierra la aplicación"""
        self.camara_activa = False                                    # Detiene loop
        if self.cap:
            self.cap.release()                                        # Libera cámara
        
        # AGREGAR - Cerrar MediaPipe Hands
        if hasattr(self, 'hands'):
            self.hands.close()                                        # Cierra recursos de MediaPipe
        
        self.root.destroy()                                           # Cierra ventana principal

class VentanaSalida:
    """Ventana para registrar la salida del usuario"""
    
    def __init__(self, parent, nombre_usuario, user_id):
        self.parent = parent                                          # Ventana padre
        self.nombre_usuario = nombre_usuario                          # Nombre del usuario
        self.user_id = user_id                                        # ID del usuario
        
        self.dialog = tk.Toplevel(parent)                             # Crea ventana de salida
        self.dialog.title("Acceso Concedido")
        self.dialog.geometry("500x350")
        self.dialog.configure(bg=COLOR_BG)
        self.dialog.transient(parent)                                 # Sobre la principal
        self.dialog.grab_set()                                        # Bloquea la principal
        
        # Centrar ventana con respecto a la principal
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_x() + 450,
            parent.winfo_y() + 275
        ))
        
        self.setup_ui()                                               # Construye UI
        self.dialog.wait_window()                                     # Espera cierre
    
    def setup_ui(self):
        """Configura la interfaz"""
        
        # Título de bienvenida
        tk.Label(
            self.dialog,
            text="✅ ACCESO CONCEDIDO",
            font=("Arial", 20, "bold"),
            bg=COLOR_BG,
            fg=COLOR_SUCCESS
        ).pack(pady=20)
        
        # Nombre del usuario
        tk.Label(
            self.dialog,
            text=f"¡Bienvenido, {self.nombre_usuario}!",
            font=("Arial", 16),
            bg=COLOR_BG,
            fg=COLOR_TEXT
        ).pack(pady=10)
        
        # Separador
        ttk.Separator(self.dialog, orient="horizontal").pack(fill="x", pady=20)
        
        # Mensaje
        tk.Label(
            self.dialog,
            text="Presiona el botón para registrar tu salida",
            font=("Arial", 11),
            bg=COLOR_BG,
            fg=COLOR_TEXT_SECONDARY
        ).pack(pady=10)
        
        # Botón salir
        tk.Button(
            self.dialog,
            text="🚪 Registrar Salida",
            font=("Arial", 16, "bold"),
            bg=COLOR_WARNING,
            fg="white",
            command=self.solicitar_salida,                            # Abre diálogo de salida
            width=20,
            height=2
        ).pack(pady=30)
    
    def solicitar_salida(self):
        """Abre diálogo para registrar la salida"""
        dialog_salida = tk.Toplevel(self.dialog)                      # Ventana secundaria
        dialog_salida.title("Registrar Salida")
        dialog_salida.geometry("400x280")
        dialog_salida.configure(bg=COLOR_PANEL)
        dialog_salida.transient(self.dialog)                          # Sobre la de acceso concedido
        dialog_salida.grab_set()                                      # Bloquea interacción
        
        resultado = {"confirmado": False}                             # Contenedor del resultado
        
        tk.Label(
            dialog_salida,
            text="📤 Registrar Salida",
            font=("Arial", 16, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT
        ).pack(pady=20)
        
        # Nombre
        tk.Label(
            dialog_salida,
            text="Nombre:",
            font=("Arial", 11),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT
        ).pack(pady=5)
        
        entry_nombre = tk.Entry(
            dialog_salida,
            font=("Arial", 12),
            width=25
        )
        entry_nombre.pack(pady=5)
        entry_nombre.insert(0, self.nombre_usuario)                   # Pre-llenado con el nombre
        
        # PIN
        tk.Label(
            dialog_salida,
            text="PIN:",
            font=("Arial", 11),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT
        ).pack(pady=5)
        
        entry_pin = tk.Entry(
            dialog_salida,
            font=("Arial", 12),
            width=25,
            show="*"
        )
        entry_pin.pack(pady=5)
        entry_pin.focus()                                             # Foco en el PIN
        
        def confirmar_salida():
            nombre = entry_nombre.get().strip()                       # Lee nombre
            pin = entry_pin.get().strip()                             # Lee PIN
            
            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio", parent=dialog_salida)
                return
            
            if not pin:
                messagebox.showerror("Error", "El PIN es obligatorio", parent=dialog_salida)
                return
            
            # Verificar PIN y nombre
            try:
                from core import fetch_active_users_and_faces         # Import para obtener usuarios
                users, _ = fetch_active_users_and_faces()
            
                if self.user_id in users and nombre == users[self.user_id]["name"]: # Comprueba identidad
                    user_pin_hash = users[self.user_id]["pin"]        # Hash del PIN
                    
                    if bcrypt.checkpw(pin.encode(), user_pin_hash.encode()): # Verifica PIN
                        # PIN correcto - registrar salida
                        log_event(
                            self.user_id,
                            "salida",
                            f"Salida registrada: {nombre}"
                        )
                        
                        messagebox.showinfo(
                            "Éxito",
                            f"Salida registrada correctamente.\n¡Hasta luego, {nombre}!",
                            parent=dialog_salida
                        )
                        
                        resultado["confirmado"] = True                # Marca confirmación
                        dialog_salida.destroy()                       # Cierra secundario
                        self.dialog.destroy()                         # Cierra principal
                    else:
                        messagebox.showerror("Error", "PIN incorrecto", parent=dialog_salida)
                        entry_pin.delete(0, tk.END)                   # Limpia campo PIN
                        entry_pin.focus()
                else:
                    messagebox.showerror("Error", "Usuario no encontrado", parent=dialog_salida)
            
            except Exception as e:
                messagebox.showerror("Error", f"Error al verificar: {e}", parent=dialog_salida)
        
        # Botones de acción
        frame_botones = tk.Frame(dialog_salida, bg=COLOR_PANEL)
        frame_botones.pack(pady=20)
        
        tk.Button(
            frame_botones,
            text="✅ Confirmar",
            font=("Arial", 11),
            bg=COLOR_SUCCESS,
            fg="white",
            command=confirmar_salida,                                 # Ejecuta verificación y registro
            width=12
        ).pack(side="left", padx=5)
        
        tk.Button(
            frame_botones,
            text="❌ Cancelar",
            font=("Arial", 11),
            bg=COLOR_ERROR,
            fg="white",
            command=dialog_salida.destroy,                            # Cierra el diálogo
            width=12
        ).pack(side="left", padx=5)
        
        # Enter para confirmar
        entry_pin.bind("<Return>", lambda e: confirmar_salida())      # Atajo de teclado