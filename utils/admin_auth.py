# utils/admin_auth.py
# --------------------------------------------
# Autenticación de administrador
# --------------------------------------------

import tkinter as tk
from tkinter import messagebox
import bcrypt
import os
import json

from config import COLOR_PANEL, COLOR_TEXT, COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ERROR

ADMIN_CONFIG_FILE = "admin_config.json"


def cargar_config_admin():
    """Carga la configuración del admin"""
    if os.path.exists(ADMIN_CONFIG_FILE):
        with open(ADMIN_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None


def guardar_config_admin(pin_hash):
    """Guarda la configuración del admin"""
    with open(ADMIN_CONFIG_FILE, 'w') as f:
        json.dump({"pin_hash": pin_hash}, f)


def configurar_admin(parent):
    """Primera configuración del PIN de admin"""
    dialog = tk.Toplevel(parent)
    dialog.title("Configurar PIN Administrador")
    dialog.geometry("400x300")
    dialog.configure(bg=COLOR_PANEL)
    dialog.transient(parent)
    dialog.grab_set()
    
    resultado = {"pin_hash": None}
    
    tk.Label(
        dialog,
        text="🔐 Configuración Inicial",
        font=("Arial", 18, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_TEXT
    ).pack(pady=20)
    
    tk.Label(
        dialog,
        text="Configura un PIN para acceder al panel de administración",
        font=("Arial", 10),
        bg=COLOR_PANEL,
        fg=COLOR_TEXT_SECONDARY,
        wraplength=300
    ).pack(pady=10)
    
    tk.Label(
        dialog,
        text="PIN (4 dígitos):",
        font=("Arial", 10),
        bg=COLOR_PANEL,
        fg=COLOR_TEXT
    ).pack(pady=5)
    
    entry_pin = tk.Entry(dialog, show="*", font=("Arial", 14), width=15)
    entry_pin.pack(pady=5)
    entry_pin.focus()
    
    tk.Label(
        dialog,
        text="Confirmar PIN:",
        font=("Arial", 10),
        bg=COLOR_PANEL,
        fg=COLOR_TEXT
    ).pack(pady=5)
    
    entry_confirm = tk.Entry(dialog, show="*", font=("Arial", 14), width=15)
    entry_confirm.pack(pady=5)
    
    def confirmar():
        pin = entry_pin.get()
        confirm = entry_confirm.get()
        
        if not pin or not pin.isdigit() or len(pin) != 4:
            messagebox.showerror("Error", "PIN debe ser 4 dígitos", parent=dialog)
            return
        
        if pin != confirm:
            messagebox.showerror("Error", "Los PINs no coinciden", parent=dialog)
            return
        
        pin_hash = bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()
        guardar_config_admin(pin_hash)
        resultado["pin_hash"] = pin_hash
        dialog.destroy()
    
    tk.Button(
        dialog,
        text="Confirmar",
        command=confirmar,
        bg=COLOR_SUCCESS,
        fg="white",
        width=15
    ).pack(pady=20)
    
    entry_pin.bind("<Return>", lambda e: entry_confirm.focus())
    entry_confirm.bind("<Return>", lambda e: confirmar())
    
    dialog.wait_window()
    return resultado["pin_hash"]


def verificar_admin(parent):
    """Solicita y verifica el PIN de administrador"""
    config = cargar_config_admin()
    
    # Si no existe config, configurar por primera vez
    if not config:
        pin_hash = configurar_admin(parent)
        if not pin_hash:
            return False
        config = {"pin_hash": pin_hash}
    
    # Solicitar PIN
    dialog = tk.Toplevel(parent)
    dialog.title("Autenticación Requerida")
    dialog.geometry("350x200")
    dialog.configure(bg=COLOR_PANEL)
    dialog.transient(parent)
    dialog.grab_set()
    
    resultado = {"autenticado": False}
    
    tk.Label(
        dialog,
        text="🔐 Acceso Administrador",
        font=("Arial", 16, "bold"),
        bg=COLOR_PANEL,
        fg=COLOR_TEXT
    ).pack(pady=20)
    
    tk.Label(
        dialog,
        text="Introduce el PIN de administrador:",
        font=("Arial", 10),
        bg=COLOR_PANEL,
        fg=COLOR_TEXT_SECONDARY
    ).pack(pady=10)
    
    entry_pin = tk.Entry(dialog, show="*", font=("Arial", 14), width=15)
    entry_pin.pack(pady=10)
    entry_pin.focus()
    
    def verificar():
        pin = entry_pin.get()
        
        if bcrypt.checkpw(pin.encode(), config["pin_hash"].encode()):
            resultado["autenticado"] = True
            dialog.destroy()
        else:
            messagebox.showerror("Error", "PIN incorrecto", parent=dialog)
            entry_pin.delete(0, tk.END)
            entry_pin.focus()
    
    frame_btns = tk.Frame(dialog, bg=COLOR_PANEL)
    frame_btns.pack(pady=20)
    
    tk.Button(
        frame_btns,
        text="Confirmar",
        command=verificar,
        bg=COLOR_SUCCESS,
        fg="white",
        width=10
    ).pack(side="left", padx=5)
    
    tk.Button(
        frame_btns,
        text="Cancelar",
        command=dialog.destroy,
        bg=COLOR_ERROR,
        fg="white",
        width=10
    ).pack(side="left", padx=5)
    
    entry_pin.bind("<Return>", lambda e: verificar())
    
    dialog.wait_window()
    return resultado["autenticado"]