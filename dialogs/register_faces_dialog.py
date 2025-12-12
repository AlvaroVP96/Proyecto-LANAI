# dialogs/register_faces_dialog.py
# --------------------------------------------
# Diálogo para registrar rostros faciales
# --------------------------------------------

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import time

from config import *
from core import get_all_users, insert_face, get_embedding_deepface


class RegistrarRostrosDialog:
    def __init__(self, parent):
        self.parent = parent
        self.resultado = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Registrar Rostros Faciales")
        self.dialog.geometry("900x750")
        self.dialog.configure(bg=COLOR_BG)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Variables
        self.cap = None
        self.usuario_seleccionado = None
        self.capturas = []
        self.max_capturas = 5
        self.capturando = False
        
        self.setup_ui()
        self.cargar_usuarios()
        self.iniciar_camara()
        
        self.dialog.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.dialog.wait_window()
        
    def setup_ui(self):
        """Configura la interfaz"""
        
        # Título
        tk.Label(
            self.dialog,
            text="📸 Registro de Rostros Faciales",
            font=("Arial", 20, "bold"),
            bg=COLOR_BG,
            fg=COLOR_TEXT
        ).pack(pady=15)
        
        # Frame principal
        frame_principal = tk.Frame(self.dialog, bg=COLOR_BG)
        frame_principal.pack(expand=True, fill="both", padx=20, pady=10)
        
        # Frame izquierdo - Cámara
        frame_camara = tk.Frame(frame_principal, bg=COLOR_PANEL, relief="raised", bd=3)
        frame_camara.pack(side="left", padx=10, fill="both", expand=True)
        
        tk.Label(
            frame_camara,
            text="Vista Previa",
            font=("Arial", 14, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT
        ).pack(pady=10)
        
        # Canvas para video
        self.canvas_video = tk.Canvas(
            frame_camara,
            width=640,
            height=480,
            bg="#000000"
        )
        self.canvas_video.pack(pady=10, padx=10)
        
        # Frame derecho - Controles
        frame_controles = tk.Frame(frame_principal, bg=COLOR_PANEL, relief="raised", bd=3)
        frame_controles.pack(side="right", padx=10, fill="both")
        
        # Selección de usuario
        tk.Label(
            frame_controles,
            text="Seleccionar Usuario:",
            font=("Arial", 12, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT
        ).pack(pady=(20, 10))
        
        self.combo_usuarios = ttk.Combobox(
            frame_controles,
            font=("Arial", 11),
            width=25,
            state="readonly"
        )
        self.combo_usuarios.pack(pady=10, padx=20)
        
        # Progreso
        tk.Label(
            frame_controles,
            text="Progreso:",
            font=("Arial", 11, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT
        ).pack(pady=(20, 5))
        
        self.label_progreso = tk.Label(
            frame_controles,
            text=f"0 / {self.max_capturas} fotos",
            font=("Arial", 14),
            bg=COLOR_PANEL,
            fg=COLOR_WARNING
        )
        self.label_progreso.pack(pady=5)
        
        self.progress_bar = ttk.Progressbar(
            frame_controles,
            length=200,
            mode='determinate'
        )
        self.progress_bar.pack(pady=10)
        
        # Botones
        self.btn_capturar = tk.Button(
            frame_controles,
            text="📷 Capturar Foto",
            font=("Arial", 14, "bold"),
            bg=COLOR_SUCCESS,
            fg="white",
            command=self.capturar_foto,
            width=20,
            height=2,
            state="disabled"
        )
        self.btn_capturar.pack(pady=20)
        
        self.btn_guardar = tk.Button(
            frame_controles,
            text="💾 Guardar Rostros",
            font=("Arial", 12, "bold"),
            bg=COLOR_INFO,
            fg="white",
            command=self.guardar_rostros,
            width=20,
            state="disabled"
        )
        self.btn_guardar.pack(pady=10)
        
        tk.Button(
            frame_controles,
            text="❌ Cancelar",
            font=("Arial", 10),
            bg=COLOR_ERROR,
            fg="white",
            command=self.cerrar,
            width=20
        ).pack(pady=10)
        
        # Instrucciones
        frame_inst = tk.Frame(frame_controles, bg=COLOR_PANEL)
        frame_inst.pack(pady=20, padx=15)
        
        tk.Label(
            frame_inst,
            text="💡 Consejos:",
            font=("Arial", 10, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT
        ).pack(anchor="w")
        
        instrucciones = [
            "• Buena iluminación",
            "• Mira a la cámara",
            "• Diferentes ángulos",
            "• Sin accesorios"
        ]
        
        for inst in instrucciones:
            tk.Label(
                frame_inst,
                text=inst,
                font=("Arial", 9),
                bg=COLOR_PANEL,
                fg=COLOR_TEXT_SECONDARY,
                anchor="w"
            ).pack(anchor="w", pady=2)
        
        # Bind evento selección
        self.combo_usuarios.bind("<<ComboboxSelected>>", self.usuario_seleccionado_changed)
        
    def cargar_usuarios(self):
        """Carga la lista de usuarios"""
        usuarios = get_all_users()
        nombres = [f"{u[1]} (ID: {u[0]})" for u in usuarios]
        self.combo_usuarios['values'] = nombres
        
        if nombres:
            self.combo_usuarios.current(0)
            self.usuario_seleccionado_changed()
    
    def usuario_seleccionado_changed(self, event=None):
        """Se ejecuta cuando se selecciona un usuario"""
        seleccion = self.combo_usuarios.get()
        if seleccion:
            # Extraer ID
            user_id = int(seleccion.split("ID: ")[1].rstrip(")"))
            self.usuario_seleccionado = user_id
            
            # Limpiar capturas previas
            self.capturas = []
            self.actualizar_progreso()
            
            # Habilitar botón
            self.btn_capturar.config(state="normal")
    
    def iniciar_camara(self):
        """Inicia la cámara"""
        self.cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.actualizar_video()
    
    def actualizar_video(self):
        """Actualiza el frame de video"""
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                
                # Dibujar marco de referencia
                h, w = frame.shape[:2]
                cv2.rectangle(frame, (w//4, h//4), (3*w//4, 3*h//4), (0, 255, 0), 2)
                cv2.putText(frame, "Centra tu rostro aqui", 
                           (w//4 + 10, h//4 - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img_tk = ImageTk.PhotoImage(image=img)
                
                self.canvas_video.create_image(0, 0, anchor="nw", image=img_tk)
                self.canvas_video.image = img_tk
        
        if hasattr(self, 'dialog') and self.dialog.winfo_exists():
            self.dialog.after(30, self.actualizar_video)
    
    def capturar_foto(self):
        """Captura una foto del usuario"""
        if self.capturando or not self.usuario_seleccionado:
            return
        
        if len(self.capturas) >= self.max_capturas:
            messagebox.showinfo("Información", 
                              f"Ya has capturado {self.max_capturas} fotos", 
                              parent=self.dialog)
            return
        
        self.capturando = True
        self.btn_capturar.config(state="disabled")
        
        # Countdown
        for i in range(3, 0, -1):
            self.label_progreso.config(text=f"Capturando en {i}...")
            self.dialog.update()
            time.sleep(1)
        
        # Capturar
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            self.capturas.append(frame.copy())
            self.actualizar_progreso()
            
            # Flash efecto
            self.canvas_video.config(bg="white")
            self.dialog.update()
            time.sleep(0.1)
            self.canvas_video.config(bg="black")
        
        self.capturando = False
        
        if len(self.capturas) < self.max_capturas:
            self.btn_capturar.config(state="normal")
        else:
            self.btn_guardar.config(state="normal")
    
    def actualizar_progreso(self):
        """Actualiza la barra de progreso"""
        num_capturas = len(self.capturas)
        self.label_progreso.config(text=f"{num_capturas} / {self.max_capturas} fotos")
        self.progress_bar['value'] = (num_capturas / self.max_capturas) * 100
        
        if num_capturas >= self.max_capturas:
            self.label_progreso.config(fg=COLOR_SUCCESS)
            self.btn_guardar.config(state="normal")
    
    def guardar_rostros(self):
        """Procesa y guarda los rostros en la BD"""
        if not self.capturas or not self.usuario_seleccionado:
            return
        
        self.btn_guardar.config(state="disabled", text="Procesando...")
        self.dialog.update()
        
        embeddings_guardados = 0
        errores = 0
        
        for i, frame in enumerate(self.capturas):
            try:
                self.label_progreso.config(
                    text=f"Procesando foto {i+1}/{len(self.capturas)}..."
                )
                self.dialog.update()
                
                # Obtener embedding
                embedding = get_embedding_deepface(frame)
                
                # Guardar en BD
                insert_face(self.usuario_seleccionado, embedding)
                embeddings_guardados += 1
                
            except Exception as e:
                print(f"Error procesando foto {i+1}: {e}")
                errores += 1
        
        # Resultado
        if embeddings_guardados > 0:
            self.resultado = embeddings_guardados
            messagebox.showinfo(
                "Éxito",
                f"✓ Rostros registrados: {embeddings_guardados}\n"
                f"✗ Errores: {errores}",
                parent=self.dialog
            )
            self.cerrar()
        else:
            messagebox.showerror(
                "Error",
                "No se pudo procesar ningún rostro.\n"
                "Intenta con mejor iluminación.",
                parent=self.dialog
            )
            self.btn_guardar.config(state="normal", text="💾 Guardar Rostros")
    
    def cerrar(self):
        """Cierra el diálogo y libera recursos"""
        if self.cap:
            self.cap.release()
        self.dialog.destroy()