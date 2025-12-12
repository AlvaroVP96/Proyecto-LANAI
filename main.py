# main.py
# --------------------------------------------
# Punto de entrada principal del sistema
# --------------------------------------------

import tkinter as tk
from gui.access_window import VentanaAcceso
from core import ensure_schema


def main():
    """Función principal"""
    # Asegurar que la BD existe con el esquema correcto
    ensure_schema()
    
    # Crear ventana principal
    root = tk.Tk()
    app = VentanaAcceso(root)
    
    # Configurar cierre
    root.protocol("WM_DELETE_WINDOW", app.cerrar)
    
    # Iniciar loop
    root.mainloop()


if __name__ == "__main__":
    main()