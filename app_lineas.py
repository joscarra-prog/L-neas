# -*- coding: utf-8 -*-
"""
Created on Fri Aug 14 16:09:50 2026

@author: josec
"""

import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración inicial de la página
st.set_page_config(page_title="Dashboard Vertimientos - Julio", layout="wide")
st.title("Análisis Horario de Medidas por Línea - Julio 2026")

# Ruta del archivo Parquet generado por el script anterior
from pathlib import Path

# Construye una ruta relativa basada en la ubicación de este script
DIRECTORIO_ACTUAL = Path(__file__).parent
ruta_parquet = DIRECTORIO_ACTUAL / "data" / "Lineas_Horario_202607.parquet"

# Cargar los datos y dejarlos en caché para mayor velocidad
@st.cache_data
def cargar_datos():
    df = pd.read_parquet(ruta_parquet)
    # Crear un campo combinado para facilitar la lectura en el selector
    df['Clave_Nombre'] = df['Clave Línea'].astype(str) + " - " + df['Línea']
    return df

try:
    df = cargar_datos()

    # --- BARRA LATERAL (Filtros) ---
    st.sidebar.header("Filtros de Búsqueda")
    
    # Filtro 1: Seleccionar Línea
    lineas_disponibles = sorted(df['Clave_Nombre'].unique())
    linea_seleccionada = st.sidebar.selectbox("Seleccione la Línea (Clave - Nombre):", lineas_disponibles)
    
    # Filtrar el dataframe temporalmente para actualizar las descripciones de esa línea
    df_temp = df[df['Clave_Nombre'] == linea_seleccionada]
    
    # Filtro 2: Seleccionar Descripción (dependiente de la línea elegida)
    descripciones_disponibles = sorted(df_temp['descripcion'].unique())
    descripcion_seleccionada = st.sidebar.selectbox("Seleccione la Descripción:", descripciones_disponibles)

    # --- PROCESAMIENTO Y GRÁFICO ---
    # Filtrar el dataframe final a graficar
    df_final = df_temp[df_temp['descripcion'] == descripcion_seleccionada].sort_values(by='Hora')

    if not df_final.empty:
        # Extraer la clave original para mostrarla sola si es necesario
        clave_str = df_final['Clave Línea'].iloc[0]
        
        st.subheader(f"Resultados para Línea: `{clave_str}` | Descripción: `{descripcion_seleccionada}`")
        
        # Tarjetas de resumen (KPIs)
        col1, col2, col3 = st.columns(3)
        col1.metric("Horas con registro", f"{len(df_final)} / 744") # 744 horas tiene julio
        col2.metric("Suma Total (medida_3)", f"{df_final['medida_3'].sum():,.2f}")
        col3.metric("Promedio Horario", f"{df_final['medida_3'].mean():,.2f}")

        # Gráfico de serie de tiempo utilizando Plotly
        fig = px.line(
            df_final,
            x='Hora',
            y='medida_3',
            title=f"Evolución Horaria de medida_3",
            labels={'Hora': 'Fecha y Hora', 'medida_3': 'Valor (medida_3)'},
            template='plotly_white'
        )
        
        # Ajustar los ejes para una visualización más limpia
        fig.update_xaxes(
            dtick="86400000", # Marcas cada 24 horas (en milisegundos)
            tickformat="%d-%b"
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # Opcional: Mostrar los datos en crudo
        with st.expander("Ver tabla de datos horarios"):
            st.dataframe(
                df_final[['Hora', 'Clave Línea', 'Línea', 'descripcion', 'medida_3']], 
                use_container_width=True,
                hide_index=True
            )
    else:
        st.warning("No se encontraron registros para la combinación seleccionada.")

except FileNotFoundError:
    st.error(f"No se encontró el archivo Parquet en la ruta especificada:\n`{ruta_parquet}`\n\nPor favor, ejecuta primero el script de procesamiento.")