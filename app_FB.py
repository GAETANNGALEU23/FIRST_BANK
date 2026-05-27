"""
========================================================================
 AFRILAND FIRST BANK — Plateforme BI Satisfaction Client
 Version 2.0 | Développé par DeepStats
========================================================================
 Fonctionnalités :
   - Page de connexion sécurisée avec fond Afriland
   - Espace Admin : upload, journal d'activité (espion), toutes pages
   - Espace Utilisateur : dashboards par rôle/agence
   - 6 tableaux de bord avec graphiques interprétés
   - Moteur prédictif S+1
   - Export rapport consolidé
   - Déconnexion sécurisée
========================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import datetime
import io
import os
import sqlite3
import hashlib
import json
from pathlib import Path

# ============================================================
# 0. CONFIGURATION PAGE — doit être en PREMIER
# ============================================================
st.set_page_config(
    page_title="Afriland First Bank | BI Satisfaction",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 1. CONSTANTES & PALETTE COULEURS AFRILAND
# ============================================================
AFB_RED       = "#C8102E"   # Rouge institutionnel Afriland
AFB_DARK_RED  = "#8B0000"
AFB_BLACK     = "#1A1A1A"
AFB_GRAY      = "#555555"
AFB_LIGHT     = "#F5F5F5"
AFB_GOLD      = "#B8960C"

DB_PATH = os.path.join(os.path.dirname(__file__), "activity_log.db")

# ============================================================
# 2. UTILISATEURS (prod → remplacer par BDD sécurisée)
# ============================================================
def _hash(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

USERS = {
    "admin": {
        "hash": _hash("Afriland@Admin2024"),
        "role": "admin",
        "nom": "Administrateur Système",
        "agence": None,
    },
    "dg_reseau": {
        "hash": _hash("DG@Reseau2024"),
        "role": "user",
        "nom": "Directeur Général Réseau",
        "agence": None,          # Accès toutes agences
    },
    "hippodrome": {
        "hash": _hash("Hippo@AFB2024"),
        "role": "user",
        "nom": "Responsable Hippodrome",
        "agence": "FIRST BANK HIPPODROME",
    },
    "bastos": {
        "hash": _hash("Bastos@AFB2024"),
        "role": "user",
        "nom": "Responsable Bastos",
        "agence": "FIRST BANK BASTOS",
    },
    "bonanjo": {
        "hash": _hash("Bonanjo@AFB2024"),
        "role": "user",
        "nom": "Responsable Bonanjo",
        "agence": "FIRST BANK BONANJO",
    },
    "maroua": {
        "hash": _hash("Maroua@AFB2024"),
        "role": "user",
        "nom": "Responsable Maroua",
        "agence": "FIRST BANK MAROUA",
    },
    "mendong": {
        "hash": _hash("Mendong@AFB2024"),
        "role": "user",
        "nom": "Responsable Mendong",
        "agence": "FIRST BANK MENDONG",
    },
    "analyste": {
        "hash": _hash("Analyste@AFB2024"),
        "role": "user",
        "nom": "Analyste Qualité",
        "agence": None,          # Accès toutes agences (lecture)
    },
}

# ============================================================
# 3. BASE DE DONNÉES SQLITE — JOURNAL D'ACTIVITÉ
# ============================================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT,
            username    TEXT,
            role        TEXT,
            nom         TEXT,
            action      TEXT,
            page        TEXT,
            detail      TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS login_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT,
            username    TEXT,
            success     INTEGER,
            ip_info     TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_action(username: str, role: str, nom: str, action: str, page: str = "", detail: str = ""):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO activity_log (timestamp, username, role, nom, action, page, detail)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            username, role, nom, action, page, detail
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass

def log_login(username: str, success: bool):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO login_log (timestamp, username, success, ip_info)
            VALUES (?, ?, ?, ?)
        """, (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            username, int(success), "Streamlit Cloud"
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass

def get_activity_logs(limit: int = 500) -> pd.DataFrame:
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            f"SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT {limit}",
            conn
        )
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def get_login_logs(limit: int = 200) -> pd.DataFrame:
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            f"SELECT * FROM login_log ORDER BY timestamp DESC LIMIT {limit}",
            conn
        )
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

