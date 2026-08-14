# -*- coding: utf-8 -*-
"""
Created on Fri Aug 14 16:09:50 2026

@author: josec
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# Configuración inicial de la página
st.set_page_config(page_title="Dashboard Vertimientos - Julio", layout="wide")
st.title("Análisis Horario de Medidas por Línea - Julio 2026")

# Ruta del archivo Parquet (actualizada a relativa para GitHub)
DIRECTORIO_ACTUAL = Path(__file__).parent
ruta_parquet = DIRECTORIO_ACTUAL / "Lineas_Horario_202607.parquet"

# Cargar los datos y dejarlos en caché para mayor velocidad
@st.cache_data
def cargar_datos():
    df = pd.read_parquet(ruta_parquet)
    
    # Dividir medida_3 por 1000 para pasar a MWh
    df['medida_3'] = df['medida_3'] / 1000
    
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
    
    # Filtrar el dataframe temporalmente
    df_temp = df[df['Clave_Nombre'] == linea_seleccionada]
    
    # Filtro 2: Seleccionar Descripción
    descripciones_disponibles = sorted(df_temp['descripcion'].unique())
    descripcion_seleccionada = st.sidebar.selectbox("Seleccione la Descripción:", descripciones_disponibles)

    # --- PROCESAMIENTO Y GRÁFICO ---
    df_final = df_temp[df_temp['descripcion'] == descripcion_seleccionada].sort_values(by='Hora')

    if not df_final.empty:
        clave_str = df_final['Clave Línea'].iloc[0]
        
        st.subheader(f"Resultados para Línea: `{clave_str}` | Descripción: `{descripcion_seleccionada}`")
        
        # --- NUEVAS TARJETAS DE RESUMEN (KPIs) ---
        # 1. Cálculos de las métricas solicitadas
        val_max = df_final['medida_3'].max()
        val_min = df_final['medida_3'].min()
        energia_transitada = df_final['medida_3'].abs().sum() # Suma de valores absolutos
        energia_desc = df_final['medida_3'].sum() # Suma normal para la descripción seleccionada

        # Modificación: Cambiar "de" por "hacia" si la energía total es negativa
        texto_descripcion = descripcion_seleccionada
        if energia_desc < 0:
            if texto_descripcion.startswith("de_"):
                texto_descripcion = texto_descripcion.replace("de_", "hacia_", 1)
            elif texto_descripcion.startswith("de "):
                texto_descripcion = texto_descripcion.replace("de ", "hacia ", 1)

        # 2. Despliegue en 4 columnas (formato sin decimales)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Máximo (MWh)", f"{val_max:,.0f}")
        col2.metric("Mínimo (MWh)", f"{val_min:,.0f}")
        col3.metric("Energía transitada (MWh)", f"{energia_transitada:,.0f}")
        col4.metric(f"Energía {texto_descripcion} (MWh)", f"{energia_desc:,.0f}")

        # Gráfico de serie de tiempo utilizando Plotly
        fig = px.line(
            df_final,
            x='Hora',
            y='medida_3',
            title=f"Evolución Horaria - MWh (medida_3)",
            labels={'Hora': 'Fecha y Hora', 'medida_3': 'MWh (medida_3)'},
            template='plotly_white'
        )
        
        # Ajustar los ejes (Marcas cada 24 horas y sin decimales en el eje Y)
        fig.update_xaxes(
            dtick="86400000",
            tickformat="%d-%b"
        )
        fig.update_yaxes(
            tickformat=",.0f"
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # Opcional: Mostrar los datos en crudo aplicando estilo sin decimales a la columna
        with st.expander("Ver tabla de datos horarios"):
            st.dataframe(
                df_final[['Hora', 'Clave Línea', 'Línea', 'descripcion', 'medida_3']].style.format({'medida_3': '{:,.0f}'}), 
                use_container_width=True,
                hide_index=True
            )
    else:
        st.warning("No se encontraron registros para la combinación seleccionada.")

except FileNotFoundError:
    st.error(f"No se encontró el archivo Parquet. Asegúrate de que el archivo exista en el repositorio de GitHub y se llame exactamente 'Lineas_Horario_202607.parquet'.")
