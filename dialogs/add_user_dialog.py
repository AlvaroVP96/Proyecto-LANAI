# dialogs/add_user_dialog.py
# --------------------------------------------
# Diálogo para agregar nuevo usuario
# --------------------------------------------

import tkinter as tk
from tkinter import messagebox
import bcrypt

from config import COLOR_PANEL, COLOR_TEXT, COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR
from core import insert_user


class AgregarUsuarioDialog:
    def __init__(self, parent):
        self.parent = parent
        self.resultado = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Agregar Nuevo Usuario")
        self.dialog.geometry("450x350")
        self.dialog.configure(bg=COLOR_PANEL)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrar ventana
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_x() + 400,
            parent.winfo_y() + 200
        ))
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del diálogo"""
        
        # Título
        tk.Label(
            self.dialog,
            text="➕ Nuevo Usuario",
            font=("Arial", 18, "bold"),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT
        ).pack(pady=20)
        
        # Frame formulario
        frame_form = tk.Frame(self.dialog, bg=COLOR_PANEL)
        frame_form.pack(pady=20, padx=40, fill="both", expand=True)
        
        # Nombre
        tk.Label(
            frame_form,
            text="Nombre completo:",
            font=("Arial", 11),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT_SECONDARY,
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        self.entry_nombre = tk.Entry(
            frame_form,
            font=("Arial", 12),
            width=30
        )
        self.entry_nombre.pack(fill="x", pady=(0, 15))
        self.entry_nombre.focus()
        
        # PIN
        tk.Label(
            frame_form,
            text="PIN (4 dígitos):",
            font=("Arial", 11),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT_SECONDARY,
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        self.entry_pin = tk.Entry(
            frame_form,
            font=("Arial", 12),
            width=30,
            show="*"
        )
        self.entry_pin.pack(fill="x", pady=(0, 15))
        
        # Confirmar PIN
        tk.Label(
            frame_form,
            text="Confirmar PIN:",
            font=("Arial", 11),
            bg=COLOR_PANEL,
            fg=COLOR_TEXT_SECONDARY,
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        self.entry_pin_confirm = tk.Entry(
            frame_form,
            font=("Arial", 12),
            width=30,
            show="*"
        )
        self.entry_pin_confirm.pack(fill="x", pady=(0, 20))
        
        # Botones
        frame_botones = tk.Frame(self.dialog, bg=COLOR_PANEL)
        frame_botones.pack(pady=20)
        
        tk.Button(
            frame_botones,
            text="✓ Crear Usuario",
            font=("Arial", 12, "bold"),
            bg=COLOR_SUCCESS,
            fg="white",
            command=self.crear_usuario,
            width=15
        ).pack(side="left", padx=5)
        
        tk.Button(
            frame_botones,
            text="✗ Cancelar",
            font=("Arial", 12),
            bg=COLOR_ERROR,
            fg="white",
            command=self.dialog.destroy,
            width=15
        ).pack(side="left", padx=5)
        
        # Enter para confirmar
        self.entry_nombre.bind("<Return>", lambda e: self.entry_pin.focus())
        self.entry_pin.bind("<Return>", lambda e: self.entry_pin_confirm.focus())
        self.entry_pin_confirm.bind("<Return>", lambda e: self.crear_usuario())
        
        self.dialog.wait_window()
        
    def crear_usuario(self):
        """Valida y crea el usuario"""
        nombre = self.entry_nombre.get().strip()
        pin = self.entry_pin.get().strip()
        pin_confirm = self.entry_pin_confirm.get().strip()
        
        # Validaciones
        if not nombre:
            messagebox.showerror("Error", "El nombre es obligatorio", parent=self.dialog)
            self.entry_nombre.focus()
            return
        
        if len(nombre) < 3:
            messagebox.showerror("Error", "El nombre debe tener al menos 3 caracteres", parent=self.dialog)
            self.entry_nombre.focus()
            return
        
        if not pin:
            messagebox.showerror("Error", "El PIN es obligatorio", parent=self.dialog)
            self.entry_pin.focus()
            return
        
        if not pin.isdigit():
            messagebox.showerror("Error", "El PIN debe contener solo números", parent=self.dialog)
            self.entry_pin.focus()
            return
        
        if len(pin) != 4:
            messagebox.showerror("Error", "El PIN debe tener exactamente 4 dígitos", parent=self.dialog)
            self.entry_pin.focus()
            return
        
        if pin != pin_confirm:
            messagebox.showerror("Error", "Los PINs no coinciden", parent=self.dialog)
            self.entry_pin_confirm.focus()
            return
        
        try:
            # Hashear PIN
            pin_hash = bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()
            
            # Insertar en BD
            user_id = insert_user(nombre, pin_hash)
            
            self.resultado = nombre
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear usuario: {e}", parent=self.dialog)