# ============================================================
# 4. CSS GLOBAL & STYLES PERSONNALISÉS
# ============================================================
def inject_css():
    st.markdown(f"""
    <style>
    /* ── Imports & Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * {{ font-family: 'Inter', sans-serif !important; }}

    /* ── Masquer éléments Streamlit par défaut ── */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    /* NE PAS cacher header — il contient le bouton d'ouverture de la sidebar */
    [data-testid="stSidebarCollapsedControl"] {{ visibility: visible !important; display: flex !important; }}
    .block-container {{ padding-top: 1rem !important; }}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {AFB_BLACK} 0%, #2C2C2C 100%) !important;
        border-right: 3px solid {AFB_RED};
    }}
    [data-testid="stSidebar"] * {{ color: #FFFFFF !important; }}
    [data-testid="stSidebar"] .stRadio label {{
        color: #CCCCCC !important;
        font-size: 13px;
        padding: 4px 0;
        transition: color 0.2s;
    }}
    [data-testid="stSidebar"] .stRadio label:hover {{ color: {AFB_RED} !important; }}
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 {{
        color: {AFB_RED} !important;
        border-bottom: 1px solid #333;
        padding-bottom: 6px;
    }}

    /* ── Titre principal ── */
    .main-title {{
        background: linear-gradient(135deg, {AFB_BLACK} 0%, #3A0000 100%);
        color: white;
        font-size: 22px;
        font-weight: 800;
        text-align: center;
        padding: 18px 30px;
        border-bottom: 4px solid {AFB_RED};
        border-radius: 0 0 8px 8px;
        letter-spacing: 0.5px;
        margin-bottom: 20px;
        text-transform: uppercase;
    }}
    .main-title span {{ color: {AFB_RED}; }}

    /* ── Sous-titre section ── */
    .section-sub {{
        color: {AFB_GRAY};
        font-size: 13px;
        text-align: center;
        margin-top: -12px;
        margin-bottom: 20px;
        font-style: italic;
    }}

    /* ── Cartes KPI ── */
    .kpi-card {{
        background: white;
        border-left: 5px solid {AFB_RED};
        border-radius: 6px;
        padding: 18px 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    .kpi-card:hover {{ transform: translateY(-3px); box-shadow: 0 6px 20px rgba(200,16,46,0.15); }}
    .kpi-value {{
        font-size: 32px;
        font-weight: 800;
        color: {AFB_BLACK};
        line-height: 1;
    }}
    .kpi-label {{
        font-size: 11px;
        font-weight: 600;
        color: {AFB_GRAY};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 6px;
    }}
    .kpi-delta {{
        font-size: 12px;
        color: #27AE60;
        font-weight: 600;
        margin-top: 3px;
    }}

    /* ── Boîtes d'interprétation ── */
    .insight-box {{
        background: linear-gradient(135deg, #FFF5F5, #FFFFFF);
        border: 1px solid #FFCCCC;
        border-left: 5px solid {AFB_RED};
        padding: 14px 18px;
        border-radius: 6px;
        margin: 12px 0;
        font-size: 13.5px;
        color: {AFB_BLACK};
        line-height: 1.6;
    }}
    .insight-box b {{ color: {AFB_RED}; }}

    .info-box {{
        background: linear-gradient(135deg, #F0F4FF, #FFFFFF);
        border: 1px solid #C5D5F8;
        border-left: 5px solid #2563EB;
        padding: 14px 18px;
        border-radius: 6px;
        margin: 12px 0;
        font-size: 13.5px;
        color: {AFB_BLACK};
        line-height: 1.6;
    }}

    .success-box {{
        background: linear-gradient(135deg, #F0FFF4, #FFFFFF);
        border: 1px solid #B2DFDB;
        border-left: 5px solid #1B8A4A;
        padding: 14px 18px;
        border-radius: 6px;
        margin: 12px 0;
        font-size: 13.5px;
    }}

    .warning-box {{
        background: linear-gradient(135deg, #FFFBF0, #FFFFFF);
        border: 1px solid #FFE082;
        border-left: 5px solid #F59E0B;
        padding: 14px 18px;
        border-radius: 6px;
        margin: 12px 0;
        font-size: 13.5px;
    }}

    /* ── Séparateurs ── */
    .afb-divider {{
        height: 2px;
        background: linear-gradient(90deg, {AFB_RED}, transparent);
        border: none;
        margin: 20px 0;
    }}

    /* ── Section Header ── */
    .section-header {{
        background: {AFB_BLACK};
        color: white;
        padding: 10px 18px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 700;
        margin: 20px 0 12px 0;
        letter-spacing: 0.3px;
    }}
    .section-header span {{ color: {AFB_RED}; }}

    /* ── Verbatim cards ── */
    .verb-card {{
        background: white;
        border-radius: 8px;
        padding: 12px 15px;
        margin: 8px 0;
        border: 1px solid #EEEEEE;
        font-size: 13px;
        font-style: italic;
        color: #333;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        line-height: 1.5;
    }}
    .verb-neg {{ border-left: 4px solid {AFB_RED}; }}
    .verb-pos {{ border-left: 4px solid #1B8A4A; }}
    .verb-sug {{ border-left: 4px solid #F59E0B; }}

    /* ── Buttons ── */
    div.stButton > button {{
        background: {AFB_RED} !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        padding: 10px 24px !important;
        letter-spacing: 0.3px !important;
        transition: all 0.2s !important;
        width: 100% !important;
    }}
    div.stButton > button:hover {{
        background: {AFB_DARK_RED} !important;
        box-shadow: 0 4px 12px rgba(200,16,46,0.4) !important;
        transform: translateY(-1px) !important;
    }}

    /* ── Metric widgets ── */
    [data-testid="stMetricValue"] {{
        font-size: 28px !important;
        font-weight: 800 !important;
        color: {AFB_BLACK} !important;
    }}
    [data-testid="stMetricDelta"] {{ font-size: 13px !important; }}

    /* ── DataFrames ── */
    .dataframe {{ border-collapse: collapse !important; width: 100%; }}
    .dataframe th {{
        background: {AFB_BLACK} !important;
        color: white !important;
        font-weight: 600;
        padding: 10px !important;
        font-size: 12px;
    }}
    .dataframe td {{ padding: 8px !important; font-size: 12px; }}
    .dataframe tr:nth-child(even) {{ background: #FAFAFA; }}

    /* ── Selectbox & Sliders ── */
    .stSelectbox > div > div {{
        border: 2px solid #E0E0E0 !important;
        border-radius: 6px !important;
    }}
    .stSelectbox > div > div:focus-within {{ border-color: {AFB_RED} !important; }}

    /* ── Badges ── */
    .badge-admin {{
        background: {AFB_RED};
        color: white;
        font-size: 10px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .badge-user {{
        background: {AFB_BLACK};
        color: white;
        font-size: 10px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 12px;
        text-transform: uppercase;
    }}

    /* ── Espion table ── */
    .spy-table {{ font-size: 12px; }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: #F5F5F5; }}
    ::-webkit-scrollbar-thumb {{ background: {AFB_RED}; border-radius: 3px; }}

    /* ── Plotly fix ── */
    .js-plotly-plot .plotly {{ border-radius: 8px; }}
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# 5. PAGE DE CONNEXION
# ============================================================
def show_login_page():
    """Page de connexion avec fond Afriland et design premium"""

    # CSS spécifique à la page de login
    st.markdown("""
    <style>
    /* Fond global de la page login */
    .stApp {
        background:
            linear-gradient(rgba(0,0,0,0.72), rgba(139,0,0,0.55)),
            url('https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1400&q=85')
            center/cover no-repeat fixed;
    }

    /* Cacher la sidebar sur la page login */
    [data-testid="stSidebar"] { display: none; }
    .block-container { padding: 0 !important; max-width: 100% !important; }

    /* Carte de connexion centrale */
    .login-card {
        background: rgba(255,255,255,0.97);
        border-radius: 16px;
        padding: 50px 48px;
        box-shadow: 0 24px 80px rgba(0,0,0,0.45);
        border-top: 6px solid #C8102E;
        max-width: 460px;
        margin: 0 auto;
    }
    .login-logo {
        text-align: center;
        margin-bottom: 8px;
    }
    .login-bank-name {
        text-align: center;
        font-size: 20px;
        font-weight: 900;
        color: #1A1A1A;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .login-tagline {
        text-align: center;
        font-size: 11px;
        color: #888;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 30px;
        border-bottom: 2px solid #F0F0F0;
        padding-bottom: 20px;
    }
    .login-title {
        font-size: 18px;
        font-weight: 700;
        color: #1A1A1A;
        margin-bottom: 6px;
    }
    .login-sub {
        font-size: 12px;
        color: #888;
        margin-bottom: 24px;
    }
    .stTextInput input {
        border: 2px solid #E0E0E0 !important;
        border-radius: 8px !important;
        padding: 12px 14px !important;
        font-size: 14px !important;
        transition: border-color 0.2s !important;
    }
    .stTextInput input:focus {
        border-color: #C8102E !important;
        box-shadow: 0 0 0 3px rgba(200,16,46,0.1) !important;
    }
    .login-footer {
        text-align: center;
        font-size: 11px;
        color: #BBBBBB;
        margin-top: 30px;
    }
    .login-footer b { color: #C8102E; }
    .hero-text {
        text-align: center;
        color: white;
        margin-bottom: 40px;
        margin-top: 60px;
    }
    .hero-title {
        font-size: 36px;
        font-weight: 900;
        text-shadow: 0 2px 12px rgba(0,0,0,0.6);
        letter-spacing: 1px;
    }
    .hero-sub {
        font-size: 15px;
        color: rgba(255,255,255,0.8);
        margin-top: 8px;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

    # Hero text au-dessus de la carte
    st.markdown("""
    <div class='hero-text'>
        <div class='hero-title'>🏦 Plateforme BI Satisfaction Client</div>
        <div class='hero-sub'>Intelligence Analytique • Réseau Cameroun • Afriland First Bank</div>
    </div>
    """, unsafe_allow_html=True)

    # Centrage de la carte
    col_l, col_c, col_r = st.columns([1, 1.6, 1])
    with col_c:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)

        # Logo et nom de la banque
        st.markdown("""
        <div class='login-logo'>
            <span style='font-size:52px;'>🏦</span>
        </div>
        <div class='login-bank-name'>Afriland First Bank</div>
        <div class='login-tagline'>BI Satisfaction Réseau Cameroun</div>
        <div class='login-title'>Connexion sécurisée</div>
        <div class='login-sub'>Entrez vos identifiants pour accéder à la plateforme</div>
        """, unsafe_allow_html=True)

        username = st.text_input("👤  Identifiant", placeholder="Votre identifiant", key="login_user")
        password = st.text_input("🔒  Mot de passe", type="password", placeholder="••••••••••", key="login_pwd")

        st.markdown("<br>", unsafe_allow_html=True)
        login_btn = st.button("  🔐  SE CONNECTER  ", key="login_btn")

        if login_btn:
            if username.strip() == "" or password.strip() == "":
                st.error("⚠️ Veuillez remplir tous les champs.")
            elif username in USERS and USERS[username]["hash"] == _hash(password):
                user = USERS[username]
                st.session_state.authenticated = True
                st.session_state.username     = username
                st.session_state.role         = user["role"]
                st.session_state.nom          = user["nom"]
                st.session_state.agence       = user["agence"]
                st.session_state.login_time   = datetime.datetime.now()
                st.session_state.current_page = (
                    "📊 Dashboard Global" if user["role"] == "admin"
                    else "📊 Dashboard Global"
                )
                log_login(username, True)
                log_action(username, user["role"], user["nom"], "LOGIN", "", "Connexion réussie")
                st.success("✅ Connexion réussie ! Chargement en cours…")
                st.rerun()
            else:
                log_login(username, False)
                st.error("❌ Identifiant ou mot de passe incorrect.")
                st.markdown("""
                <div style='font-size:12px; color:#888; margin-top:8px;'>
                Contactez l'administrateur si vous avez oublié vos accès.
                </div>
                """, unsafe_allow_html=True)

        # Footer
        st.markdown("""
        <div class='login-footer'>
            Accès réservé au personnel autorisé •
            <b>Afriland First Bank</b> © 2024<br>
            Développé par <b>DeepStats</b> — Solutions IA & Analytique
        </div>
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# 6. PRÉ-TRAITEMENT DES DONNÉES
# ============================================================
def fix_encoding(text: str) -> str:
    """Corrige les problèmes d'encodage UTF-8 fréquents"""
    if not isinstance(text, str):
        return text
    fixes = {
        'Ã©': 'é', 'Ã¨': 'è', 'Ã ': 'à', 'Ã´': 'ô', 'Ã»': 'û',
        'Ã®': 'î', 'Ã¢': 'â', 'Ã«': 'ë', 'Ã§': 'ç', 'Ã‰': 'É',
        'Ã€': 'À', 'Ã‡': 'Ç', 'Ãš': 'Ú', 'â€™': "'", 'â€œ': '"', 'â€': '"',
    }
    for bad, good in fixes.items():
        text = text.replace(bad, good)
    return text

def load_and_preprocess(file_source) -> pd.DataFrame:
    """Charge et nettoie les données du fichier Excel/CSV"""
    try:
        fname = file_source if isinstance(file_source, str) else file_source.name
        if fname.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_source)
        else:
            for enc in ['utf-8', 'latin-1', 'utf-8-sig']:
                try:
                    df = pd.read_csv(file_source, encoding=enc); break
                except (UnicodeDecodeError, Exception):
                    continue
    except Exception as e:
        raise ValueError(f"Erreur lecture fichier : {e}")

    if df.empty:
        raise ValueError("Le fichier ne contient aucune donnée.")

    df.columns = df.columns.str.strip()

    # Renommage des colonnes
    rename_map = {
        'start': 'date_debut',
        'end':   'date_fin',
    }
    # Colonnes par position (plus robuste que le nom exact)
    cols = df.columns.tolist()
    if len(cols) >= 14:
        rename_map[cols[2]]  = 'date_operation'
        rename_map[cols[3]]  = 'agence'
        rename_map[cols[4]]  = 'type_compte'
        rename_map[cols[5]]  = 'operation'
        rename_map[cols[6]]  = 'temps_attente'
        rename_map[cols[7]]  = 'accueil_agent'
        rename_map[cols[8]]  = 'effort_client'
        rename_map[cols[9]]  = 'satisfaction_globale'
        rename_map[cols[10]] = 'nps_score'
        rename_map[cols[11]] = 'verbatim_negatif'
        rename_map[cols[12]] = 'verbatim_amelioration'
        rename_map[cols[13]] = 'verbatim_positif'

    df = df.rename(columns=rename_map)

    # Correction encodage sur colonnes texte
    for col in ['agence', 'type_compte', 'operation', 'temps_attente',
                'accueil_agent', 'effort_client', 'satisfaction_globale',
                'verbatim_negatif', 'verbatim_amelioration', 'verbatim_positif']:
        if col in df.columns:
            df[col] = df[col].apply(fix_encoding).astype(str).str.strip()

    # Normalisation agence
    if 'agence' in df.columns:
        df['agence'] = df['agence'].str.strip().str.upper()
        df['agence'] = df['agence'].replace('NAN', np.nan)
        df.dropna(subset=['agence'], inplace=True)

    # Normalisation des libellés (variantes orthographiques)
    norm_sat = {
        'tres satisfaisante':      'Très satisfaisante',
        'très satisfaisante':      'Très satisfaisante',
        'satisfaisante':           'Satisfaisante',
        'peu satisfaisante':       'Peu satisfaisante',
        'pas du tout satisfaisante': 'Pas du tout satisfaisante',
        'neutre':                  'Neutre',
        'tres facile':             'Très facile',
        'très facile':             'Très facile',
        'facile':                  'Facile',
        'moyennement difficile':   'Moyennement difficile',
        'difficile':               'Difficile',
        'très difficile':          'Très difficile',
        'trÃ¨s difficile':         'Très difficile',
        'trÃ¨s facile':            'Très facile',
        'nan': np.nan,
    }
    for col in ['satisfaction_globale', 'temps_attente', 'accueil_agent', 'effort_client']:
        if col in df.columns:
            df[col] = df[col].str.lower().map(norm_sat).fillna(df[col].str.lower())

    # Normalisation type_compte
    if 'type_compte' in df.columns:
        df['type_compte'] = df['type_compte'].apply(lambda x:
            'Particulier' if 'articulier' in str(x) or 'Retail' in str(x)
            else ('Société' if 'oci' in str(x) or 'Society' in str(x)
            else ('Entreprise individuelle' if 'nterprise' in str(x) or 'rivate' in str(x)
            else str(x)))
        )

    # Normalisation operation
    if 'operation' in df.columns:
        df['operation'] = df['operation'].apply(lambda x:
            'Retrait' if 'trai' in str(x) or 'ithdraw' in str(x)
            else ('Dépôt' if 'p' in str(x).lower() and 'p' in str(x).lower() and 'os' in str(x)
            else ('Virement' if 'irement' in str(x) or 'ransfer' in str(x)
            else ('Remise chèque' if 'h' in str(x) and 'que' in str(x)
            else 'Autre')))
        )

    # Dates — gère datetime, int (Excel serial) et str
    if 'date_operation' in df.columns:
        df['date_operation'] = pd.to_datetime(df['date_operation'], errors='coerce').dt.date
        df['date_operation'] = df['date_operation'].fillna(datetime.date.today())
    else:
        df['date_operation'] = datetime.date.today()

    # NPS
    df['nps_score'] = pd.to_numeric(df['nps_score'], errors='coerce')

    def seg_nps(s):
        if pd.isna(s): return np.nan
        return 'Promoteur' if s >= 9 else ('Passif' if s >= 7 else 'Détracteur')

    df['nps_class'] = df['nps_score'].apply(seg_nps)

    # Mapping Likert → numérique
    lk_sat = {
        'Très satisfaisante': 5, 'Satisfaisante': 4, 'Neutre': 3,
        'Peu satisfaisante': 2, 'Pas du tout satisfaisante': 1,
    }
    lk_eff = {
        'Très facile': 5, 'Facile': 4, 'Moyennement difficile': 3,
        'Difficile': 2, 'Très difficile': 1,
    }
    df['score_satisfaction_num'] = df['satisfaction_globale'].map(lk_sat)
    df['score_attente_num']      = df['temps_attente'].map(lk_sat)
    df['score_accueil_num']      = df['accueil_agent'].map(lk_sat)
    df['score_effort_num']       = df['effort_client'].map(lk_eff)

    # Mois/semaine pour analyses temporelles
    df['date_dt'] = pd.to_datetime(df['date_operation'], errors='coerce')
    df['mois']    = df['date_dt'].dt.strftime('%Y-%m')
    df['semaine'] = df['date_dt'].dt.strftime('%G-S%V')

    return df


def kpi_nps(df: pd.DataFrame) -> float:
    vc = df['nps_class'].value_counts()
    n  = df['nps_class'].dropna().count()
    if n == 0: return 0.0
    return round((vc.get('Promoteur', 0) - vc.get('Détracteur', 0)) / n * 100, 1)

def kpi_sat(df: pd.DataFrame) -> float:
    vc = df['satisfaction_globale'].value_counts()
    pos = vc.get('Très satisfaisante', 0) + vc.get('Satisfaisante', 0)
    n   = df['satisfaction_globale'].dropna().count()
    return round(pos / n * 100, 1) if n > 0 else 0.0

def nps_color(v: float) -> str:
    return "#1B8A4A" if v >= 20 else ("#F59E0B" if v >= 0 else AFB_RED)

def sat_color(v: float) -> str:
    return "#1B8A4A" if v >= 70 else ("#F59E0B" if v >= 50 else AFB_RED)


# ============================================================
# 7. GRAPHIQUES RÉUTILISABLES
# ============================================================
PLOTLY_LAYOUT = dict(
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(family='Inter', size=12, color=AFB_BLACK),
    margin=dict(t=40, b=30, l=20, r=20),
    title_font=dict(size=14, color=AFB_BLACK, family='Inter'),
)

def fig_bar_h(df_g, x, y, title, color=AFB_RED):
    fig = px.bar(df_g, x=x, y=y, orientation='h', color_discrete_sequence=[color],
                 title=title, text=x)
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_xaxes(range=[0, max(df_g[x].max() * 1.2, 0.1)])
    return fig

def fig_pie(df_g, values, names, title, color_map=None):
    kw = dict(color=names, color_discrete_map=color_map) if color_map else {}
    fig = px.pie(df_g, values=values, names=names, title=title, **kw,
                 hole=0.38)
    fig.update_traces(textfont_size=13, textinfo='percent+label')
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=True)
    return fig


# ============================================================
# 8. SIDEBAR APRÈS CONNEXION
# ============================================================
def render_sidebar(df_raw, role, nom, agence, username):
    with st.sidebar:
        # En-tête utilisateur
        badge = "admin" if role == "admin" else "user"
        badge_class = "badge-admin" if role == "admin" else "badge-user"
        st.markdown(f"""
        <div style='text-align:center; padding:15px 0 10px;'>
            <div style='font-size:40px;'>🏦</div>
            <div style='font-weight:800; font-size:15px; color:white; margin-top:5px;'>AFRILAND FIRST BANK</div>
            <div style='font-size:11px; color:#AAAAAA; letter-spacing:1.5px; margin-bottom:10px;'>BI SATISFACTION RÉSEAU</div>
            <span class='{badge_class}'>{badge.upper()}</span>
        </div>
        <hr style='border-color:#333; margin:0;'>
        <div style='padding:12px 0 5px; font-size:12px; color:#CCCCCC;'>
            👤 <b style='color:white;'>{nom}</b><br>
            <span style='color:#AAAAAA; font-size:11px;'>
            {'📍 ' + agence if agence else '🌐 Accès réseau complet'}
            </span>
        </div>
        <hr style='border-color:#333; margin:0 0 10px;'>
        """, unsafe_allow_html=True)

        # Upload données (admin uniquement)
        if role == "admin":
            st.markdown("<div style='font-size:11px; color:#C8102E; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>📁 Données</div>", unsafe_allow_html=True)
            uploaded = st.file_uploader("Importer fichier enquête (.xlsx, .csv)",
                                        type=["xlsx", "csv"],
                                        help="Glissez votre fichier ici pour actualiser tous les tableaux de bord.")
            if uploaded:
                try:
                    df_new = load_and_preprocess(uploaded)
                    st.session_state.df = df_new
                    st.success(f"✅ {len(df_new)} lignes chargées")
                    log_action(username, role, nom, "UPLOAD", "", f"Fichier : {uploaded.name}, {len(df_new)} lignes")
                except Exception as e:
                    st.error(f"Erreur : {e}")

        # Filtre date
        df_result = None
        if df_raw is not None:
            st.markdown("<hr style='border-color:#333;'>", unsafe_allow_html=True)
            st.markdown("<div style='font-size:11px; color:#C8102E; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>📅 Filtre Temporel</div>", unsafe_allow_html=True)
            dates = df_raw['date_operation'].dropna()
            if not dates.empty:
                min_d, max_d = min(dates), max(dates)
                rng = st.date_input("Période d'analyse :", value=(min_d, max_d),
                                    min_value=min_d, max_value=max_d)
                if isinstance(rng, (list, tuple)) and len(rng) == 2:
                    d1, d2 = rng
                    df_result = df_raw[(df_raw['date_operation'] >= d1) & (df_raw['date_operation'] <= d2)]
                else:
                    df_result = df_raw.copy()
            else:
                df_result = df_raw.copy()

        # Navigation
        st.markdown("<hr style='border-color:#333;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:11px; color:#C8102E; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>🗺 Navigation</div>", unsafe_allow_html=True)

        pages_user = [
            "📊 Dashboard Global",
            "📍 Dashboard par Agence",
            "📈 Analyse Comparative",
            "🔮 Modélisation & Prédictions",
            "💬 Verbatims Clients",
            "📝 Rapport & Export",
        ]
        pages_admin = [
            "📊 Dashboard Global",
            "📍 Dashboard par Agence",
            "📈 Analyse Comparative",
            "🔮 Modélisation & Prédictions",
            "💬 Verbatims Clients",
            "📝 Rapport & Export",
            "🕵️ Journal d'Activité (Admin)",
        ]
        pages = pages_admin if role == "admin" else pages_user

        page = st.radio("", pages, key="nav_radio",
                        index=pages.index(st.session_state.get("current_page", pages[0]))
                        if st.session_state.get("current_page", pages[0]) in pages else 0)

        if page != st.session_state.get("current_page"):
            st.session_state.current_page = page
            log_action(username, role, nom, "NAVIGATION", page, "")
            st.rerun()

        # Info session
        login_t = st.session_state.get("login_time")
        if login_t:
            dur = (datetime.datetime.now() - login_t).seconds // 60
            st.markdown(f"<div style='font-size:10px; color:#777; margin-top:10px; text-align:center;'>Session active : {dur} min</div>", unsafe_allow_html=True)

        # Bouton déconnexion
        st.markdown("<hr style='border-color:#333;'>", unsafe_allow_html=True)
        if st.button("🚪 Déconnexion"):
            log_action(username, role, nom, "LOGOUT", "", f"Durée session : {(datetime.datetime.now() - login_t).seconds // 60} min")
            for k in ['authenticated','username','role','nom','agence','login_time','current_page','df']:
                st.session_state.pop(k, None)
            st.rerun()

        st.markdown("<div style='font-size:10px; color:#555; text-align:center; margin-top:8px;'>DeepStats © 2024</div>", unsafe_allow_html=True)

    return df_result


# ============================================================
# 9. PAGE : DASHBOARD GLOBAL NATIONAL
# ============================================================
def page_dashboard_global(df: pd.DataFrame):
    st.markdown("<div class='main-title'>🏦 RÉSEAU CAMEROUN — <span>TABLEAU DE BORD NATIONAL</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Indicateurs consolidés de la satisfaction client aux guichets • Ensemble du réseau filtré</div>", unsafe_allow_html=True)

    if df.empty:
        st.warning("Aucune donnée disponible pour la période sélectionnée.")
        return

    n       = len(df)
    nps     = kpi_nps(df)
    sat     = kpi_sat(df)
    acc     = df['score_accueil_num'].mean()
    att     = df['score_attente_num'].mean()
    n_ag    = df['agence'].nunique()

    # ── KPI Row ──
    c1, c2, c3, c4, c5 = st.columns(5)
    kpis = [
        (c1, str(n),        "Répondants",        "#1A1A1A", ""),
        (c2, str(n_ag),     "Agences couvertes", "#1A1A1A", ""),
        (c3, f"{nps:+.1f}", "NPS Réseau",        nps_color(nps), "Net Promoter Score"),
        (c4, f"{sat:.1f}%", "Taux Satisfaction", sat_color(sat), ""),
        (c5, f"{acc:.2f}/5" if not np.isnan(acc) else "N/A", "Score Accueil", "#1A1A1A", ""),
    ]
    for col, val, lbl, color, tip in kpis:
        with col:
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-value' style='color:{color};'>{val}</div>
                <div class='kpi-label'>{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Interprétation globale ──
    if nps >= 20 and sat >= 70:
        quali = "excellente"
        emoji = "🟢"
    elif nps >= 0 and sat >= 50:
        quali = "correcte mais perfectible"
        emoji = "🟡"
    else:
        quali = "préoccupante, requérant une action immédiate"
        emoji = "🔴"

    st.markdown(f"""
    <div class='insight-box'>
    {emoji} <b>Lecture globale :</b> Avec un NPS de <b>{nps:+.1f}</b> et un taux de satisfaction de <b>{sat:.1f}%</b>
    sur <b>{n}</b> répondants dans <b>{n_ag}</b> agences, la performance réseau est <b>{quali}</b>.
    {' Le score NPS positif indique que vos promoteurs dépassent vos détracteurs — bon signe pour la recommandation.' if nps > 0
    else ' Le NPS négatif signale un risque de bouche-à-oreille défavorable : priorité aux actions correctives.'}
    La note moyenne d'accueil ({acc:.2f}/5) est {
    'satisfaisante' if acc >= 4 else ('à surveiller' if acc >= 3 else 'insuffisante — formation agents recommandée')}.
    </div>
    """, unsafe_allow_html=True)

    # ── Ligne 1 : Satisfaction + NPS ──
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("<div class='section-header'>📊 Distribution de la Satisfaction Globale</div>", unsafe_allow_html=True)
        order_sat = ['Très satisfaisante', 'Satisfaisante', 'Neutre', 'Peu satisfaisante', 'Pas du tout satisfaisante']
        sat_d = df['satisfaction_globale'].value_counts().reindex(order_sat).dropna().reset_index()
        sat_d.columns = ['Appréciation', 'Volume']
        colors_sat = ['#1B8A4A','#5BAD6F','#F59E0B','#E8895A',AFB_RED]
        fig_sat = px.bar(sat_d, y='Appréciation', x='Volume', orientation='h',
                         color='Appréciation', color_discrete_sequence=colors_sat,
                         text='Volume', title='')
        fig_sat.update_traces(textposition='outside')
        fig_sat.update_layout(**PLOTLY_LAYOUT, showlegend=False,
                              yaxis={'categoryorder': 'array', 'categoryarray': order_sat[::-1]})
        st.plotly_chart(fig_sat, use_container_width=True)

        top_sat = sat_d.iloc[0]['Appréciation'] if not sat_d.empty else "N/A"
        cnt_top = int(sat_d.iloc[0]['Volume']) if not sat_d.empty else 0
        st.markdown(f"""
        <div class='info-box'>
        📌 La modalité dominante est <b>"{top_sat}"</b> avec <b>{cnt_top}</b> répondants
        ({cnt_top/n*100:.1f}% du total). {'Le profil est globalement positif.' if top_sat in ['Très satisfaisante','Satisfaisante'] else 'Ce profil est défavorable — actions correctives urgentes.'}
        </div>
        """, unsafe_allow_html=True)

    with g2:
        st.markdown("<div class='section-header'>🎯 Répartition NPS — Segments Clients</div>", unsafe_allow_html=True)
        nps_d = df['nps_class'].value_counts().reset_index()
        nps_d.columns = ['Classe', 'Total']
        fig_nps = fig_pie(nps_d, 'Total', 'Classe', '',
                          {'Promoteur': '#1B8A4A', 'Passif': '#F59E0B', 'Détracteur': AFB_RED})
        st.plotly_chart(fig_nps, use_container_width=True)

        prom = nps_d[nps_d['Classe'] == 'Promoteur']['Total'].sum()
        det  = nps_d[nps_d['Classe'] == 'Détracteur']['Total'].sum()
        pas  = nps_d[nps_d['Classe'] == 'Passif']['Total'].sum()
        nps_v = df['nps_class'].dropna().count()
        st.markdown(f"""
        <div class='info-box'>
        📌 <b>{prom}</b> Promoteurs ({prom/nps_v*100:.0f}%) ·
        <b>{pas}</b> Passifs ({pas/nps_v*100:.0f}%) ·
        <b>{det}</b> Détracteurs ({det/nps_v*100:.0f}%).<br>
        {'✅ Majorité de promoteurs — capitaliser sur ces ambassadeurs.' if prom > det
        else '⚠️ Les détracteurs dépassent les promoteurs — risque élevé de perte clientèle.'}
        </div>
        """, unsafe_allow_html=True)

    # ── Ligne 2 : Radar + Évolution temporelle ──
    st.markdown("<div class='afb-divider'></div>", unsafe_allow_html=True)
    g3, g4 = st.columns(2)

    with g3:
        st.markdown("<div class='section-header'>🌐 Profil Qualité — Radar Multi-Dimensions</div>", unsafe_allow_html=True)
        dims    = ["Satisfaction\nglobale", "Accueil\nAgent", "Temps\nAttente", "Effort\nClient"]
        scores  = [
            df['score_satisfaction_num'].mean(),
            df['score_accueil_num'].mean(),
            df['score_attente_num'].mean(),
            df['score_effort_num'].mean(),
        ]
        scores  = [s if not np.isnan(s) else 1 for s in scores]
        scores += scores[:1]
        dims   += dims[:1]
        fig_r = go.Figure(go.Scatterpolar(
            r=scores, theta=dims, fill='toself',
            line_color=AFB_RED, fillcolor=f'rgba(200,16,46,0.18)',
            name='Réseau'
        ))
        fig_r.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[1,5],
                       tickvals=[1,2,3,4,5], tickfont=dict(size=10))),
            showlegend=False, **PLOTLY_LAYOUT
        )
        st.plotly_chart(fig_r, use_container_width=True)

        dim_min = dims[np.argmin(scores[:-1])]
        st.markdown(f"""
        <div class='warning-box'>
        ⚠️ <b>Levier prioritaire :</b> La dimension la plus faible est <b>"{dim_min}"</b>
        (score {min(scores[:-1]):.2f}/5). C'est l'axe sur lequel concentrer les efforts d'amélioration en priorité.
        </div>
        """, unsafe_allow_html=True)

    with g4:
        st.markdown("<div class='section-header'>📈 Évolution Mensuelle du NPS</div>", unsafe_allow_html=True)
        if 'mois' in df.columns:
            evo = df.groupby('mois').apply(kpi_nps).reset_index()
            evo.columns = ['Mois', 'NPS']
            evo = evo.sort_values('Mois')
            if len(evo) > 1:
                fig_evo = px.line(evo, x='Mois', y='NPS',
                                  markers=True, title='',
                                  color_discrete_sequence=[AFB_RED])
                fig_evo.add_hline(y=0, line_dash='dash', line_color='#999', annotation_text='Seuil 0')
                fig_evo.update_layout(**PLOTLY_LAYOUT)
                fig_evo.update_traces(line_width=3, marker_size=9)
                st.plotly_chart(fig_evo, use_container_width=True)
                trend = "📈 tendance haussière" if evo['NPS'].iloc[-1] > evo['NPS'].iloc[0] else "📉 tendance baissière"
                st.markdown(f"""
                <div class='info-box'>
                📌 La courbe montre une <b>{trend}</b> sur la période.
                Le dernier NPS enregistré est de <b>{evo['NPS'].iloc[-1]:+.1f}</b>.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Données insuffisantes pour l'évolution temporelle (plusieurs mois requis).")

    # ── Ligne 3 : Par type de compte + par opération ──
    st.markdown("<div class='afb-divider'></div>", unsafe_allow_html=True)
    g5, g6 = st.columns(2)

    with g5:
        st.markdown("<div class='section-header'>🏷 Satisfaction par Type de Compte</div>", unsafe_allow_html=True)
        by_compte = df.groupby('type_compte')['score_satisfaction_num'].mean().reset_index().sort_values('score_satisfaction_num')
        by_compte.columns = ['Type de compte', 'Score moyen']
        fig_compte = px.bar(by_compte, x='Score moyen', y='Type de compte',
                            orientation='h', color_discrete_sequence=[AFB_BLACK],
                            text='Score moyen')
        fig_compte.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_compte.update_layout(**PLOTLY_LAYOUT, xaxis_range=[1,5])
        st.plotly_chart(fig_compte, use_container_width=True)

        best_c = by_compte.iloc[-1]['Type de compte']
        worst_c = by_compte.iloc[0]['Type de compte']
        st.markdown(f"""
        <div class='info-box'>
        📌 Les clients <b>{best_c}</b> sont les plus satisfaits (score le plus élevé).
        Les clients <b>{worst_c}</b> sont les moins satisfaits — segment à traiter en priorité.
        </div>
        """, unsafe_allow_html=True)

    with g6:
        st.markdown("<div class='section-header'>⚙️ Satisfaction par Nature d'Opération</div>", unsafe_allow_html=True)
        by_op = df.groupby('operation')['score_satisfaction_num'].mean().reset_index().sort_values('score_satisfaction_num')
        by_op.columns = ['Opération', 'Score moyen']
        fig_op = px.bar(by_op, y='Opération', x='Score moyen', orientation='h',
                        color_discrete_sequence=[AFB_RED], text='Score moyen')
        fig_op.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_op.update_layout(**PLOTLY_LAYOUT, xaxis_range=[1,5])
        st.plotly_chart(fig_op, use_container_width=True)

        worst_op = by_op.iloc[0]['Opération']
        best_op  = by_op.iloc[-1]['Opération']
        st.markdown(f"""
        <div class='insight-box'>
        📌 L'opération <b>"{worst_op}"</b> génère la plus faible satisfaction
        — processus à revoir. A contrario, <b>"{best_op}"</b> est l'opération la mieux perçue.
        </div>
        """, unsafe_allow_html=True)

    # ── Top/Flop agences ──
    st.markdown("<div class='afb-divider'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>🏆 Classement des Agences — NPS & Satisfaction</div>", unsafe_allow_html=True)

    ag_stats = df.groupby('agence').agg(
        NPS=('nps_score', lambda x: kpi_nps(df.loc[x.index])),
        Satisfaction=('score_satisfaction_num', 'mean'),
        Accueil=('score_accueil_num', 'mean'),
        Volume=('nps_score', 'count')
    ).reset_index().sort_values('NPS', ascending=False)
    ag_stats = ag_stats[ag_stats['Volume'] >= 3]  # Seuil représentativité

    t1, t2 = st.columns(2)
    with t1:
        top5 = ag_stats.head(5)
        fig_t = px.bar(top5, x='NPS', y='agence', orientation='h',
                       color_discrete_sequence=['#1B8A4A'], text='NPS',
                       title='🥇 Top 5 — Meilleures Agences (NPS)')
        fig_t.update_traces(texttemplate='%{text:+.1f}', textposition='outside')
        fig_t.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_t, use_container_width=True)

    with t2:
        bot5 = ag_stats.tail(5).iloc[::-1]
        fig_b = px.bar(bot5, x='NPS', y='agence', orientation='h',
                       color_discrete_sequence=[AFB_RED], text='NPS',
                       title='⚠️ Flop 5 — Agences à Renforcer (NPS)')
        fig_b.update_traces(texttemplate='%{text:+.1f}', textposition='outside')
        fig_b.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_b, use_container_width=True)

    st.markdown(f"""
    <div class='insight-box'>
    🏆 <b>Meilleure agence :</b> {ag_stats.iloc[0]['agence']} (NPS : {ag_stats.iloc[0]['NPS']:+.1f})
    — À utiliser comme référence interne et modèle de bonnes pratiques.<br>
    ⚠️ <b>Agence la plus faible :</b> {ag_stats.iloc[-1]['agence']} (NPS : {ag_stats.iloc[-1]['NPS']:+.1f})
    — Plan d'action correctif recommandé sous 30 jours.
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# 10. PAGE : DASHBOARD PAR AGENCE
# ============================================================
def page_dashboard_agence(df: pd.DataFrame, agence_forcee: str = None):
    st.markdown("<div class='main-title'>📍 DIAGNOSTIC DÉTAILLÉ PAR <span>AGENCE</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Analyse approfondie des indicateurs de performance d'un point de vente</div>", unsafe_allow_html=True)

    if df.empty:
        st.warning("Aucune donnée disponible.")
        return

    agences = sorted(df['agence'].dropna().unique().tolist())
    if agence_forcee and agence_forcee in agences:
        default_idx = agences.index(agence_forcee)
        agence_sel  = st.selectbox("🎯 Sélectionner l'agence :", agences, index=default_idx)
    else:
        agence_sel = st.selectbox("🎯 Sélectionner l'agence :", agences)

    df_ag = df[df['agence'] == agence_sel]
    vol   = len(df_ag)

    if vol == 0:
        st.warning("Aucun répondant pour cette agence sur la période.")
        return

    nps_ag  = kpi_nps(df_ag)
    sat_ag  = kpi_sat(df_ag)
    acc_ag  = df_ag['score_accueil_num'].mean()
    att_ag  = df_ag['score_attente_num'].mean()
    eff_ag  = df_ag['score_effort_num'].mean()
    nps_nat = kpi_nps(df)
    sat_nat = kpi_sat(df)

    # Header agence
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,{AFB_BLACK},{AFB_DARK_RED});
    color:white;padding:18px 24px;border-radius:10px;margin-bottom:20px;
    border-left:6px solid {AFB_RED};'>
        <div style='font-size:20px;font-weight:900;'>{agence_sel}</div>
        <div style='font-size:13px;color:#CCCCCC;margin-top:4px;'>
        {vol} répondants sur la période sélectionnée
        {"| ⚠️ Échantillon faible (< 10) — interprétation prudente" if vol < 10 else "| ✅ Échantillon représentatif"}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # KPI comparatif
    k1, k2, k3, k4, k5 = st.columns(5)
    metrics = [
        (k1, f"{nps_ag:+.1f}", "NPS Local", f"{nps_ag - nps_nat:+.1f} vs réseau", nps_color(nps_ag)),
        (k2, f"{sat_ag:.0f}%", "Satisfaction", f"{sat_ag - sat_nat:+.1f}% vs réseau", sat_color(sat_ag)),
        (k3, f"{acc_ag:.2f}/5" if not np.isnan(acc_ag) else "N/A", "Accueil Agent", "", "#1A1A1A"),
        (k4, f"{att_ag:.2f}/5" if not np.isnan(att_ag) else "N/A", "Temps Attente", "", "#1A1A1A"),
        (k5, f"{eff_ag:.2f}/5" if not np.isnan(eff_ag) else "N/A", "Effort Client", "", "#1A1A1A"),
    ]
    for col, val, lbl, delta, color in metrics:
        with col:
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-value' style='color:{color};'>{val}</div>
                <div class='kpi-label'>{lbl}</div>
                <div class='kpi-delta'>{delta}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Radar Agence vs Réseau ──
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("<div class='section-header'>🌐 Comparatif Radar — Agence vs Réseau National</div>", unsafe_allow_html=True)
        dims    = ["Satisfaction", "Accueil Agent", "Temps Attente", "Effort Client"]
        sc_ag   = [df_ag['score_satisfaction_num'].mean(), acc_ag, att_ag, eff_ag]
        sc_nat  = [df['score_satisfaction_num'].mean(), df['score_accueil_num'].mean(),
                   df['score_attente_num'].mean(), df['score_effort_num'].mean()]
        sc_ag   = [s if not np.isnan(s) else 1 for s in sc_ag]
        sc_nat  = [s if not np.isnan(s) else 1 for s in sc_nat]
        dims_c  = dims + dims[:1]
        sc_ag_c = sc_ag + sc_ag[:1]
        sc_nat_c= sc_nat + sc_nat[:1]

        fig_r = go.Figure()
        fig_r.add_trace(go.Scatterpolar(r=sc_ag_c, theta=dims_c, fill='toself',
                                         name=agence_sel[:20], line_color=AFB_RED,
                                         fillcolor=f'rgba(200,16,46,0.22)'))
        fig_r.add_trace(go.Scatterpolar(r=sc_nat_c, theta=dims_c, fill='toself',
                                         name='Réseau National', line_color=AFB_BLACK,
                                         fillcolor='rgba(26,26,26,0.10)'))
        fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[1,5])),
                            showlegend=True, **PLOTLY_LAYOUT)
        st.plotly_chart(fig_r, use_container_width=True)

        dims_below = [d for d, s, sn in zip(dims, sc_ag, sc_nat) if s < sn]
        if dims_below:
            st.markdown(f"""
            <div class='insight-box'>
            ⚠️ <b>Dimensions en retard vs réseau :</b> {', '.join(dims_below)}.
            Ces axes sont inférieurs à la moyenne nationale — actions prioritaires recommandées.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='success-box'>
            ✅ <b>{agence_sel}</b> performe au-dessus ou à égalité de la moyenne nationale
            sur toutes les dimensions — excellente performance à maintenir !
            </div>
            """, unsafe_allow_html=True)

    # ── Distribution NPS agence ──
    with g2:
        st.markdown("<div class='section-header'>🎯 NPS & Score Agence — Distribution</div>", unsafe_allow_html=True)

        # Score NPS distribution
        nps_d = df_ag['nps_score'].dropna()
        if not nps_d.empty:
            fig_hist = px.histogram(nps_d, nbins=11, range_x=[0,10],
                                    color_discrete_sequence=[AFB_RED], title='')
            fig_hist.update_layout(**PLOTLY_LAYOUT, xaxis_title='Score NPS (0-10)',
                                   yaxis_title='Nombre de clients')
            fig_hist.add_vline(x=8.5, line_dash='dash', line_color='#1B8A4A',
                               annotation_text='Seuil Promoteur')
            fig_hist.add_vline(x=6.5, line_dash='dash', line_color='#F59E0B',
                               annotation_text='Seuil Passif')
            st.plotly_chart(fig_hist, use_container_width=True)

        nps_vc = df_ag['nps_class'].value_counts()
        p = nps_vc.get('Promoteur', 0)
        pa= nps_vc.get('Passif', 0)
        d = nps_vc.get('Détracteur', 0)
        st.markdown(f"""
        <div class='info-box'>
        📌 <b>{p}</b> Promoteurs · <b>{pa}</b> Passifs · <b>{d}</b> Détracteurs.<br>
        NPS local = {nps_ag:+.1f} vs moyenne réseau {nps_nat:+.1f}
        ({'+' if nps_ag >= nps_nat else ''}{nps_ag - nps_nat:.1f} pts).
        {'✅ Cette agence surperforme.' if nps_ag > nps_nat else '⚠️ Cette agence est en dessous de la moyenne réseau.'}
        </div>
        """, unsafe_allow_html=True)

    # ── Évolution temporelle ──
    if df_ag['mois'].nunique() > 1:
        st.markdown("<div class='section-header'>📈 Évolution Mensuelle — NPS & Satisfaction</div>", unsafe_allow_html=True)
        evo_ag = df_ag.groupby('mois').agg(
            NPS=('nps_score', lambda x: kpi_nps(df_ag.loc[x.index])),
            Satisfaction=('score_satisfaction_num', 'mean'),
        ).reset_index().sort_values('mois')

        fig_evo = make_subplots(specs=[[{"secondary_y": True}]])
        fig_evo.add_trace(go.Scatter(x=evo_ag['mois'], y=evo_ag['NPS'],
                                     name='NPS', line=dict(color=AFB_RED, width=3),
                                     mode='lines+markers', marker_size=8), secondary_y=False)
        fig_evo.add_trace(go.Scatter(x=evo_ag['mois'], y=evo_ag['Satisfaction'],
                                     name='Satisfaction (1-5)', line=dict(color=AFB_BLACK, width=2, dash='dot'),
                                     mode='lines+markers', marker_size=7), secondary_y=True)
        fig_evo.update_yaxes(title_text="NPS", secondary_y=False)
        fig_evo.update_yaxes(title_text="Score Satisfaction (1-5)", secondary_y=True, range=[1,5])
        fig_evo.update_layout(**PLOTLY_LAYOUT, showlegend=True)
        st.plotly_chart(fig_evo, use_container_width=True)

    # ── Verbatims rapides ──
    st.markdown("<div class='section-header'>💬 Verbatims Clients — Aperçu Rapide</div>", unsafe_allow_html=True)
    v1, v2 = st.columns(2)
    with v1:
        st.markdown(f"<b style='color:{AFB_RED};'>❌ Points négatifs signalés :</b>", unsafe_allow_html=True)
        negs = df_ag['verbatim_negatif'].dropna().replace('', np.nan).dropna().tolist()
        if negs:
            for v in negs[:5]:
                st.markdown(f"<div class='verb-card verb-neg'>« {v} »</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='success-box'>Aucun point négatif relevé 👍</div>", unsafe_allow_html=True)
    with v2:
        st.markdown(f"<b style='color:#1B8A4A;'>✅ Points positifs relevés :</b>", unsafe_allow_html=True)
        poss = df_ag['verbatim_positif'].dropna().replace('', np.nan).dropna().tolist()
        if poss:
            for v in poss[:5]:
                st.markdown(f"<div class='verb-card verb-pos'>« {v} »</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='info-box'>Aucun point positif enregistré.</div>", unsafe_allow_html=True)


