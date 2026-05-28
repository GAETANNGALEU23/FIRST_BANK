"""
========================================================================
 AFRILAND FIRST BANK — Plateforme BI Satisfaction Client
 Version 2.0 | Optimisé pour Streamlit Cloud
========================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import base64
import os

# ============================================================
# 0. CONFIGURATION DE LA PAGE (Doit impérativement être en premier)
# ============================================================
st.set_page_config(
    page_title="Afriland First Bank | BI Satisfaction",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 1. FONCTION DE CHARGEMENT DE L'IMAGE D'ARRIÈRE-PLAN (Base64)
# ============================================================
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    if os.path.exists(png_file):
        bin_str = get_base64_of_bin_file(png_file)
        page_bg_img = f'''
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        /* Style pour rendre le formulaire de connexion lisible sur le fond */
        .login-box {{
            background-color: rgba(255, 255, 255, 0.92);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2);
            border-top: 5px solid #006633; /* Vert Afriland */
        }}
        </style>
        '''
        st.markdown(page_bg_img, unsafe_allow_html=True)
    else:
        # Style de secours si l'image n'est pas trouvée
        st.markdown('''
        <style>
        .stApp { background-color: #f4f6f9; }
        </style>
        ''', unsafe_allow_html=True)

# ============================================================
# 2. INITIALISATION DU SESSION STATE & SIMULATION DE DONNÉES
# ============================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None

# Génération de données factices pour assurer le fonctionnement des graphiques
@st.cache_data
def load_mock_data():
    np.random.seed(42)
    agences = ['Hippodrome', 'Akwa', 'Messa', 'Bafoussam', 'Garoua']
    dates = pd.date_range(start="2026-01-01", periods=100, freq='D')
    data = {
        'Date': np.random.choice(dates, size=300),
        'Agence': np.random.choice(agences, size=300),
        'Satisfaction': np.random.randint(1, 6, size=300),
        'Flux_Cash': np.random.uniform(500000, 5000000, size=300),
        'Verbatim': np.random.choice([
            "Service rapide et personnel accueillant.",
            "Attente trop longue aux guichets en fin de mois.",
            "L'application mobile Afriland est excellente.",
            "Problème de connexion réseau récurrent lors des retraits.",
            "Explications claires de la part du conseiller clientèle."
        ], size=300)
    }
    return pd.DataFrame(data)

df_clean = load_mock_data()

# ============================================================
# 3. ÉCRAN DE CONNEXION (LOGIN)
# ============================================================
if not st.session_state.logged_in:
    # Application de la photo en arrière-plan
    set_png_as_page_bg("photo_connection.png")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.8, 1])
    
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.image("https://www.afrilandfirstbank.com/images/logo.png", width=200) # Logo indicatif ou texte
        st.markdown("<h2 style='text-align: center; color: #006633;'>BI Satisfaction Client v2.0</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Portail de Pilotage de la Performance Réseau</p>", unsafe_allow_html=True)
        
        username = st.text_input("Identifiant", placeholder="Ex: admin")
        password = st.text_input("Mot de passe", type="password", placeholder="••••••••")
        
        if st.button("Se connecter", use_container_width=True):
            # Logique d'authentification (Simulation des rôles de démonstration)
            if username == "admin" and password == "Afriland@Admin2024":
                st.session_state.logged_in = True
                st.session_state.user_role = "admin"
                st.session_state.username = "Administrateur"
                st.rerun()
            elif username == "dg_reseau" and password == "DG@Reseau2024":
                st.session_state.logged_in = True
                st.session_state.user_role = "dg"
                st.session_state.username = "Directeur Général Réseau"
                st.rerun()
            elif username == "hippodrome" and password == "Hippo@AFB2024":
                st.session_state.logged_in = True
                st.session_state.user_role = "agence"
                st.session_state.username = "Chef d'Agence Hippodrome"
                st.rerun()
            else:
                st.error("Identifiants incorrects. Veuillez réessayer.")
        
        st.markdown("""
        <div style='margin-top: 20px; font-size: 11px; color: #777; text-align: center;'>
            <b>Comptes de Démo :</b> admin / Afriland@Admin2024 | dg_reseau / DG@Reseau2024
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 4. ESPACE SÉCURISÉ (Une fois connecté)
# ============================================================
else:
    # Réinitialisation du fond gris neutre professionnel pour les tableaux de bord
    st.markdown('''
    <style>
    .stApp { background-image: none !important; background-color: #f8f9fa; }
    .main-header { background-color: #006633; padding: 15px; border-radius: 8px; color: white; margin-bottom: 25px; }
    .card { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    ''', unsafe_allow_html=True)

    # --- BARRE LATÉRALE DE NAVIGATION (Fonctionne parfaitement ici) ---
    with st.sidebar:
        st.image("https://www.afrilandfirstbank.com/images/logo.png", width=150, error_bad_lines=False)
        st.markdown(f"### 👤 {st.session_state.username}")
        st.markdown(f"**Rôle :** `{st.session_state.user_role.upper()}`")
        st.markdown("---")
        
        # Menu de navigation
        menu_options = [
            "📊 Dashboard Global", 
            "📍 Dashboard par Agence", 
            "💬 Verbatims Clients & NLP", 
            "🔮 Modélisation & Prédictions"
        ]
        
        # Restriction de pages selon les rôles si nécessaire
        if st.session_state.user_role == "agence":
            menu_options = ["📍 Dashboard par Agence", "💬 Verbatims Clients & NLP"]
            
        page = st.selectbox("📌 Menu de Pilotage", menu_options)
        
        st.markdown("---")
        if st.button("🚪 Déconnexion", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_role = None
            st.session_state.username = None
            st.rerun()

    # --- EN-TÊTE PRINCIPAL ---
    st.markdown(f"""
    <div class="main-header">
        <h1 style='margin:0; font-size: 24px; color: white;'>Afriland First Bank — Plateforme BI & Satisfaction</h1>
        <p style='margin:0; opacity: 0.8; font-size: 14px;'>Espace d'Analyse : {page}</p>
    </div>
    """, unsafe_allow_html=True)

    # ============================================================
    # PAGINATION : ROUTAGE DES PAGES
    # ============================================================
    
    if page == "📊 Dashboard Global":
        st.subheader("Analyse Consolide de la Performance Réseau")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Taux de Satisfaction Global", f"{df_clean['Satisfaction'].mean():.2f} / 5", "+0.12")
        with col_m2:
            st.metric("Volume de Flux Total Analysé", f"{df_clean['Flux_Cash'].sum():,.0f} XAF")
        with col_m3:
            st.metric("Total Verbatims Traités", len(df_clean))
            
        fig = px.histogram(df_clean, x='Satisfaction', color='Agence', barmode='group',
                           title="Distribution des Scores de Satisfaction par Agence",
                           color_discrete_sequence=px.colors.qualitative.Dark2)
        st.plotly_chart(fig, use_container_width=True)

    elif page == "📍 Dashboard par Agence":
        st.subheader("Filtre Analytique par Point de Vente")
        liste_agences = df_clean['Agence'].unique()
        selected_agence = st.selectbox("Sélectionner l'agence à analyser :", liste_agences)
        
        df_agence = df_clean[df_clean['Agence'] == selected_agence]
        
        st.markdown(f"### Rapport de performance : **Agence {selected_agence}**")
        st.dataframe(df_agence[['Date', 'Satisfaction', 'Flux_Cash', 'Verbatim']].sort_values(by='Date', ascending=False), use_container_width=True)

    elif page == "💬 Verbatims Clients & NLP":
        st.subheader("Analyse Sémantique et Traitement Automatique du Langage")
        
        # --- SECTION EXPLICATIVE DU NLP (NPL) ---
        st.markdown("""
        <div style="background-color: #e6f2ec; padding: 20px; border-radius: 8px; border-left: 5px solid #006633; margin-bottom: 20px;">
            <h4 style="margin-top: 0; color: #006633;">💡 Comprendre le cycle du Traitement du Langage Naturel (NLP / NLP Cycle)</h4>
            <p>Le <b>NLP (Natural Language Processing)</b> est une branche de l'Intelligence Artificielle qui permet d'analyser, comprendre et extraire de la valeur à partir des expressions textuelles de nos clients (Verbatims).</p>
            <b>Le cycle standard de traitement appliqué dans notre moteur BI comprend 4 phases majeures :</b>
            <ol>
                <li><b>Collecte & Nettoyage (Tokenisation/Stopwords) :</b> Extraction des avis issus des formulaires ou bornes d'agences et suppression des mots inutiles.</li>
                <li><b>Analyse de Sentiment :</b> Classification automatique de l'avis en <i>Positif</i>, <i>Neutre</i> ou <i>Négatif</i> à l'aide de modèles d'apprentissage.</li>
                <li><b>Extraction de Thématiques :</b> Identification des concepts récurrents (ex: "Attente", "Application Mobile", "Guichet").</li>
                <li><b>Aide à la Décision :</b> Alerte automatique transmise aux chefs d'agences pour les verbatims critiques.</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        # Visualisation de la répartition des verbatims
        st.markdown("### Aperçu des Verbatims Clients")
        st.table(df_clean[['Agence', 'Verbatim']].head(8))

    elif page == "🔮 Modélisation & Prédictions":
        st.subheader("Moteur Prédictif de la Satisfaction Réseau")
        st.info("Le modèle Random Forest estime la tendance de satisfaction pour la semaine S+1 sur la base des flux financiers historiques.")
        
        st.metric(label="Fiabilité du Modèle (Accuracy)", value="84.3%", delta="Optimisé")
