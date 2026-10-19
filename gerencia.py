import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client

# Configuración de la página con la identidad corporativa de Crealag
st.set_page_config(
    page_title="crealag - Sistema de Supervisión", 
    layout="wide", 
    page_icon="🏢"
)

# --- CREDENCIALES ---
SUPABASE_URL = "https://jdihosehcvvzxsbhnqvf.supabase.co"
SUPABASE_KEY = "sb_publishable_D79R2pyWt6LI3lggygrbjg_4oJmoEX_"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Estilos CSS - Paleta Oscura Ejecutiva Crealag (Estructura Fija)
st.markdown("""
    <style>
    .stApp, [data-testid="stHeader"], [data-testid="stToolbar"] {
        background-color: #0A0F1D !important;
        color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] {
        background-color: #111B2E !important;
        border-right: 1px solid #1E293B !important;
    }
    h1, h2, h3, h4, h5, h6, p, span, label, div, .stMarkdown {
        color: #F8FAFC !important;
        font-weight: 700 !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #1A263D !important;
        color: #F8FAFC !important;
        border: 1px solid #2D3E5E !important;
        border-radius: 8px !important;
    }
    [data-baseweb="popover"], [data-baseweb="menu"] {
        background-color: #111B2E !important;
        color: #F8FAFC !important;
    }
    button, .stButton > button, [data-testid="baseButton-primary"], div.stButton > button {
        background: linear-gradient(135deg, #2D2412 0%, #1A160A 100%) !important;
        color: #F8FAFC !important;
        border: 1px solid #D4AF37 !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        padding: 10px 20px !important;
    }
    [data-testid="stMetricValue"] {
        color: #F8FAFC !important;
        font-weight: 800 !important;
        font-size: 30px !important;
    }
    [data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-weight: 700 !important;
    }
    .brand-title {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 800 !important;
        color: #F8FAFC !important;
    }
    .welcome-card {
        background: #111B2E;
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        margin-top: 30px;
    }
    .row-card {
        background-color: #111B2E;