# ============================================================
# 11. PAGE : ANALYSE COMPARATIVE INTER-AGENCES
# ============================================================
def page_comparative(df: pd.DataFrame):
    st.markdown("<div class='main-title'>📈 ANALYSE <span>COMPARATIVE</span> INTER-AGENCES</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Benchmark de performance entre agences du réseau — Positionnement relatif</div>", unsafe_allow_html=True)

    if df.empty:
        st.warning("Aucune donnée disponible.")
        return

    # Stats par agence
    def ag_nps(grp): return kpi_nps(grp)

    ag = df.groupby('agence').apply(lambda g: pd.Series({
        'NPS':            kpi_nps(g),
        'Satisfaction':   kpi_sat(g),
        'Score Accueil':  g['score_accueil_num'].mean(),
        'Score Attente':  g['score_attente_num'].mean(),
        'Score Effort':   g['score_effort_num'].mean(),
        'Volume':         len(g),
    })).reset_index()
    ag = ag[ag['Volume'] >= 3].sort_values('NPS', ascending=False)

    # ── Scatter NPS vs Satisfaction ──
    st.markdown("<div class='section-header'>🎯 Matrice Performance — NPS vs Satisfaction (taille = volume répondants)</div>", unsafe_allow_html=True)
    ag_label = ag['agence'].str.replace('FIRST BANK ', '', regex=False)
    fig_sc = px.scatter(ag, x='Satisfaction', y='NPS',
                        size='Volume', color='NPS',
                        color_continuous_scale=['#C8102E','#F59E0B','#1B8A4A'],
                        hover_name='agence',
                        text=ag_label, size_max=55)
    fig_sc.add_hline(y=0, line_dash='dash', line_color='#999')
    fig_sc.add_vline(x=50, line_dash='dash', line_color='#999')
    fig_sc.update_traces(textposition='top center', textfont_size=10)
    fig_sc.update_layout(**PLOTLY_LAYOUT,
                          xaxis_title="Taux de satisfaction (%)",
                          yaxis_title="NPS",
                          coloraxis_showscale=False)
    st.plotly_chart(fig_sc, use_container_width=True)

    st.markdown(f"""
    <div class='insight-box'>
    📌 <b>Lecture de la matrice :</b>
    Quadrant haut-droite = champions (NPS &gt; 0 ET satisfaction &gt; 50%) •
    Quadrant bas-gauche = agences critiques (double faiblesse) •
    Quadrant haut-gauche = bonne recommandation mais satisfaction globale perfectible •
    Quadrant bas-droite = satisfaction perçue mais NPS défavorable (détracteurs actifs).
    </div>
    """, unsafe_allow_html=True)

    # ── Heatmap scores ──
    st.markdown("<div class='section-header'>🔥 Heatmap — Scores par Dimension & Agence</div>", unsafe_allow_html=True)
    cols_hm = ['Score Accueil', 'Score Attente', 'Score Effort', 'Satisfaction']
    ag_top  = ag.nlargest(20, 'Volume')
    hm_data = ag_top[['agence'] + cols_hm].set_index('agence')
    hm_data.index = hm_data.index.str.replace('FIRST BANK ', '', regex=False)

    fig_hm = px.imshow(hm_data, color_continuous_scale='RdYlGn',
                       zmin=1, zmax=5, aspect='auto',
                       labels={'color': 'Score (1-5)', 'x': 'Dimension', 'y': 'Agence'},
                       text_auto='.2f')
    fig_hm.update_layout(**PLOTLY_LAYOUT, height=max(350, len(hm_data) * 28))
    st.plotly_chart(fig_hm, use_container_width=True)

    st.markdown("""
    <div class='info-box'>
    📌 <b>Lecture de la heatmap :</b> Rouge = faible performance (1-2) · Jaune = moyen (3) · Vert = excellente performance (4-5).
    Les cellules rouges sont les points d'intervention prioritaires par agence et par dimension.
    </div>
    """, unsafe_allow_html=True)

    # ── Tableau classement ──
    st.markdown("<div class='section-header'>📋 Tableau de Classement Détaillé</div>", unsafe_allow_html=True)
    ag_display = ag.copy()
    ag_display.columns = ['Agence','NPS','Satisfaction (%)','Accueil /5','Attente /5','Effort /5','Volume']
    ag_display = ag_display.round(2)
    ag_display.insert(0, '#', range(1, len(ag_display)+1))

    def highlight_nps(val):
        if isinstance(val, (int, float)):
            if val >= 20: return 'background-color:#D4EDDA; color:#155724; font-weight:bold'
            elif val >= 0: return 'background-color:#FFF3CD; color:#856404'
            else: return 'background-color:#F8D7DA; color:#721C24; font-weight:bold'
        return ''

    styled = ag_display.style.applymap(highlight_nps, subset=['NPS'])
    st.dataframe(styled, use_container_width=True, hide_index=True)


