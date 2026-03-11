import tkinter as tk
from tkinter import simpledialog
import difflib
import json
import os
import re
import smtplib
from email.message import EmailMessage

# ----------------------------
# CONFIGURACION
# ----------------------------

ARCHIVO_BD = "conocimiento_fiestas.json"
CARPETA_PEDIDOS = "pedidos"

PASSWORD_ADMIN = "1234"

EMAIL = "matius.anyshit@gmail.com"
EMAIL_PASSWORD = "evjdtktaekuqbukx"

if not os.path.exists(CARPETA_PEDIDOS):
    os.makedirs(CARPETA_PEDIDOS)

# ----------------------------
# BASE DE CONOCIMIENTO
# ----------------------------

base_inicial = {
    "hola": "Hola 👋 Bienvenido a Eventos Montes de Oca 🎉",
    "que rentan": "Rentamos juegos de sillas (10 sillas + 1 tablón) y brincolines.",
    "precios": "Cada juego cuesta $220 y los brincolines $500."
}

if not os.path.exists(ARCHIVO_BD):
    with open(ARCHIVO_BD, "w") as f:
        json.dump(base_inicial, f, indent=4)

with open(ARCHIVO_BD, "r") as f:
    conocimiento = json.load(f)

# ----------------------------
# PRECIOS
# ----------------------------

PRECIO_JUEGO = 220
PRECIO_BRINCOLIN = 500

SILLAS_POR_JUEGO = 10
TABLONES_POR_JUEGO = 1

# ----------------------------
# ESTADO BOT
# ----------------------------

estado_pedido = None
datos_pedido = {}
total_actual = 0

# ----------------------------
# UTILIDADES
# ----------------------------

def normalizar(texto):

    texto = texto.lower().strip()

    palabras_basura = [
        "hola",
        "buenas",
        "buenos",
        "quiero",
        "necesito",
        "me",
        "gustaria",
        "por",
        "favor",
        "quisiera"
    ]

    palabras = texto.split()

    palabras_limpias = [p for p in palabras if p not in palabras_basura]

    return " ".join(palabras_limpias)

# ----------------------------
# CORREO
# ----------------------------

def enviar_correo(texto):

    try:
        correo = EmailMessage()

        correo["Subject"] = "Nuevo pedido - Eventos Montes de Oca"
        correo["From"] = EMAIL
        correo["To"] = EMAIL

        correo.set_content(texto)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL, EMAIL_PASSWORD)
            smtp.send_message(correo)

    except:
        print("Error enviando correo")

# ----------------------------
# GUARDAR PEDIDO
# ----------------------------

def guardar_pedido(cliente, telefono, direccion, fecha, pedido, total):

    numero = len(os.listdir(CARPETA_PEDIDOS)) + 1

    datos = {
        "cliente": cliente,
        "telefono": telefono,
        "direccion": direccion,
        "fecha": fecha,
        "pedido": pedido,
        "total": total
    }

    archivo = f"{CARPETA_PEDIDOS}/pedido_{numero}.json"

    with open(archivo, "w") as f:
        json.dump(datos, f, indent=4)

    return numero

# ----------------------------
# COTIZACION
# ----------------------------

def cotizar(mensaje):

    mensaje = normalizar(mensaje)

    numeros = re.findall(r'\d+', mensaje)

    if not numeros:
        return None, None

    cantidad = int(numeros[0])

    if "juego" in mensaje or "silla" in mensaje:

        total = cantidad * PRECIO_JUEGO
        sillas = cantidad * SILLAS_POR_JUEGO
        tablones = cantidad * TABLONES_POR_JUEGO

        texto = f"""📋 Cotización

{cantidad} juegos

{sillas} sillas
{tablones} tablones

💰 Total: ${total}
"""

        return texto, total

    if "brincolin" in mensaje:

        total = cantidad * PRECIO_BRINCOLIN

        texto = f"""📋 Cotización

{cantidad} brincolines

💰 Total: ${total}
"""

        return texto, total

    return None, None

# ----------------------------
# BUSCAR RESPUESTA
# ----------------------------

def buscar_respuesta(pregunta):

    pregunta = normalizar(pregunta)

    match = difflib.get_close_matches(pregunta, conocimiento.keys(), n=1, cutoff=0.6)

    if match:
        return conocimiento[match[0]]

    return None

# ----------------------------
# APRENDER / ELIMINAR
# ----------------------------

def aprender(pregunta, respuesta):

    conocimiento[pregunta] = respuesta

    with open(ARCHIVO_BD, "w") as f:
        json.dump(conocimiento, f, indent=4)

def eliminar_conocimiento(pregunta):

    if pregunta in conocimiento:
        del conocimiento[pregunta]

        with open(ARCHIVO_BD, "w") as f:
            json.dump(conocimiento, f, indent=4)

        return "Conocimiento eliminado."

    return "No existe esa pregunta."

def comando_aprender(mensaje):

    if "|" not in mensaje:
        return "Usa: aprender pregunta | respuesta"

    partes = mensaje.replace("aprender","").split("|")

    pregunta = normalizar(partes[0])
    respuesta = partes[1].strip()

    password = simpledialog.askstring("Admin","Contraseña")

    if password != PASSWORD_ADMIN:
        return "Contraseña incorrecta"

    aprender(pregunta, respuesta)

    return "✅ Conocimiento agregado"

