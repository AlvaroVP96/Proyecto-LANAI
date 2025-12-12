# gui/admin_window.py
# --------------------------------------------
# Panel de administración simplificado
# --------------------------------------------
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import cv2
from PIL import Image, ImageTk
import bcrypt
import time

from config import *
from core import (
    ensure_schema,
    get_all_users,
    update_user_status,
    delete_user,
    get_recent_events,
    insert_user,
    insert_face,
    get_embedding_deepface,
    log_event
)
from utils.admin_auth import verificar_admin


class VentanaAdmin:
    def __init__(self, parent):
        self.parent = parent
        
        # Verificar autenticación
        if not verificar_admin(parent):
            self.window = None
            return
        
        self.window = tk.Toplevel(parent)
        self.window.title("Panel de Administración")
        self.window.geometry("1200x800")
        self.window.configure(bg=COLOR_BG)
        
        # Variables
        self.usuarios_data = []
        self.cap_registro = None  # <-- Cámara para registro
        self.camara_registro_activa = False  # <-- Estado de cámara de registro
        
        self.setup_ui()
        self.cargar_usuarios()
        self.cargar_eventos()
        
        self.window.protocol("WM_DELETE_WINDOW", self.cerrar)
    
    def setup_ui(self):
        """Configura la interfaz"""
        # Título
        tk.Label(
            self.window,
            text="⚙️ PANEL DE ADMINISTRACIÓN",
            font=("Arial", 24, "bold"),
            bg=COLOR_BG,
            fg=COLOR_TEXT
        ).pack(pady=20)
        
        # Tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill="both", padx=20, pady=10)
        
        # Tab 1: Usuarios
        self.tab_usuarios = tk.Frame(self.notebook, bg=COLOR_PANEL)
        self.notebook.add(self.tab_usuarios, text="👥 Usuarios")
        
        # Tab 2: Historial
        self.tab_historial = tk.Frame(self.notebook, bg=COLOR_PANEL)
        self.notebook.add(self.tab_historial, text="📊 Historial")
        
        self.setup_tab_usuarios()
        self.setup_tab_historial()
    
    # ==================== TAB USUARIOS ====================
    
    def setup_tab_usuarios(self):
        """Configura la pestaña de usuarios"""
        # Frame superior - Botones
        frame_botones = tk.Frame(self.tab_usuarios, bg=COLOR_PANEL)
        frame_botones.pack(pady=20, fill="x", padx=20)
        
        tk.Button(
            frame_botones,
            text="➕ Registrar Nuevo Usuario",
            font=("Arial", 14, "bold"),
            bg=COLOR_SUCCESS,
            fg="white",
            command=self.registrar_nuevo_usuario,
            width=25,
            height=2
        ).pack(side="left", padx=10)
        
        tk.Button(
            frame_botones,
            text="🔄 Actualizar Lista",
            font=("Arial", 12),
            bg=COLOR_INFO,
            fg="white",
            command=self.cargar_usuarios,
            width=20
        ).pack(side="left", padx=10)
        
        # Frame tabla
        frame_tabla = tk.Frame(self.tab_usuarios, bg=COLOR_PANEL)
        frame_tabla.pack(expand=True, fill="both", padx=20, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_tabla)
        scrollbar.pack(side="right", fill="y")
        
        # Treeview
        columns = ("ID", "Nombre", "Rostros", "Estado", "Fecha Registro")
        self.tree_usuarios = ttk.Treeview(
            frame_tabla,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar.set,
            height=15
        )
        
        # Configurar columnas
        self.tree_usuarios.heading("ID", text="ID")
        self.tree_usuarios.heading("Nombre", text="Nombre")
        self.tree_usuarios.heading("Rostros", text="Rostros Registrados")
        self.tree_usuarios.heading("Estado", text="Estado")
        self.tree_usuarios.heading("Fecha Registro", text="Fecha de Registro")
        
        self.tree_usuarios.column("ID", width=50, anchor="center")
        self.tree_usuarios.column("Nombre", width=200)
        self.tree_usuarios.column("Rostros", width=150, anchor="center")
        self.tree_usuarios.column("Estado", width=100, anchor="center")
        self.tree_usuarios.column("Fecha Registro", width=150, anchor="center")
        
        self.tree_usuarios.pack(expand=True, fill="both")
        scrollbar.config(command=self.tree_usuarios.yview)
        
        # Botones de acción
        frame_acciones = tk.Frame(self.tab_usuarios, bg=COLOR_PANEL)
        frame_acciones.pack(pady=10)
        
        tk.Button(
            frame_acciones,
            text="🗑️ Eliminar Usuario",
            font=("Arial", 11),
            bg=COLOR_ERROR,
            fg="white",
            command=self.eliminar_usuario,
            width=20
        ).pack(side="left", padx=5)
        
        tk.Button(
            frame_acciones,
            text="🔒 Activar/Desactivar",
            font=("Arial", 11),
            bg=COLOR_WARNING,
            fg="white",
            command=self.toggle_usuario,
            width=20
        ).pack(side="left", padx=5)
    
    def cargar_usuarios(self):
        """Carga la lista de usuarios"""
        # Limpiar tabla
        for item in self.tree_usuarios.get_children():
            self.tree_usuarios.delete(item)
        
        # Obtener usuarios
        usuarios = get_all_users()
        self.usuarios_data = usuarios
        
        # Agregar a la tabla
        for usuario in usuarios:
            user_id, nombre, pin, active, created_at = usuario
            
            # Contar rostros manualmente desde la BD
            import sqlite3
            from config import DB_PATH
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM faces WHERE user_id = ?", (user_id,))
            num_rostros = c.fetchone()[0]
            conn.close()
            
            estado = "✅ Activo" if active else "❌ Inactivo"
            rostros_text = f"{num_rostros} rostros" if num_rostros else "Sin rostros"
            
            # CORREGIR MANEJO DE FECHA
            if isinstance(created_at, str):
                fecha = created_at[:10]  # Ya es string
            else:
                # Si es timestamp o None
                fecha = str(created_at) if created_at else "N/A"
            
            self.tree_usuarios.insert(
                "",
                "end",
                values=(user_id, nombre, rostros_text, estado, fecha)
            )
    
    def eliminar_usuario(self):
        """Elimina un usuario seleccionado"""
        seleccion = self.tree_usuarios.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un usuario primero")
            return
        
        item = self.tree_usuarios.item(seleccion[0])
        user_id = item['values'][0]
        nombre = item['values'][1]
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar usuario '{nombre}'?\n\nEsta acción no se puede deshacer."):
            try:
                delete_user(user_id)
                messagebox.showinfo("Éxito", f"Usuario '{nombre}' eliminado correctamente")
                self.cargar_usuarios()
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar usuario: {e}")
    
    def toggle_usuario(self):
        """Activa/desactiva un usuario"""
        seleccion = self.tree_usuarios.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un usuario primero")
            return
        
        item = self.tree_usuarios.item(seleccion[0])
        user_id = item['values'][0]
        nombre = item['values'][1]
        estado_actual = "✅ Activo" in item['values'][3]
        
        nuevo_estado = 0 if estado_actual else 1
        accion = "desactivar" if estado_actual else "activar"
        
        if messagebox.askyesno("Confirmar", f"¿{accion.capitalize()} usuario '{nombre}'?"):
            try:
                update_user_status(user_id, nuevo_estado)
                messagebox.showinfo("Éxito", f"Usuario '{nombre}' {accion}do correctamente")
                self.cargar_usuarios()
            except Exception as e:
                messagebox.showerror("Error", f"Error al {accion} usuario: {e}")
    
    # ==================== REGISTRO NUEVO USUARIO ====================
    
    def registrar_nuevo_usuario(self):
        """Inicia el proceso de registro de nuevo usuario"""
        # Crear ventana de registro
        self.dialog_registro = tk.Toplevel(self.window)
        self.dialog_registro.title("Registrar Nuevo Usuario")
        self.dialog_registro.geometry("900x700")
        self.dialog_registro.configure(bg=COLOR_BG)
        self.dialog_registro.transient(self.window)
        self.dialog_registro.grab_set()
        
        # Variables del proceso
        self.nombre_usuario = None
        self.capturas_rostro = []
        self.embeddings_rostro = []
        self.pin_usuario = None
        self.cap_registro = None
        self.paso_actual = 1  # 1: Nombre, 2: Captura rostros, 3: PIN, 4: Guardar
        
        self.setup_dialogo_registro()
        
        self.dialog_registro.protocol("WM_DELETE_WINDOW", self.cerrar_registro)
    
    def setup_dialogo_registro(self):
        """Configura el diálogo de registro"""
        # Título
        self.label_titulo_registro = tk.Label(
            self.dialog_registro,
            text="📝 PASO 1: Nombre del Usuario",
            font=("Arial", 20, "bold"),
            bg=COLOR_BG,
            fg=COLOR_TEXT
        )
        self.label_titulo_registro.pack(pady=20)
        
        # Frame contenido (cambiará según el paso)
        self.frame_contenido = tk.Frame(self.dialog_registro, bg=COLOR_BG)
        self.frame_contenido.pack(expand=True, fill="both", padx=40, pady=20)
        
        # Mostrar paso 1
        self.mostrar_paso_nombre()
    
    # ========== PASO 1: NOMBRE ==========
    
    def mostrar_paso_nombre(self):
        """Muestra el formulario para ingresar nombre"""
        # Limpiar frame
        for widget in self.frame_contenido.winfo_children():
            widget.destroy()
        
        tk.Label(
            self.frame_contenido,
            text="Introduce el nombre completo del usuario:",
            font=("Arial", 14),
            bg=COLOR_BG,
            fg=COLOR_TEXT
        ).pack(pady=20)
        
        self.entry_nombre = tk.Entry(
            self.frame_contenido,
            font=("Arial", 16),
            width=30
        )
        self.entry_nombre.pack(pady=10)
        self.entry_nombre.focus()
        
        tk.Button(
            self.frame_contenido,
            text="➡️ Continuar",
            font=("Arial", 14, "bold"),
            bg=COLOR_SUCCESS,
            fg="white",
            command=self.validar_nombre,
            width=20,
            height=2
        ).pack(pady=30)
        
        self.entry_nombre.bind("<Return>", lambda e: self.validar_nombre())
    
    def validar_nombre(self):
        """Valida el nombre y pasa al siguiente paso"""
        nombre = self.entry_nombre.get().strip()
        
        if not nombre:
            messagebox.showerror("Error", "El nombre es obligatorio", parent=self.dialog_registro)
            return
        
        if len(nombre) < 3:
            messagebox.showerror("Error", "El nombre debe tener al menos 3 caracteres", parent=self.dialog_registro)
            return
        
        self.nombre_usuario = nombre
        self.paso_actual = 2
        self.label_titulo_registro.config(text="📸 PASO 2: Captura de Rostros")
        self.mostrar_paso_rostros()
    
    # ========== PASO 2: CAPTURA ROSTROS ==========
    
    def actualizar_video_registro(self):
        """Actualiza el video en tiempo real"""
        if self.cap_registro and self.cap_registro.isOpened() and self.camara_registro_activa:
            ret, frame = self.cap_registro.read()
            if ret:
                frame = cv2.flip(frame, 1)
                
                # Dibujar guía
                h, w = frame.shape[:2]
                cv2.rectangle(frame, (w//4, h//4), (3*w//4, 3*h//4), (0, 255, 0), 2)
                cv2.putText(frame, "Centra tu rostro aqui", 
                           (w//4 + 10, h//4 - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img_tk = ImageTk.PhotoImage(image=img)
                
                self.canvas_registro.create_image(0, 0, anchor="nw", image=img_tk)
                self.canvas_registro.image = img_tk
        
        if hasattr(self, 'dialog_registro') and self.dialog_registro.winfo_exists() and self.camara_registro_activa:
            self.dialog_registro.after(30, self.actualizar_video_registro)
    
    def mostrar_paso_rostros(self):
        """Muestra la interfaz de captura de rostros"""
        # Limpiar frame
        for widget in self.frame_contenido.winfo_children():
            widget.destroy()
        
        # Instrucciones
        tk.Label(
            self.frame_contenido,
            text=f"Capturando rostros para: {self.nombre_usuario}",
            font=("Arial", 14, "bold"),
            bg=COLOR_BG,
            fg=COLOR_TEXT
        ).pack(pady=10)
        
        tk.Label(
            self.frame_contenido,
            text="Captura 5 fotos desde diferentes ángulos",
            font=("Arial", 12),
            bg=COLOR_BG,
            fg=COLOR_TEXT_SECONDARY
        ).pack(pady=5)
        
        # Canvas para video
        self.canvas_registro = tk.Canvas(
            self.frame_contenido,
            width=640,
            height=480,
            bg="#000000"
        )
        self.canvas_registro.pack(pady=20)
        
        # Progreso
        self.label_progreso = tk.Label(
            self.frame_contenido,
            text="0 / 5 fotos capturadas",
            font=("Arial", 14),
            bg=COLOR_BG,
            fg=COLOR_WARNING
        )
        self.label_progreso.pack(pady=10)
        
        # Botón capturar
        self.btn_capturar = tk.Button(
            self.frame_contenido,
            text="📷 Capturar Foto",
            font=("Arial", 14, "bold"),
            bg=COLOR_SUCCESS,
            fg="white",
            command=self.capturar_rostro,
            width=20,
            height=2
        )
        self.btn_capturar.pack(pady=10)
        
        # Iniciar cámara de registro
        if not self.cap_registro or not self.cap_registro.isOpened():
            self.cap_registro = cv2.VideoCapture(CAMERA_ID, cv2.CAP_DSHOW)
            self.cap_registro.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap_registro.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.camara_registro_activa = True  # <-- ACTIVAR CÁMARA
        self.actualizar_video_registro()
    
    def capturar_rostro(self):
        """Captura una foto del rostro"""
        if len(self.capturas_rostro) >= 5:
            return
        
        self.btn_capturar.config(state="disabled")
        
        # Countdown
        for i in range(3, 0, -1):
            self.label_progreso.config(text=f"Capturando en {i}...")
            self.dialog_registro.update()
            time.sleep(1)
        
        # Capturar
        ret, frame = self.cap_registro.read()
        if ret:
            frame = cv2.flip(frame, 1)
            self.capturas_rostro.append(frame.copy())
            
            # Actualizar progreso
            num = len(self.capturas_rostro)
            self.label_progreso.config(text=f"{num} / 5 fotos capturadas")
            
            # Flash
            self.canvas_registro.config(bg="white")
            self.dialog_registro.update()
            time.sleep(0.1)
            self.canvas_registro.config(bg="black")
            
            if num >= 5:
                self.label_progreso.config(fg=COLOR_SUCCESS)
                self.btn_capturar.config(text="✅ Completado", state="disabled")
                
                # Botón continuar
                tk.Button(
                    self.frame_contenido,
                    text="➡️ Verificar y Continuar",
                    font=("Arial", 12, "bold"),
                    bg=COLOR_INFO,
                    fg="white",
                    command=self.verificar_rostros,
                    width=20
                ).pack(pady=10)
            else:
                self.btn_capturar.config(state="normal")
    
    def verificar_rostros(self):
        """Verifica que los rostros se detectaron correctamente"""
        self.btn_capturar.config(state="disabled")
        self.label_progreso.config(text="Verificando rostros...")
        self.dialog_registro.update()
        
        embeddings_ok = 0
        
        for frame in self.capturas_rostro:
            try:
                embedding = get_embedding_deepface(frame)
                self.embeddings_rostro.append(embedding)
                embeddings_ok += 1
            except Exception as e:
                print(f"Error al procesar rostro: {e}")
        
        if embeddings_ok >= 3:  # Al menos 3 rostros válidos
            messagebox.showinfo(
                "Éxito",
                f"✅ {embeddings_ok} rostros verificados correctamente",
                parent=self.dialog_registro
            )
            self.cerrar_camara_registro()
            self.paso_actual = 3
            self.label_titulo_registro.config(text="🔢 PASO 3: PIN de Seguridad")
            self.mostrar_paso_pin()
        else:
            messagebox.showerror(
                "Error",
                f"Solo se detectaron {embeddings_ok} rostros válidos.\nIntenta de nuevo con mejor iluminación.",
                parent=self.dialog_registro
            )
            self.capturas_rostro = []
            self.embeddings_rostro = []
            self.mostrar_paso_rostros()
    
    # ========== PASO 3: PIN ==========
    
    def mostrar_paso_pin(self):
        """Muestra el formulario para ingresar PIN"""
        # Limpiar frame
        for widget in self.frame_contenido.winfo_children():
            widget.destroy()
        
        tk.Label(
            self.frame_contenido,
            text="Configura un PIN de 4 dígitos:",
            font=("Arial", 14),
            bg=COLOR_BG,
            fg=COLOR_TEXT
        ).pack(pady=20)
        
        tk.Label(
            self.frame_contenido,
            text="PIN:",
            font=("Arial", 12),
            bg=COLOR_BG,
            fg=COLOR_TEXT_SECONDARY
        ).pack(pady=5)
        
        self.entry_pin = tk.Entry(
            self.frame_contenido,
            font=("Arial", 16),
            width=15,
            show="*"
        )
        self.entry_pin.pack(pady=10)
        self.entry_pin.focus()
        
        tk.Label(
            self.frame_contenido,
            text="Confirmar PIN:",
            font=("Arial", 12),
            bg=COLOR_BG,
            fg=COLOR_TEXT_SECONDARY
        ).pack(pady=5)
        
        self.entry_pin_confirm = tk.Entry(
            self.frame_contenido,
            font=("Arial", 16),
            width=15,
            show="*"
        )
        self.entry_pin_confirm.pack(pady=10)
        
        tk.Button(
            self.frame_contenido,
            text="✅ Guardar Usuario",
            font=("Arial", 14, "bold"),
            bg=COLOR_SUCCESS,
            fg="white",
            command=self.guardar_usuario,
            width=20,
            height=2
        ).pack(pady=30)
        
        self.entry_pin.bind("<Return>", lambda e: self.entry_pin_confirm.focus())
        self.entry_pin_confirm.bind("<Return>", lambda e: self.guardar_usuario())
    
    def guardar_usuario(self):
        """Valida el PIN y guarda el usuario en la BD"""
        pin = self.entry_pin.get().strip()
        pin_confirm = self.entry_pin_confirm.get().strip()
        
        # Validaciones
        if not pin or not pin.isdigit() or len(pin) != 4:
            messagebox.showerror("Error", "El PIN debe ser 4 dígitos numéricos", parent=self.dialog_registro)
            return
        
        if pin != pin_confirm:
            messagebox.showerror("Error", "Los PINs no coinciden", parent=self.dialog_registro)
            return
        
        # Encriptar PIN
        pin_hash = bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()
        
        try:
            # Guardar usuario
            user_id = insert_user(self.nombre_usuario, pin_hash)
            
            # Guardar rostros
            for embedding in self.embeddings_rostro:
                insert_face(user_id, embedding)
            
            # Log
            log_event(user_id, "granted", "Usuario registrado desde panel admin")
            
            messagebox.showinfo(
                "Éxito",
                f"✅ Usuario '{self.nombre_usuario}' registrado correctamente\n\n"
                f"Rostros guardados: {len(self.embeddings_rostro)}",
                parent=self.dialog_registro
            )
            
            self.cerrar_registro()
            self.cargar_usuarios()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar usuario:\n{e}", parent=self.dialog_registro)
    
    def cerrar_camara_registro(self):
        """Cierra la cámara del registro"""
        self.camara_registro_activa = False  # <-- DESACTIVAR PRIMERO
        if self.cap_registro:
            self.cap_registro.release()
            self.cap_registro = None
    
    def cerrar_registro(self):
        """Cierra el diálogo de registro"""
        self.cerrar_camara_registro()
        if hasattr(self, 'dialog_registro') and self.dialog_registro.winfo_exists():
            self.dialog_registro.destroy()
    
    # ==================== TAB HISTORIAL ====================
    
    def setup_tab_historial(self):
        """Configura la pestaña de historial"""
        # Frame superior
        frame_top = tk.Frame(self.tab_historial, bg=COLOR_PANEL)
        frame_top.pack(pady=20, fill="x", padx=20)
        
        tk.Label(
            frame_top,
            text="Eventos recientes:",
            font=("Arial", 14, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT
        ).pack(side="left")
        
        tk.Button(
            frame_top,
            text="🔄 Actualizar",
            font=("Arial", 11),
            bg=COLOR_INFO,
            fg="white",
            command=self.cargar_eventos,
            width=15
        ).pack(side="right", padx=5)
        
        tk.Button(
            frame_top,
            text="📥 Exportar CSV",
            font=("Arial", 11),
            bg=COLOR_SUCCESS,
            fg="white",
            command=self.exportar_csv,
            width=15
        ).pack(side="right", padx=5)
        
        # Frame tabla
        frame_tabla = tk.Frame(self.tab_historial, bg=COLOR_PANEL)
        frame_tabla.pack(expand=True, fill="both", padx=20, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_tabla)
        scrollbar.pack(side="right", fill="y")
        
        # Treeview
        columns = ("Fecha/Hora", "Usuario", "Resultado", "Notas")
        self.tree_eventos = ttk.Treeview(
            frame_tabla,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar.set,
            height=20
        )
        
        self.tree_eventos.heading("Fecha/Hora", text="Fecha/Hora")
        self.tree_eventos.heading("Usuario", text="Usuario")
        self.tree_eventos.heading("Resultado", text="Resultado")
        self.tree_eventos.heading("Notas", text="Notas")
        
        self.tree_eventos.column("Fecha/Hora", width=180)
        self.tree_eventos.column("Usuario", width=200)
        self.tree_eventos.column("Resultado", width=120, anchor="center")
        self.tree_eventos.column("Notas", width=400)
        
        self.tree_eventos.pack(expand=True, fill="both")
        scrollbar.config(command=self.tree_eventos.yview)
    
    def cargar_eventos(self):
        """Carga el historial de eventos"""
        # Limpiar tabla
        for item in self.tree_eventos.get_children():
            self.tree_eventos.delete(item)
        
        # Obtener eventos
        eventos = get_recent_events(100)
        
        # Agregar a la tabla
        for evento in eventos:
            event_id, ts, device, user_id, result, note = evento
            
            # Obtener nombre de usuario
            usuario_nombre = "Desconocido"
            for user in self.usuarios_data:
                if user[0] == user_id:
                    usuario_nombre = user[1]
                    break
            
            resultado = "✅ Concedido" if result == "granted" else "❌ Denegado"
            
            self.tree_eventos.insert(
                "",
                "end",
                values=(ts, usuario_nombre, resultado, note or "")
            )
    
    def exportar_csv(self):
        """Exporta el historial a CSV"""
        archivo = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"historial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if archivo:
            try:
                import csv
                eventos = get_recent_events(1000)
                
                with open(archivo, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Fecha/Hora", "Dispositivo", "Usuario ID", "Resultado", "Notas"])
                    
                    for evento in eventos:
                        event_id, ts, device, user_id, result, note = evento
                        writer.writerow([ts, device, user_id, result, note or ""])
                
                messagebox.showinfo("Éxito", f"Historial exportado a:\n{archivo}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar: {e}")
    
    def cerrar(self):
        """Cierra la ventana de administración"""
        # Asegurar que se cierra la cámara de registro si está abierta
        self.cerrar_camara_registro()
        
        # Cerrar diálogo de registro si está abierto
        if hasattr(self, 'dialog_registro') and self.dialog_registro.winfo_exists():
            self.dialog_registro.destroy()
        
        # Cerrar ventana principal
        if self.window:
            self.window.destroy()