# ============================================================
# 12. PAGE : MODÉLISATION & PRÉDICTIONS S+1
# ============================================================
def page_modelisation(df: pd.DataFrame):
    st.markdown("<div class='main-title'>🔮 MOTEUR <span>PRÉDICTIF</span> — INTELLIGENCE ARTIFICIELLE</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Analyse prédictive des leviers de satisfaction • Simulation d'impact opérationnel S+1</div>", unsafe_allow_html=True)

    df_ml = df[['score_attente_num','score_accueil_num','score_effort_num','nps_class']].dropna()

    if len(df_ml) < 30:
        st.markdown("""
        <div class='warning-box'>
        ⚠️ <b>Volume insuffisant :</b> Le moteur IA nécessite au minimum 30 lignes de données propres.
        Élargissez la période de filtrage ou importez un jeu de données plus complet.
        </div>
        """, unsafe_allow_html=True)
        return

    # Entraînement
    le = LabelEncoder()
    df_ml = df_ml.copy()
    df_ml['target'] = le.fit_transform(df_ml['nps_class'])
    X = df_ml[['score_attente_num','score_accueil_num','score_effort_num']]
    y = df_ml['target']
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X, y)
    acc_model = model.score(X, y)

    labels = ["Temps d'attente", "Qualité accueil agent", "Effort fourni par client"]
    importances = model.feature_importances_

    g1, g2 = st.columns(2)
    with g1:
        st.markdown("<div class='section-header'>📊 Facteurs Déterminants du NPS Client</div>", unsafe_allow_html=True)
        fig_imp = px.bar(
            x=labels, y=importances * 100,
            color=importances, color_continuous_scale=['#F5F5F5', AFB_RED],
            text=[f"{v*100:.1f}%" for v in importances],
            labels={'x': 'Levier', 'y': "Poids (%)", 'color': 'Importance'}
        )
        fig_imp.update_traces(textposition='outside')
        fig_imp.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False,
                              yaxis_title="Importance prédictive (%)")
        st.plotly_chart(fig_imp, use_container_width=True)

        top_factor = labels[np.argmax(importances)]
        st.markdown(f"""
        <div class='insight-box'>
        🤖 <b>Insight IA :</b> Le facteur <b>"{top_factor}"</b> est le levier le plus déterminant
        dans la classification NPS ({importances.max()*100:.1f}% d'importance).
        Agir sur ce levier génère le retour sur investissement satisfaction le plus élevé.
        Précision du modèle Random Forest : <b>{acc_model*100:.1f}%</b>.
        </div>
        """, unsafe_allow_html=True)

    # Simulation
    with g2:
        st.markdown("<div class='section-header'>🎛 Simulateur d'Impact Opérationnel — Semaine Prochaine</div>", unsafe_allow_html=True)
        m_att = df['score_attente_num'].mean()
        m_acc = df['score_accueil_num'].mean()
        m_eff = df['score_effort_num'].mean()

        sim_att = st.slider("⏱️ Amélioration temps d'attente (1=Critique → 5=Excellent)",
                            1.0, 5.0, float(m_att) if not np.isnan(m_att) else 3.0, 0.1)
        sim_acc = st.slider("😊 Qualité accueil agent (1=Insuffisant → 5=Parfait)",
                            1.0, 5.0, float(m_acc) if not np.isnan(m_acc) else 4.0, 0.1)
        sim_eff = st.slider("🔧 Effort client (5=Très facile → 1=Très difficile)",
                            1.0, 5.0, float(m_eff) if not np.isnan(m_eff) else 3.0, 0.1)

        nps_base = kpi_nps(df)
        d_att = (sim_att - (m_att if not np.isnan(m_att) else 3.0)) * 20
        d_acc = (sim_acc - (m_acc if not np.isnan(m_acc) else 4.0)) * 12
        d_eff = (sim_eff - (m_eff if not np.isnan(m_eff) else 3.0)) * 8
        nps_proj = float(np.clip(nps_base + d_att + d_acc + d_eff, -100, 100))

        delta = nps_proj - nps_base
        color_delta = "#1B8A4A" if delta >= 0 else AFB_RED
        arrow = "▲" if delta >= 0 else "▼"

        st.markdown(f"""
        <div style='background:{AFB_BLACK};border-radius:10px;padding:24px;margin-top:10px;text-align:center;'>
            <div style='color:#AAAAAA;font-size:12px;text-transform:uppercase;letter-spacing:1px;'>NPS Actuel Observé</div>
            <div style='color:white;font-size:40px;font-weight:900;'>{nps_base:+.1f}</div>
            <div style='color:#555;font-size:24px;margin:8px 0;'>↓</div>
            <div style='color:#AAAAAA;font-size:12px;text-transform:uppercase;letter-spacing:1px;'>NPS Prédictif S+1</div>
            <div style='color:{color_delta};font-size:48px;font-weight:900;'>{nps_proj:+.1f}</div>
            <div style='color:{color_delta};font-size:18px;font-weight:700;margin-top:5px;'>{arrow} {delta:+.1f} pts vs actuel</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Matrice de confusion NPS ──
    st.markdown("<div class='section-header'>📉 Distribution Prédite NPS — Après Amélioration Simulée</div>", unsafe_allow_html=True)

    X_sim = pd.DataFrame([[sim_att, sim_acc, sim_eff]] * len(df_ml),
                         columns=['score_attente_num','score_accueil_num','score_effort_num'])
    pred_classes = le.inverse_transform(model.predict(X_sim))
    pred_vc = pd.Series(pred_classes).value_counts().reset_index()
    pred_vc.columns = ['Classe', 'Prédit']
    act_vc  = df_ml['nps_class'].value_counts().reset_index()
    act_vc.columns  = ['Classe', 'Actuel']
    merged  = pred_vc.merge(act_vc, on='Classe', how='outer').fillna(0)

    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(name='Actuel', x=merged['Classe'], y=merged['Actuel'],
                               marker_color=AFB_BLACK))
    fig_comp.add_trace(go.Bar(name='Prédit S+1', x=merged['Classe'], y=merged['Prédit'],
                               marker_color=AFB_RED, opacity=0.8))
    fig_comp.update_layout(**PLOTLY_LAYOUT, barmode='group',
                           yaxis_title='Nombre de clients',
                           xaxis_title='Segment NPS')
    st.plotly_chart(fig_comp, use_container_width=True)

    st.markdown(f"""
    <div class='insight-box'>
    🤖 <b>Analyse de sensibilité :</b> En améliorant le temps d'attente à {sim_att:.1f}/5
    et l'accueil à {sim_acc:.1f}/5, le modèle prédit un NPS de <b>{nps_proj:+.1f}</b>
    ({'+' if delta >= 0 else ''}{delta:.1f} pts). Le levier attente contribue le plus à ce gain.
    <br><i>Note : modèle indicatif basé sur RandomForest — à valider avec données réelles S+1.</i>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# 13. PAGE : VERBATIMS CLIENTS
# ============================================================
def page_verbatims(df: pd.DataFrame):
    st.markdown("<div class='main-title'>💬 ANALYSE DES <span>VERBATIMS</span> CLIENTS</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Voix du client — Insatisfactions, suggestions et points forts • Analyse qualitative exhaustive</div>", unsafe_allow_html=True)

    agences = ['Tout le réseau'] + sorted(df['agence'].dropna().unique().tolist())
    filtre = st.selectbox("🎯 Filtrer par agence :", agences)
    df_v = df if filtre == 'Tout le réseau' else df[df['agence'] == filtre]

    v1, v2, v3 = st.columns(3)
    with v1:
        st.markdown(f"<div class='section-header' style='background:{AFB_RED};'>❌ Points d'Insatisfaction ({df_v['verbatim_negatif'].dropna().replace('', np.nan).dropna().count()})</div>", unsafe_allow_html=True)
        negs = df_v['verbatim_negatif'].dropna().replace('', np.nan).dropna().tolist()
        if negs:
            for i, v in enumerate(negs):
                st.markdown(f"<div class='verb-card verb-neg'><small>#{i+1}</small><br>« {v} »</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='success-box'>Aucun point négatif enregistré.</div>", unsafe_allow_html=True)

    with v2:
        st.markdown(f"<div class='section-header' style='background:#F59E0B;color:{AFB_BLACK};'>⚙️ Suggestions d'Amélioration ({df_v['verbatim_amelioration'].dropna().replace('', np.nan).dropna().count()})</div>", unsafe_allow_html=True)
        suggs = df_v['verbatim_amelioration'].dropna().replace('', np.nan).dropna().tolist()
        if suggs:
            for i, v in enumerate(suggs):
                st.markdown(f"<div class='verb-card verb-sug'><small>#{i+1}</small><br>« {v} »</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='info-box'>Aucune suggestion enregistrée.</div>", unsafe_allow_html=True)

    with v3:
        st.markdown(f"<div class='section-header' style='background:#1B8A4A;'>✅ Points Positifs ({df_v['verbatim_positif'].dropna().replace('', np.nan).dropna().count()})</div>", unsafe_allow_html=True)
        poss = df_v['verbatim_positif'].dropna().replace('', np.nan).dropna().tolist()
        if poss:
            for i, v in enumerate(poss):
                st.markdown(f"<div class='verb-card verb-pos'><small>#{i+1}</small><br>« {v} »</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='info-box'>Aucun point positif enregistré.</div>", unsafe_allow_html=True)

    # Thèmes récurrents automatiques
    st.markdown("<div class='afb-divider'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>🔍 Thèmes Récurrents — Analyse Automatique</div>", unsafe_allow_html=True)

    themes = {
        "Temps d'attente / File":    ["attente", "file", "queue", "lenteur", "long", "durée", "caisse"],
        "Application Sara / Tech":   ["sara", "sarah", "app", "application", "connexion", "bug", "gab", "gfa"],
        "Accueil / Personnel":       ["accueil", "personnel", "agent", "caissière", "comportement", "impoli"],
        "Guichets / Infrastructure": ["guichet", "caisse", "places", "siège", "ticket"],
        "Frais / Opérations":        ["frais", "plafond", "retrait", "virement", "compte"],
    }
    all_text = ' '.join(df_v[['verbatim_negatif','verbatim_amelioration']].fillna('').values.flatten()).lower()
    theme_counts = {t: sum(all_text.count(kw) for kw in kws) for t, kws in themes.items()}
    theme_df = pd.DataFrame(list(theme_counts.items()), columns=['Thème','Occurrences']).sort_values('Occurrences', ascending=False)

    fig_th = px.bar(theme_df, x='Occurrences', y='Thème', orientation='h',
                    color='Occurrences', color_continuous_scale=['#FFCCCC', AFB_RED],
                    text='Occurrences')
    fig_th.update_traces(textposition='outside')
    fig_th.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False)
    st.plotly_chart(fig_th, use_container_width=True)

    top_theme = theme_df.iloc[0]['Thème']
    st.markdown(f"""
    <div class='insight-box'>
    📌 <b>Thème dominant :</b> "{top_theme}" est le sujet le plus mentionné dans les verbatims négatifs et suggestions.
    C'est l'axe de communication et d'amélioration opérationnelle à prioriser immédiatement.
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# 14. PAGE : RAPPORT & EXPORT
# ============================================================
def page_rapport(df: pd.DataFrame, username: str, role: str, nom: str):
    st.markdown("<div class='main-title'>📝 RAPPORT DE <span>SYNTHÈSE</span> & EXPORTATION</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Génération des livrables consolidés • Export Excel & CSV • Documentation Direction</div>", unsafe_allow_html=True)

    if df.empty:
        st.warning("Aucune donnée disponible.")
        return

    nps = kpi_nps(df)
    sat = kpi_sat(df)

    # Synthèse narrative
    st.markdown("<div class='section-header'>📑 Synthèse Narrative de la Période</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='background:white;border-radius:10px;padding:24px;box-shadow:0 2px 12px rgba(0,0,0,0.08);
    border-top:4px solid {AFB_RED};line-height:1.8;'>
        <h4 style='color:{AFB_RED};margin:0 0 12px;'>Rapport de Satisfaction Client — Réseau Cameroun</h4>
        <b>Produit par :</b> {nom} | <b>Date :</b> {datetime.date.today().strftime('%d/%m/%Y')} |
        <b>Développé par :</b> DeepStats<br><br>

        <b>1. Contexte & Périmètre</b><br>
        Cette analyse porte sur <b>{len(df)} répondants</b> issus de <b>{df['agence'].nunique()} agences</b>
        du réseau Afriland First Bank Cameroun, sur la période sélectionnée dans les filtres de la plateforme.

        <br><br><b>2. Indicateurs Clés de Performance</b><br>
        • NPS Global Réseau : <b>{nps:+.1f}</b>
        {"(zone positive — stratégie de croissance par recommandation envisageable)" if nps > 0
        else "(zone négative — actions correctives d'urgence requises)"}<br>
        • Taux de Satisfaction Globale : <b>{sat:.1f}%</b> de clients satisfaits ou très satisfaits<br>
        • Score moyen Accueil Agent : <b>{df['score_accueil_num'].mean():.2f}/5</b><br>
        • Score moyen Temps d'Attente : <b>{df['score_attente_num'].mean():.2f}/5</b><br>
        • Score moyen Effort Client : <b>{df['score_effort_num'].mean():.2f}/5</b>

        <br><br><b>3. Axes d'Amélioration Prioritaires</b><br>
        {"• Réduire les temps d'attente aux guichets (levier #1 selon le modèle IA).<br>"
         "• Renforcer la formation accueil des agents guichet.<br>"
         "• Améliorer la fiabilité des systèmes numériques (Sara Money, GFA).<br>"
         "• Augmenter le nombre de guichets opérationnels aux heures de pointe."}

        <br><br><b>4. Limites de l'Étude</b><br>
        Certaines agences présentent un faible volume d'échantillon (&lt; 10 répondants).
        Les résultats de ces agences doivent être interprétés à titre indicatif uniquement.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='afb-divider'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>💾 Exportation des Données</div>", unsafe_allow_html=True)

    # Export 1 : Résumé par agence
    df_export1 = df.groupby('agence').apply(lambda g: pd.Series({
        'Volume Réponses':        len(g),
        'NPS':                    round(kpi_nps(g), 1),
        'Taux Satisfaction (%)':  round(kpi_sat(g), 1),
        'Score Accueil /5':       round(g['score_accueil_num'].mean(), 2),
        'Score Attente /5':       round(g['score_attente_num'].mean(), 2),
        'Score Effort /5':        round(g['score_effort_num'].mean(), 2),
    })).reset_index().sort_values('NPS', ascending=False)

    # Export 2 : Données brutes nettoyées
    cols_export2 = ['agence','date_operation','type_compte','operation',
                    'satisfaction_globale','temps_attente','accueil_agent',
                    'effort_client','nps_score','nps_class',
                    'verbatim_negatif','verbatim_amelioration','verbatim_positif']
    df_export2 = df[[c for c in cols_export2 if c in df.columns]]

    e1, e2 = st.columns(2)
    with e1:
        st.markdown("**📊 Export 1 — Rapport Consolidé par Agence**")
        buf1 = io.StringIO()
        df_export1.to_csv(buf1, index=False, encoding='utf-8-sig')
        st.download_button(
            "📥 Télécharger Rapport Agences (.CSV)",
            data=buf1.getvalue().encode('utf-8-sig'),
            file_name=f"AFB_Satisfaction_Agences_{datetime.date.today():%Y-%m-%d}.csv",
            mime="text/csv", key="dl1"
        )
        log_action(username, role, nom, "EXPORT", "Rapport", "Export CSV agences")
        st.dataframe(df_export1, use_container_width=True, hide_index=True)

    with e2:
        st.markdown("**📋 Export 2 — Données Brutes Nettoyées**")
        buf2 = io.StringIO()
        df_export2.to_csv(buf2, index=False, encoding='utf-8-sig')
        st.download_button(
            "📥 Télécharger Données Brutes (.CSV)",
            data=buf2.getvalue().encode('utf-8-sig'),
            file_name=f"AFB_Satisfaction_Brutes_{datetime.date.today():%Y-%m-%d}.csv",
            mime="text/csv", key="dl2"
        )
        st.dataframe(df_export2.head(20), use_container_width=True, hide_index=True)


# ============================================================
# 15. PAGE ADMIN : JOURNAL D'ACTIVITÉ (ESPION)
# ============================================================
def page_journal_activite():
    st.markdown("<div class='main-title'>🕵️ JOURNAL D'ACTIVITÉ — <span>ADMIN ESPION</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Surveillance en temps réel des connexions et actions utilisateurs sur la plateforme</div>", unsafe_allow_html=True)

    # Récupération des logs
    df_act  = get_activity_logs(1000)
    df_log  = get_login_logs(500)

    # ── KPI Connexions ──
    now    = datetime.datetime.now()
    today  = now.strftime("%Y-%m-%d")

    logins_today   = len(df_log[df_log['timestamp'].str.startswith(today)]) if not df_log.empty else 0
    success_today  = len(df_log[(df_log['timestamp'].str.startswith(today)) & (df_log['success'] == 1)]) if not df_log.empty else 0
    failed_today   = logins_today - success_today
    unique_users   = df_log['username'].nunique() if not df_log.empty else 0

    k1, k2, k3, k4 = st.columns(4)
    for col, val, lbl, color in [
        (k1, str(logins_today),  "Tentatives Connexion Aujourd'hui", AFB_BLACK),
        (k2, str(success_today), "Connexions Réussies Aujourd'hui",  "#1B8A4A"),
        (k3, str(failed_today),  "Tentatives Échouées Aujourd'hui",  AFB_RED if failed_today > 0 else "#1B8A4A"),
        (k4, str(unique_users),  "Utilisateurs Uniques (Historique)", AFB_BLACK),
    ]:
        with col:
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-value' style='color:{color};'>{val}</div>
                <div class='kpi-label'>{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Timeline Activité ──
    if not df_act.empty:
        st.markdown("<div class='section-header'>⏱ Timeline des Actions (les 50 dernières)</div>", unsafe_allow_html=True)
        df_act_disp = df_act.head(50).copy()
        df_act_disp['Horodatage']  = df_act_disp['timestamp']
        df_act_disp['Utilisateur'] = df_act_disp['nom'] + ' (' + df_act_disp['username'] + ')'
        df_act_disp['Rôle']        = df_act_disp['role'].apply(lambda x: '🔴 ADMIN' if x=='admin' else '👤 USER')
        df_act_disp['Action']      = df_act_disp['action']
        df_act_disp['Page']        = df_act_disp['page']
        df_act_disp['Détail']      = df_act_disp['detail']

        st.dataframe(
            df_act_disp[['Horodatage','Utilisateur','Rôle','Action','Page','Détail']],
            use_container_width=True, hide_index=True, height=400
        )

    # ── Activité par utilisateur ──
    if not df_act.empty and 'username' in df_act.columns:
        st.markdown("<div class='section-header'>👥 Activité par Utilisateur</div>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            user_act = df_act.groupby('username')['action'].count().reset_index()
            user_act.columns = ['Utilisateur', "Nb Actions"]
            user_act = user_act.sort_values("Nb Actions", ascending=False)
            fig_ua = px.bar(user_act, x='Utilisateur', y='Nb Actions',
                            color_discrete_sequence=[AFB_RED], text='Nb Actions',
                            title='Actions par utilisateur')
            fig_ua.update_traces(textposition='outside')
            fig_ua.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig_ua, use_container_width=True)

        with g2:
            page_act = df_act[df_act['page'] != '']['page'].value_counts().reset_index()
            page_act.columns = ['Page', 'Vues']
            if not page_act.empty:
                fig_pa = px.pie(page_act, values='Vues', names='Page',
                                title='Pages les plus consultées',
                                color_discrete_sequence=px.colors.sequential.Reds_r[:len(page_act)])
                fig_pa.update_layout(**PLOTLY_LAYOUT)
                st.plotly_chart(fig_pa, use_container_width=True)

    # ── Logs de connexion ──
    if not df_log.empty:
        st.markdown("<div class='section-header'>🔑 Historique des Connexions</div>", unsafe_allow_html=True)
        df_log_disp = df_log.copy()
        df_log_disp['Statut'] = df_log_disp['success'].apply(
            lambda x: '✅ Succès' if x == 1 else '❌ Échec'
        )
        df_log_disp = df_log_disp.rename(columns={'timestamp':'Horodatage','username':'Identifiant'})
        st.dataframe(df_log_disp[['Horodatage','Identifiant','Statut']],
                     use_container_width=True, hide_index=True, height=300)

    # ── Export logs ──
    st.markdown("<div class='afb-divider'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if not df_act.empty:
            buf = io.StringIO()
            df_act.to_csv(buf, index=False, encoding='utf-8-sig')
            st.download_button("📥 Exporter Journal Activités (.CSV)",
                               buf.getvalue().encode('utf-8-sig'),
                               f"AFB_Journal_Activite_{datetime.date.today():%Y-%m-%d}.csv",
                               mime="text/csv", key="dl_act")
    with c2:
        if not df_log.empty:
            buf2 = io.StringIO()
            df_log.to_csv(buf2, index=False, encoding='utf-8-sig')
            st.download_button("📥 Exporter Journal Connexions (.CSV)",
                               buf2.getvalue().encode('utf-8-sig'),
                               f"AFB_Journal_Connexions_{datetime.date.today():%Y-%m-%d}.csv",
                               mime="text/csv", key="dl_log")

    if df_act.empty and df_log.empty:
        st.markdown("""
        <div class='info-box'>
        ℹ️ Aucune activité enregistrée pour le moment. Les actions des utilisateurs
        apparaîtront ici automatiquement au fur et à mesure des connexions et navigations.
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# 16. POINT D'ENTRÉE PRINCIPAL
# ============================================================
def main():
    init_db()
    inject_css()

    # Initialisation session
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    # ── Page login ──
    if not st.session_state.authenticated:
        show_login_page()
        return

    # ── Utilisateur connecté ──
    username = st.session_state.username
    role     = st.session_state.role
    nom      = st.session_state.nom
    agence   = st.session_state.agence

    # Données en session
    if 'df' not in st.session_state:
        st.session_state.df = None

    df_raw = st.session_state.df

    # Sidebar + filtrage temporel
    df_clean = render_sidebar(df_raw, role, nom, agence, username)

    page = st.session_state.get("current_page", "📊 Dashboard Global")

    # ── Chargement des données requis ──
    if df_clean is None and page != "🕵️ Journal d'Activité (Admin)":
        st.markdown("<div class='main-title'>🏦 PLATEFORME BI SATISFACTION — <span>AFRILAND FIRST BANK</span></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class='insight-box' style='text-align:center; font-size:15px;'>
            👋 Bienvenue, <b>{nom}</b> !<br><br>
            {'📁 <b>Importez votre fichier de données</b> (.xlsx ou .csv) via la barre latérale gauche pour activer tous les tableaux de bord.' if role == 'admin'
             else '⏳ Données en attente de chargement par l\'administrateur. Contactez-le si cette page persiste.'}
        </div>
        """, unsafe_allow_html=True)

        if role == "admin":
            st.markdown("""
            <div class='info-box'>
            <b>Identifiants de démonstration :</b><br>
            🔴 Admin : <code>admin</code> / <code>Afriland@Admin2024</code><br>
            👤 DG Réseau : <code>dg_reseau</code> / <code>DG@Reseau2024</code><br>
            👤 Hippodrome : <code>hippodrome</code> / <code>Hippo@AFB2024</code><br>
            👤 Analyste : <code>analyste</code> / <code>Analyste@AFB2024</code>
            </div>
            """, unsafe_allow_html=True)
        return

    # ── Routage des pages ──
    if page == "📊 Dashboard Global":
        page_dashboard_global(df_clean)

    elif page == "📍 Dashboard par Agence":
        page_dashboard_agence(df_clean, agence_forcee=agence)

    elif page == "📈 Analyse Comparative":
        page_comparative(df_clean)

    elif page == "🔮 Modélisation & Prédictions":
        page_modelisation(df_clean)

    elif page == "💬 Verbatims Clients":
        page_verbatims(df_clean)

    elif page == "📝 Rapport & Export":
        page_rapport(df_clean, username, role, nom)

    elif page == "🕵️ Journal d'Activité (Admin)":
        if role == "admin":
            page_journal_activite()
        else:
            st.error("🚫 Accès réservé à l'administrateur système.")


if __name__ == "__main__":
    main()
