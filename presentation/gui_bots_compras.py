import threading
import pandas as pd 
import tkinter as tk
from logic.shein_bot_compras import SheinBotCompras
from tkinter import ttk, filedialog,messagebox
from data.dat_bug_logs import BugLogogger

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BOTS COMPRA FACIL")
        self.geometry("1000x600")
        self.configure(bg="#f5f5f5")  # Color de fondo más suave
        self.data_db = None
        self.bug_logger=BugLogogger()
        # Crear estilos para mejorar la UI
        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 10), padx=10, pady=5)
        style.configure("BotonAzul.TButton",
                        foreground="black",
                        background="#3498db",  # Azul más suave
                        borderwidth=0,
                        relief="flat")
        style.map("BotonAzul.TButton",
                  background=[("active", "#1d7cb7")],  # Mejor transición en estado activo
                  foreground=[("active", "white")])

        # Panel superior (Header)
        self.header = tk.Label(self, text="Bienvenido", font=("Helvetica", 18, "bold"), 
                               bg="#2980b9", fg="white", pady=15)
        self.header.pack(fill=tk.X)

        # Contenedor principal
        self.main_frame = tk.Frame(self, bg="#f5f5f5")
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=0, pady=0)

        # Panel izquierdo (Menú)
        self.menu_frame = tk.Frame(self.main_frame, width=260, bg="#2c3e50", relief="solid")
        self.menu_frame.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)

        # Botón estilizado
        self.btn_bot_shein = ttk.Button(self.menu_frame, text="Bot Shein",
                                        command=lambda: self.show_section("Bot Shein"),
                                        style="BotonAzul.TButton")
        self.btn_bot_shein.pack(pady=10, padx=20, fill=tk.X)

        # Panel derecho (Contenido)
        self.content_frame = tk.Frame(self.main_frame, bg="#ecf0f1", relief="solid", bd=2)
        self.content_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=0, pady=0)

        # Etiqueta dentro del panel de contenido
        self.section_label = tk.Label(self.content_frame, text="Seleccione una opción", 
                                      font=("Helvetica", 14), bg="#ecf0f1", pady=20)
        self.section_label.pack()

    def show_section(self, section):
        self.header.config(text=section)
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        if section == "Bot Shein":
            self.show_bot_shein()
    
    def show_bot_shein(self):
        self.header.config(text="Bot Shein")
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # self.section_label = tk.Label(self.content_frame, text="Bot Shein", font=("Arial", 14), bg="#ecf0f1")
        # self.section_label.pack(pady=20)
        
        # Contenedor para botones en línea
        button_frame = tk.Frame(self.content_frame, bg="#ecf0f1")
        button_frame.pack(pady=10)
        
        # Botón para subir archivo CSV
        self.btn_upload_csv = ttk.Button(button_frame, text="Subir CSV", command=self.upload_csv)
        self.btn_upload_csv.grid(row=0, column=0, padx=5)
        
        # Botón para iniciar el bot
        self.btn_start_bot = ttk.Button(button_frame, text="Iniciar Bot", command=self.start_bot_shein,state=tk.DISABLED)
        self.btn_start_bot.grid(row=0, column=1, padx=5)
        

        self.btn_export_csv = ttk.Button(button_frame, text="Exportar CSV", command=self.export_csv, state=tk.DISABLED)
        self.btn_export_csv.grid(row=0, column=2, padx=5)
        # Tabla de datos
        self.tree = ttk.Treeview(self.content_frame, columns=("SKU","Nombre_Producto", "Cantidad","Resultado","Tienda"),show="headings") #,"Size"), show='headings')
        
        
        for col in ("SKU","Nombre_Producto","Cantidad","Resultado","Tienda"):
            self.tree.heading(col, text=col, anchor=tk.CENTER)


        self.tree.column("SKU", width=100, anchor=tk.CENTER)
        self.tree.column("Nombre_Producto", width=200, anchor=tk.CENTER)
        self.tree.column("Cantidad", width=30, anchor=tk.CENTER)
        self.tree.column("Resultado", width=150, anchor=tk.CENTER)
        self.tree.column("Tienda", width=30, anchor=tk.CENTER)
        self.tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Panel de logs
        self.logs_frame = tk.Frame(self.content_frame, bg="#dfe6e9", padx=5, pady=5)
        self.logs_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        self.logs_label = tk.Label(self.logs_frame, text="Logs", font=("Arial", 12, "bold"), bg="#dfe6e9")
        self.logs_label.pack(anchor="w")
        
        # Texto de salida (logs)
        self.logs = tk.Text(self.logs_frame, height=10, width=80, bg="#f8f9fa")
        self.logs.pack(expand=True, fill=tk.BOTH, pady=5)
    
    def upload_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        self.actualizar_logs("Cargando archivo CSV... 📂")
        self.actualizar_logs(f"Archivo seleccionado: {file_path}")

        if not file_path:
            self.actualizar_logs("No se ha seleccionado ningún archivo", error=True)
            return

        df = None
        delimiters = [";", ","]
        
        for delimiter in delimiters:
            self.actualizar_logs(f"Intentando cargar archivo CSV con delimitador: {delimiter}")
            try:
                
                df = pd.read_csv(file_path, delimiter=delimiter, encoding="utf-8-sig", engine="python")
                self.actualizar_logs(f"Archivo CSV cargado correctamente ✅")
                break  # Si logra leer el archivo, sale del bucle
            except Exception as e:
                self.actualizar_logs(f"Error al leer CSV ", error=True)
                self.bug_logger.createLog(f"Error al leer CSV",severity="ERROR",module="gui_bots",stack_trace=str(e))

        if df is None:
            self.actualizar_logs("Error al procesar el archivo CSV", error=True)
            return

        # Normalizar nombres de columnas (evita errores por mayúsculas y espacios)
        df.columns = df.columns.str.strip().str.lower()

        # Asegurar que "cantidad" es int
        if "cantidad" in df.columns:
            df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce").fillna(0).astype(int)

        # Renombrar columnas si es necesario
        column_mapping = {"nombre": "nombre_producto"}
        df.rename(columns=column_mapping, inplace=True)

        # Reemplazar NaN en "resultado" y "tienda"
        for col in ["resultado", "tienda"]:
            if col in df.columns:
                df[col] = df[col].fillna("-")


        self.data = df.astype(str).to_dict("records")
        self.actualizar_logs(f"Registros cargados: {len(self.data)}")
        if self.data:
            self.populate_table()
            self.btn_start_bot.config(state=tk.NORMAL)
        else:
            self.actualizar_logs("No se ha podido cargar el archivo CSV", error=True)


    def populate_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in self.data:
            self.tree.insert("", "end", values=(item["sku"], item["nombre_producto"], item["cantidad"],item["resultado"],item["tienda"]))
    
    def start_bot_shein(self):
        messagebox.showinfo("Confirmación", "El bot se ejecutará en este momento. Por favor, limpie su carrito de compras antes de continuar. logeese nuevamente en shein y visualice su carrito de compras")
        confirmar = messagebox.askyesno("Confirmación", "¿Limpió su carrito? Si presiona 'No', no podrá iniciar el bot.")
        if not confirmar:
            return  # Si el usuario presiona "No", no ejecuta el bot
        
        self.btn_start_bot.config(state=tk.DISABLED) 
        def run_bot():

            try:
                self.actualizar_logs("Iniciando bot... 🏃‍♂️")
                bot = SheinBotCompras(gui_callback=self.actualizar_logs)
                if not self.data:
                    self.actualizar_logs("No se ha cargado ningún archivo CSV", error=True)
                    self.actualizar_logs("Proceso finalizado ❌")
                    bot.driver.quit()
                
                data_bd=bot.get_data_process(data=self.data)

                self.tree.delete(*self.tree.get_children())
                for index,item in enumerate(data_bd):
                    print(f"Insertando fila {index}: {item}")
                    self.tree.insert("", "end", values=(item["sku"], item["nombre_producto"], item["cantidad"], item["resultado"],item["tienda"]))
                    if "añadido" in item["resultado"].lower():
                        self.actualizar_logs(f"SKU: {item['sku']} - Estado: {item['resultado']}")
                    else:
                        self.actualizar_logs(f"SKU: {item['sku']} - Estado: {item['resultado']}", error=True)

                self.data_db = data_bd
                self.actualizar_logs("Proceso finalizado ✅")
                self.btn_start_bot.config(state=tk.NORMAL)
                self.btn_export_csv.config(state=tk.NORMAL)
                bot.driver.quit()
            except Exception as e:
                self.actualizar_logs(f"Error al ejecutar el bot: {e}", error=True)
                self.actualizar_logs("Proceso finalizado {ocurrio un error} ❌", error=True)
                self.btn_start_bot.config(state=tk.NORMAL)
                bot.driver.quit()
                self.bug_logger.createLog(f"Error al ejecutar el bot",severity="ERROR",module="gui_bots",stack_trace=str(e))

        threading.Thread(target=run_bot, daemon=True).start()

    def export_csv(self):
        if not hasattr(self, "data_db") or not self.data_db:
            self.actualizar_logs("No hay datos para exportar", error=True)
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            df = pd.DataFrame(self.data_db)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            self.actualizar_logs(f"Datos exportados a {file_path} ✅")
            messagebox.showinfo("Exportación exitosa", "Datos exportados correctamente")
            self.data_db=None



    def actualizar_logs(self, mensaje, error=False):
        """ Muestra los logs en la interfaz con colores """
        self.logs.tag_configure("error", foreground="red")
        self.logs.tag_configure("info", foreground="blue")
        tag = "error" if error else "info" 
        self.logs.insert(tk.END, f"{mensaje}\n", tag)
        self.logs.yview(tk.END)