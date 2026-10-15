import streamlit as pd_st
import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
from supabase import create_client

# Configuración de la página con la identidad corporativa de Crealag (Sistema de Supervisión)
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
    return create_client(SUPABASE_URL, SUPABASE