def comando_eliminar(mensaje):

    password = simpledialog.askstring("Admin","Contraseña")

    if password != PASSWORD_ADMIN:
        return "Contraseña incorrecta"

    pregunta = normalizar(mensaje.replace("eliminar",""))

    return eliminar_conocimiento(pregunta)

# ----------------------------
# PEDIDO
# ----------------------------

def iniciar_pedido(pedido, total):

    global estado_pedido, datos_pedido, total_actual

    estado_pedido = "nombre"
    total_actual = total

    datos_pedido = {"pedido": pedido}

    return "Para confirmar el pedido necesito algunos datos.\n\n¿Nombre?"

def procesar_pedido(mensaje):

    global estado_pedido, datos_pedido

    if estado_pedido == "nombre":
        datos_pedido["cliente"] = mensaje
        estado_pedido = "telefono"
        return "¿Teléfono?"

    elif estado_pedido == "telefono":
        datos_pedido["telefono"] = mensaje
        estado_pedido = "direccion"
        return "¿Dirección del evento?"

    elif estado_pedido == "direccion":
        datos_pedido["direccion"] = mensaje
        estado_pedido = "fecha"
        return "¿Fecha del evento?"

    elif estado_pedido == "fecha":

        numero = guardar_pedido(
            datos_pedido["cliente"],
            datos_pedido["telefono"],
            datos_pedido["direccion"],
            mensaje,
            datos_pedido["pedido"],
            total_actual
        )

        texto = f"""
Nuevo pedido #{numero}

Cliente: {datos_pedido['cliente']}
Telefono: {datos_pedido['telefono']}
Direccion: {datos_pedido['direccion']}
Fecha: {mensaje}

Pedido: {datos_pedido['pedido']}
Total: ${total_actual}
"""

        enviar_correo(texto)

        estado_pedido = None

        return f"✅ Pedido registrado\nNúmero: {numero}"

# ----------------------------
# RESPONDER
# ----------------------------

def responder(mensaje):

    global estado_pedido, total_actual

    msg = normalizar(mensaje)

    if msg in ["salir","terminar","cerrar"]:
        ventana.destroy()
        return ""

    if msg.startswith("aprender"):
        return comando_aprender(mensaje)

    if msg.startswith("eliminar"):
        return comando_eliminar(mensaje)

    if estado_pedido:
        return procesar_pedido(mensaje)

    respuesta, total = cotizar(mensaje)

    if respuesta:
        total_actual = total
        datos_pedido["pedido"] = mensaje
        return respuesta + "\n\nEscriba SI para confirmar"

    if msg == "si" and total_actual > 0:
        return iniciar_pedido(datos_pedido["pedido"], total_actual)

    respuesta = buscar_respuesta(mensaje)

    if respuesta:
        return respuesta

    return "No entendí tu mensaje."

# ----------------------------
# INTERFAZ
# ----------------------------

# ----------------------------
# INTERFAZ TIPO CHAT
# ----------------------------

ventana = tk.Tk()
ventana.title("Eventos Montes de Oca")
ventana.geometry("420x650")
ventana.configure(bg="#ECE5DD")

chat_frame = tk.Frame(ventana, bg="#ECE5DD")
chat_frame.pack(fill=tk.BOTH, expand=True)

canvas = tk.Canvas(chat_frame, bg="#ECE5DD", highlightthickness=0)
scrollbar = tk.Scrollbar(chat_frame, command=canvas.yview)

scrollable_frame = tk.Frame(canvas, bg="#ECE5DD")

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")


# ----------------------------
# BURBUJAS DE CHAT
# ----------------------------

def burbuja(texto, lado):

    frame = tk.Frame(scrollable_frame, bg="#ECE5DD")

    if lado == "cliente":

        msg = tk.Label(
            frame,
            text=texto,
            bg="#DCF8C6",
            wraplength=250,
            padx=10,
            pady=5,
            justify="left"
        )

        msg.pack(anchor="e", padx=10, pady=3)

    else:

        msg = tk.Label(
            frame,
            text=texto,
            bg="white",
            wraplength=250,
            padx=10,
            pady=5,
            justify="left"
        )

        msg.pack(anchor="w", padx=10, pady=3)

    frame.pack(fill="both", expand=True)

    ventana.update_idletasks()
    canvas.yview_moveto(1)


# ----------------------------
# ENVIAR MENSAJE
# ----------------------------

def enviar():

    mensaje = entrada.get()

    if mensaje == "":
        return

    burbuja(mensaje, "cliente")

    entrada.delete(0, tk.END)

    respuesta = responder(mensaje)

    if respuesta:
        ventana.after(400, lambda: burbuja(respuesta, "bot"))


# ----------------------------
# AREA DE ESCRITURA
# ----------------------------

entrada_frame = tk.Frame(ventana, bg="#075E54")
entrada_frame.pack(fill=tk.X)

entrada = tk.Entry(entrada_frame, font=("Arial", 12), bd=0)
entrada.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)

boton = tk.Button(
    entrada_frame,
    text="Enviar",
    command=enviar,
    bg="#25D366",
    fg="white"
)

boton.pack(side=tk.RIGHT, padx=10)

burbuja("Hola 👋 Bienvenido a Eventos Montes de Oca 🎉", "bot")

ventana.mainloop()

ventana.mainloop()