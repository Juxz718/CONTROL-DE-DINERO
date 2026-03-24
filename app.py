%%writefile app.py
import streamlit as st
import pandas as pd
import sqlite3
import re
from datetime import datetime
import matplotlib.pyplot as plt

def conectar_db():
    return sqlite3.connect('mis_gastos.db')

def inicializar_db():
    conn = conectar_db()
    conn.execute('CREATE TABLE IF NOT EXISTS movimientos (fecha TEXT, descripcion TEXT, monto REAL, tipo TEXT)')
    conn.commit()
    conn.close()

# --- LÓGICA DE DETECCIÓN AUTOMÁTICA ---
def clasificar_movimiento(texto):
    # Palabras que indican que entró dinero
    palabras_ingreso = ['sueldo', 'pago', 'cachuelo', 'jacintos', 'transferencia', 'regalo', 'ingreso', 'venta']
    texto_busqueda = texto.lower()
    
    if any(palabra in texto_busqueda for palabra in palabras_ingreso):
        return "Ingreso"
    return "Gasto"

st.set_page_config(page_title="Finanzas Estilo WhatsApp", layout="centered")
inicializar_db()

st.title("📲 Mi Chat de Finanzas")
st.write("Escribe directamente (ej: '50 soles de los jacintos' o '15 menu')")

# Entrada única tipo chat
entrada = st.text_input("¿Qué pasó hoy?", placeholder="Escribe aquí...")

if st.button("Enviar 📩") or (entrada and st.session_state.get('last_input') != entrada):
    match = re.search(r'(\d+(?:\.\d+)?)', entrada)
    if match:
        monto = float(match.group(1))
        tipo = clasificar_movimiento(entrada)
        desc = entrada.replace(match.group(1), "").strip() or f"{tipo} registrado"
        fecha = datetime.now().strftime("%Y-%m-%d")
        
        conn = conectar_db()
        conn.execute('INSERT INTO movimientos VALUES (?, ?, ?, ?)', (fecha, desc, monto, tipo))
        conn.commit()
        conn.close()
        
        color = "green" if tipo == "Ingreso" else "red"
        st.markdown(f":{color}[**{tipo} registrado:** S/. {monto} - {desc}]")
    elif entrada:
        st.warning("No vi ningún monto numérico.")

# --- VISUALIZACIÓN ---
conn = conectar_db()
df = pd.read_sql_query("SELECT * FROM movimientos", conn)
conn.close()

if not df.empty:
    st.divider()
    ingresos = df[df['tipo'] == 'Ingreso']['monto'].sum()
    gastos = df[df['tipo'] == 'Gasto']['monto'].sum()
    
    c1, c2 = st.columns(2)
    c1.metric("Ingresos", f"S/. {ingresos}")
    c2.metric("Gastos", f"S/. {gastos}")
    
    # Gráfico de torta para ver la proporción
    st.subheader("Balance Visual")
    fig, ax = plt.subplots()
    ax.pie([ingresos, gastos], labels=['Ingresos', 'Gastos'], autopct='%1.1f%%', colors=['#2ecc71', '#e74c3c'])
    st.pyplot(fig)
