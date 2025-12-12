# gui/access_window.py
# --------------------------------------------
# Ventana principal de acceso
# --------------------------------------------

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import cv2
from PIL import Image, ImageTk
import random
import time
import bcrypt

from config import *
from core import (
    fetch_active_users_and_faces,
    log_event,
    get_embedding_deepface,
    best_match_per_user,
    GestureDetector
)

import mediapipe as mp

class VentanaAcceso:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Control de Acceso")
        self.root.geometry("1400x900")
        self.root.configure(bg=COLOR_BG)
        
        # Variables
        self.cap = None
        self.verificando = False
        self.detector = GestureDetector()
        self.camara_activa = False
        
        self.frames_correctos = 0
        self.frames_necesarios = 30  # Número de frames consecutivos necesarios
        self.gesto_actual = None
        self.gesto_objetivo = None
        self.usuario_verificando = None
        
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.setup_ui()
        self.iniciar_video()
    
    def setup_ui(self):
        """Configura todos los elementos de la interfaz"""
        
        # Título
        titulo = tk.Label(
            self.root,
            text="SISTEMA DE CONTROL DE ACCESO",
            font=("Arial", 24, "bold"),
            bg=COLOR_BG,
            fg=COLOR_TEXT
        )
        titulo.pack(pady=20)
        
        # Frame principal
        frame_principal = tk.Frame(self.root, bg=COLOR_BG)
        frame_principal.pack(expand=True, fill="both", padx=20, pady=10)
        
        # Frame izquierdo - Cámara
        frame_camara = tk.Frame(frame_principal, bg=COLOR_PANEL, relief="raised", bd=3)
        frame_camara.pack(side="left", padx=10, fill="both", expand=True)
        
        tk.Label(
            frame_camara,
            text="Vista en Vivo",
            font=("Arial", 14, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT
        ).pack(pady=10)
        
        # Canvas para video
        self.canvas_video = tk.Canvas(
            frame_camara,
            width=CAMERA_WIDTH,
            height=CAMERA_HEIGHT,
            bg="#000000"
        )
        self.canvas_video.pack(pady=10, padx=10)
        
        # Frame derecho - Controles
        frame_controles = tk.Frame(frame_principal, bg=COLOR_PANEL, relief="raised", bd=3)
        frame_controles.pack(side="right", padx=10, fill="both")
        
        tk.Label(
            frame_controles,
            text="Panel de Control",
            font=("Arial", 14, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT
        ).pack(pady=20)
        
        # Botón verificar
        self.btn_verificar = tk.Button(
            frame_controles,
            text="🔐 VERIFICAR ACCESO",
            font=("Arial", 16, "bold"),
            bg=COLOR_SUCCESS,
            fg="white",
            activebackground="#229954",
            command=self.iniciar_verificacion,
            width=20,
            height=3
        )
        self.btn_verificar.pack(pady=20, padx=20)
        
        # Estado
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
        
        # Separador
        ttk.Separator(frame_controles, orient="horizontal").pack(fill="x", pady=20, padx=20)
        
        # Información del sistema
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
        
        # Botón admin
        self.btn_admin = tk.Button(
            frame_controles,
            text="⚙️ Panel Admin",
            font=("Arial", 10),
            bg=COLOR_INFO,
            fg="white",
            command=self.abrir_admin,
            width=20
        )
        self.btn_admin.pack(side="bottom", pady=20)
        
        # Actualizar info
        self.actualizar_info_sistema()
        
    def iniciar_video(self):
        """Inicia la captura de video"""
        if not self.cap or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_DSHOW)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self.camara_activa = True  
        self.actualizar_video()
    
    def pausar_camara(self):  
        """Pausa la cámara sin liberarla"""
        self.camara_activa = False
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None
        # Mostrar imagen de pausa en el canvas
        self.canvas_video.delete("all")
        self.canvas_video.create_text(
            CAMERA_WIDTH // 2,
            CAMERA_HEIGHT // 2,
            text="⏸️ CÁMARA PAUSADA\n\n(Panel de administración abierto)",
            font=("Arial", 20, "bold"),
            fill=COLOR_WARNING
        )
    
    def reanudar_camara(self): 
        """Reanuda la cámara"""
        if not self.camara_activa:
            self.iniciar_video()
    
    def actualizar_video(self):
        """Actualiza el video en tiempo real"""
        if not self.camara_activa:  
            return
        
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                if self.verificando:
                    frame = self.procesar_frame_gestos(frame)
                else:
                    frame = cv2.flip(frame, 1)
                
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img_tk = ImageTk.PhotoImage(image=img)
                
                self.canvas_video.create_image(0, 0, anchor="nw", image=img_tk)
                self.canvas_video.image = img_tk
        
        if self.camara_activa:  # <-- SOLO CONTINUAR SI ESTÁ ACTIVA
            self.root.after(30, self.actualizar_video)
    
    def procesar_frame_gestos(self, frame):
        """Procesa frame para gestos"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)
        
        gesto_correcto = False
        
        cv2.putText(frame, f"Gesto: {self.gesto_nombre}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0,255,0), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(0,255,255), thickness=2)
                )
                
                if self.detector.verificar_gesto(self.gesto_actual, hand_landmarks.landmark):
                    gesto_correcto = True
                    self.frames_correctos += 1
        
        if not gesto_correcto:
            self.frames_correctos = max(0, self.frames_correctos - 1)
        
        progreso = min(int((self.frames_correctos / self.frames_necesarios) * 100), 100)
        
        cv2.rectangle(frame, (10, 450), (630, 470), (50, 50, 50), -1)
        if progreso > 0:
            color = (0, 255, 0) if gesto_correcto else (255, 165, 0)
            cv2.rectangle(frame, (10, 450), (10 + int(progreso * 6.2), 470), color, -1)
        
        cv2.putText(frame, f"{progreso}%", (540, 465), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def verificacion_gesto_gui(self, timeout=GESTURE_TIMEOUT):
        """Verificación de gesto"""
        self.gesto_actual = random.choice(list(self.detector.gestos_disponibles.keys()))
        self.gesto_nombre = self.detector.gestos_disponibles[self.gesto_actual]
        self.frames_correctos = 0
        self.modo_normal = False
        
        start_time = time.time()
        
        while True:
            if time.time() - start_time > timeout:
                self.modo_normal = True
                self.gesto_actual = None
                raise TimeoutError("Tiempo agotado")
            
            if self.frames_correctos >= self.frames_necesarios:
                time.sleep(0.5)
                self.modo_normal = True
                self.gesto_actual = None
                return True
            
            time.sleep(0.1)
            self.root.update()
    
    def actualizar_info_sistema(self):
        """Actualiza info del sistema"""
        users, faces = fetch_active_users_and_faces()
        self.label_usuarios.config(text=str(len(users)))
        
    def cambiar_estado(self, texto, color=COLOR_WARNING):
        """Cambia estado"""
        self.label_estado.config(text=texto, fg=color)
        self.root.update()
        
    def iniciar_verificacion(self):
        """Inicia verificación"""
        if self.verificando:
            messagebox.showwarning("Aviso", "Verificación en curso")
            return
        
        self.btn_verificar.config(state="disabled", bg="#95A5A6")
        self.verificando = True
        
        thread = threading.Thread(target=self.proceso_verificacion, daemon=True)
        thread.start()
    
    def proceso_verificacion(self):
        """Proceso de verificación completo"""
        try:
            self.cambiar_estado("Cargando...", COLOR_INFO)
            users, faces = fetch_active_users_and_faces()
            
            if not users:
                messagebox.showerror("Error", "No hay usuarios")
                return
            
            # Gesto
            self.cambiar_estado("Paso 1/4: Gesto", COLOR_WARNING)
            try:
                if not self.verificacion_gesto_gui():
                    log_event(None, "Entrada Denegada", "Gesto fallido")
                    messagebox.showerror("Denegado", "Gesto fallido")
                    return
            except TimeoutError:
                log_event(None, "Entrada Denegada", "Tiempo para gesto agotado")
                messagebox.showerror("Error", "Tiempo agotado")
                return
            
            # Captura
            self.cambiar_estado("Paso 2/4: Captura", COLOR_WARNING)
            time.sleep(1)
            
            ret, frame = self.cap.read()
            if not ret:
                messagebox.showerror("Error", "Captura fallida")
                return
            
            frame = cv2.flip(frame, 1)
            
            # Reconocimiento
            self.cambiar_estado("Paso 3/4: Reconociendo", COLOR_WARNING)
            
            try:
                query_emb = get_embedding_deepface(frame)
            except:
                log_event(None, "Entrada Denegada", "No se detecto Rostro")
                messagebox.showerror("Error", "Sin rostro")
                return
            
            best_uid, best_score = best_match_per_user(query_emb, faces)
            
            if best_uid is None or best_score < FACE_THRESHOLD:
                log_event(None, "Entrada Denegada", f"No reconocido: {best_score:.3f}")
                messagebox.showerror("Denegado", f"Desconocido\nScore: {best_score:.3f}")
                return
            
            # PIN
            user = users.get(best_uid)
            self.cambiar_estado(f"Usuario: {user['name']}", COLOR_INFO)
            
            pin = self.solicitar_pin(user['name'])
            if not pin:
                return
            
            if bcrypt.checkpw(pin.encode(), user["pin"].encode()):
                self.cambiar_estado("PERMITIDO", COLOR_SUCCESS)
                log_event(best_uid, "Entrada Permitida", f"Acceso Permitido: {user['name']} || score={best_score:.3f}")
               
                VentanaSalida(self.root, user['name'], best_uid)    
            else:
                log_event(best_uid, "Entrada Denegada", "Pin Incorrecto")
                messagebox.showerror("Denegado", "PIN incorrecto")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
        finally:
            self.verificando = False
            self.modo_normal = True
            self.gesto_actual = None
            self.btn_verificar.config(state="normal", bg=COLOR_SUCCESS)
            self.cambiar_estado("Esperando...", COLOR_WARNING)
    
    def solicitar_pin(self, nombre):
        """Diálogo PIN"""
        dialog = tk.Toplevel(self.root)
        dialog.title("PIN")
        dialog.geometry("350x200")
        dialog.configure(bg=COLOR_PANEL)
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.geometry("+%d+%d" % (self.root.winfo_x() + 275, self.root.winfo_y() + 250))
        
        resultado = {"pin": None}
        
        tk.Label(dialog, text=f"Usuario: {nombre}", font=("Arial", 12, "bold"),
                bg=COLOR_PANEL, fg=COLOR_TEXT).pack(pady=20)
        
        tk.Label(dialog, text="PIN:", font=("Arial", 10),
                bg=COLOR_PANEL, fg=COLOR_TEXT_SECONDARY).pack(pady=5)
        
        entry_pin = tk.Entry(dialog, show="*", font=("Arial", 14), width=15)
        entry_pin.pack(pady=10)
        entry_pin.focus()
        
        def confirmar():
            resultado["pin"] = entry_pin.get()
            dialog.destroy()
        
        frame_btns = tk.Frame(dialog, bg=COLOR_PANEL)
        frame_btns.pack(pady=20)
        
        tk.Button(frame_btns, text="OK", command=confirmar,
                 bg=COLOR_SUCCESS, fg="white", width=10).pack(side="left", padx=5)
        tk.Button(frame_btns, text="Cancelar", command=dialog.destroy,
                 bg=COLOR_ERROR, fg="white", width=10).pack(side="left", padx=5)
        
        entry_pin.bind("<Return>", lambda e: confirmar())
        
        dialog.wait_window()
        return resultado["pin"]
    
    def abrir_admin(self):
        """Abre panel admin"""
        self.abrir_panel_admin()
    
    def abrir_panel_admin(self):
        """Abre el panel de administración"""
        # PAUSAR CÁMARA ANTES DE ABRIR
        self.pausar_camara()
        
        from gui.admin_window import VentanaAdmin
        admin_window = VentanaAdmin(self.root)
        
        # Esperar a que se cierre el panel admin
        if admin_window.window:
            admin_window.window.wait_window()
        
        # REANUDAR CÁMARA AL CERRAR
        self.reanudar_camara()
    
    def cerrar(self):
        """Cierra la aplicación"""
        self.camara_activa = False
        if self.cap:
            self.cap.release()
        
        # AGREGAR - Cerrar MediaPipe Hands
        if hasattr(self, 'hands'):
            self.hands.close()
        
        self.root.destroy()

class VentanaSalida:
    """Ventana para registrar la salida del usuario"""
    
    def __init__(self, parent, nombre_usuario, user_id):
        self.parent = parent
        self.nombre_usuario = nombre_usuario
        self.user_id = user_id
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Acceso Concedido")
        self.dialog.geometry("500x350")
        self.dialog.configure(bg=COLOR_BG)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrar ventana
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_x() + 450,
            parent.winfo_y() + 275
        ))
        
        self.setup_ui()
        self.dialog.wait_window()
    
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
            command=self.solicitar_salida,
            width=20,
            height=2
        ).pack(pady=30)
    
    def solicitar_salida(self):
        """Abre diálogo para registrar la salida"""
        dialog_salida = tk.Toplevel(self.dialog)
        dialog_salida.title("Registrar Salida")
        dialog_salida.geometry("400x280")
        dialog_salida.configure(bg=COLOR_PANEL)
        dialog_salida.transient(self.dialog)
        dialog_salida.grab_set()
        
        resultado = {"confirmado": False}
        
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
        entry_nombre.insert(0, self.nombre_usuario)  # Pre-llenar con nombre
        
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
        entry_pin.focus()
        
        def confirmar_salida():
            nombre = entry_nombre.get().strip()
            pin = entry_pin.get().strip()
            
            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio", parent=dialog_salida)
                return
            
            if not pin:
                messagebox.showerror("Error", "El PIN es obligatorio", parent=dialog_salida)
                return
            
            # Verificar PIN y nombre
            try:
                from core import fetch_active_users_and_faces
                users, _ = fetch_active_users_and_faces()
            
                if self.user_id in users and nombre == users[self.user_id]["name"]:
                    user_pin_hash = users[self.user_id]["pin"]
                    
                    if bcrypt.checkpw(pin.encode(), user_pin_hash.encode()):
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
                        
                        resultado["confirmado"] = True
                        dialog_salida.destroy()
                        self.dialog.destroy()
                    else:
                        messagebox.showerror("Error", "PIN incorrecto", parent=dialog_salida)
                        entry_pin.delete(0, tk.END)
                        entry_pin.focus()
                else:
                    messagebox.showerror("Error", "Usuario no encontrado", parent=dialog_salida)
            
            except Exception as e:
                messagebox.showerror("Error", f"Error al verificar: {e}", parent=dialog_salida)
        
        # Botones
        frame_botones = tk.Frame(dialog_salida, bg=COLOR_PANEL)
        frame_botones.pack(pady=20)
        
        tk.Button(
            frame_botones,
            text="✅ Confirmar",
            font=("Arial", 11),
            bg=COLOR_SUCCESS,
            fg="white",
            command=confirmar_salida,
            width=12
        ).pack(side="left", padx=5)
        
        tk.Button(
            frame_botones,
            text="❌ Cancelar",
            font=("Arial", 11),
            bg=COLOR_ERROR,
            fg="white",
            command=dialog_salida.destroy,
            width=12
        ).pack(side="left", padx=5)
        
        # Enter para confirmar
        entry_pin.bind("<Return>", lambda e: confirmar_salida())