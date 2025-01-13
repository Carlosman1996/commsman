import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pickle
from backend.core.backend_manager import BackendManager  # Asegúrate de tener este archivo y clase implementados


class Gui:
    def __init__(self, root):
        self.root = root
        self.root.title("Industrial Postman")
        self.root.geometry("800x600")

        # Inicializar el Backend Manager
        self.backend_manager = BackendManager("MODBUS")

        # Dividir pantalla
        self.left_frame = tk.Frame(root, width=300, bg="lightgrey")
        self.right_frame = tk.Frame(root, bg="white")
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        # Árbol de peticiones (izquierda)
        self.tree = ttk.Treeview(self.left_frame)
        self.tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Agregar barra de scroll
        tree_scroll = ttk.Scrollbar(self.left_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        # Configurar columnas del árbol
        self.tree.heading("#0", text="Peticiones", anchor=tk.W)
        self.tree.bind("<<TreeviewSelect>>", self.display_request_details)

        # Botones de gestión de grupos/peticiones
        btn_frame = tk.Frame(self.left_frame, bg="lightgrey")
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="Añadir Carpeta", command=self.add_folder).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Añadir Petición", command=self.add_request).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Eliminar", command=self.delete_item).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Editar Nombre", command=self.edit_name).pack(side=tk.LEFT, padx=5)

        # Detalles de la petición (derecha)
        self.details_frame = tk.Frame(self.right_frame, bg="white")
        self.details_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        tk.Label(self.details_frame, text="Detalles de la petición", font=("Arial", 14), bg="white").pack(anchor=tk.W)

        self.details_text = tk.Text(self.details_frame, height=20, bg="lightgrey")
        self.details_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Diccionario para almacenar datos de las peticiones
        self.requests = {}

        # Cargar configuración guardada
        self.load_configuration()

    def add_folder(self):
        """Añade una carpeta al árbol."""
        folder_name = self.simple_input("Nombre de la carpeta")
        if not folder_name:
            return

        selected = self.tree.selection()
        if selected:
            # Añadir subcarpeta dentro de la carpeta seleccionada
            parent = selected[0]
            self.tree.insert(parent, tk.END, text=folder_name)
        else:
            # Añadir carpeta al nivel raíz
            self.tree.insert("", tk.END, text=folder_name)

    def add_request(self):
        """Añade una petición a una carpeta seleccionada."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selecciona un elemento", "Por favor selecciona una carpeta.")
            return

        parent = selected[0]
        request_name = self.simple_input("Nombre de la petición")
        if request_name:
            item_id = self.tree.insert(parent, tk.END, text=request_name)
            self.requests[item_id] = {
                "name": request_name,
                "protocol": "MODBUS",
                "method": "read",
                "params": {"address": 0, "count": 1}
            }

    def display_request_details(self, event):
        """Muestra los detalles de la petición seleccionada en el panel derecho."""
        selected = self.tree.selection()
        if selected and selected[0] in self.requests:
            request = self.requests[selected[0]]
            self.details_text.delete("1.0", tk.END)
            self.details_text.insert(tk.END, f"Nombre: {request['name']}\n")
            self.details_text.insert(tk.END, f"Protocolo: {request['protocol']}\n")
            self.details_text.insert(tk.END, f"Método: {request['method']}\n")
            self.details_text.insert(tk.END, f"Parámetros:\n")
            for key, value in request["params"].items():
                self.details_text.insert(tk.END, f"  {key}: {value}\n")
            # Botón para enviar petición
            send_button = tk.Button(self.details_frame, text="Enviar Petición Modbus", command=self.send_modbus_request)
            send_button.pack(pady=5)
        else:
            self.details_text.delete("1.0", tk.END)

    def delete_item(self):
        """Elimina la carpeta o petición seleccionada."""
        selected = self.tree.selection()
        if selected:
            item_id = selected[0]
            self.tree.delete(item_id)
            if item_id in self.requests:
                del self.requests[item_id]
            self.save_configuration()

    def edit_name(self):
        """Edita el nombre de la carpeta o petición seleccionada."""
        selected = self.tree.selection()
        if selected:
            current_name = self.tree.item(selected[0], "text")
            new_name = self.simple_input(f"Nuevo nombre para '{current_name}'")
            if new_name:
                self.tree.item(selected[0], text=new_name)
                if selected[0] in self.requests:
                    self.requests[selected[0]]["name"] = new_name
                self.save_configuration()

    def send_modbus_request(self):
        """Envía la petición Modbus seleccionada."""
        selected = self.tree.selection()
        if selected and selected[0] in self.requests:
            request = self.requests[selected[0]]
            # Usar el BackendManager para enviar la petición
            response = self.backend_manager.send_modbus_request(request["params"].get("address", 0), request["params"].get("count", 1))
            if response:
                messagebox.showinfo("Respuesta", f"Registros leídos: {response}")
            else:
                messagebox.showerror("Error", "Error al realizar la petición Modbus")

    def simple_input(self, prompt):
        """Muestra un cuadro de diálogo simple para ingresar texto."""
        input_window = tk.Toplevel(self.root)
        input_window.title(prompt)
        tk.Label(input_window, text=prompt).pack(pady=10)
        entry = tk.Entry(input_window)
        entry.pack(pady=5)
        entry.focus()
        result = []

        def save_input():
            result.append(entry.get())
            input_window.destroy()

        tk.Button(input_window, text="Aceptar", command=save_input).pack(pady=10)
        self.root.wait_window(input_window)
        return result[0] if result else None

    def save_configuration(self):
        """Guarda la configuración en un archivo pickle."""
        with open("configuration.pkl", "wb") as f:
            pickle.dump(self.requests, f)

    def load_configuration(self):
        """Carga la configuración desde un archivo pickle."""
        try:
            with open("configuration.pkl", "rb") as f:
                self.requests = pickle.load(f)
                # Cargar el árbol con los datos
                for item_id, request in self.requests.items():
                    self.tree.insert("", tk.END, text=request["name"])
        except FileNotFoundError:
            self.requests = {}


# Punto de entrada principal
if __name__ == "__main__":
    root = tk.Tk()
    app = Gui(root)
    root.mainloop()
