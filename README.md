# 🏦 Afriland First Bank — Plateforme BI Satisfaction Client

**Version 2.0 | Développé par DeepStats**

## Déploiement Streamlit Cloud

1. **Pusher le code** sur GitHub (repo public ou privé)
1. Se connecter sur [share.streamlit.io](https://share.streamlit.io)
1. Déployer `app.py` avec les settings :
- **Main file path :** `app.py`
- **Python version :** 3.10+

## Identifiants par défaut

|Rôle                    |Identifiant |Mot de passe        |Accès                    |
|------------------------|------------|--------------------|-------------------------|
|🔴 Administrateur        |`admin`     |`Afriland@Admin2024`|Tout + Journal d’activité|
|👤 DG Réseau             |`dg_reseau` |`DG@Reseau2024`     |Toutes agences           |
|👤 Responsable Hippodrome|`hippodrome`|`Hippo@AFB2024`     |Agence Hippodrome        |
|👤 Responsable Bastos    |`bastos`    |`Bastos@AFB2024`    |Agence Bastos            |
|👤 Responsable Bonanjo   |`bonanjo`   |`Bonanjo@AFB2024`   |Agence Bonanjo           |
|👤 Responsable Maroua    |`maroua`    |`Maroua@AFB2024`    |Agence Maroua            |
|👤 Responsable Mendong   |`mendong`   |`Mendong@AFB2024`   |Agence Mendong           |
|👤 Analyste Qualité      |`analyste`  |`Analyste@AFB2024`  |Toutes agences (lecture) |


> ⚠️ **Sécurité :** En production, migrez les credentials vers une BDD sécurisée ou les Streamlit Secrets.

## Fonctionnalités

### Pages disponibles

- **📊 Dashboard Global National** — KPIs, NPS, satisfaction, top/flop agences
- **📍 Dashboard par Agence** — Diagnostic individuel avec radar comparatif
- **📈 Analyse Comparative** — Heatmap, matrice scatter, classement inter-agences
- **🔮 Modélisation & Prédictions S+1** — RandomForest, simulateur d’impact
- **💬 Verbatims Clients** — Voix du client, thèmes récurrents automatiques
- **📝 Rapport & Export** — Synthèse narrative + exports CSV
- **🕵️ Journal d’Activité** *(Admin uniquement)* — Surveillance des connexions/actions

### Format fichier attendu

- Extension : `.xlsx` ou `.csv`
- Colonnes exactes du questionnaire KoBoToolbox AFB standard
- Exemple fourni : `Exemple_donnée.xlsx`

## Architecture technique

```
app.py              # Application principale (1950+ lignes)
requirements.txt    # Dépendances Python
README.md           # Ce fichier
activity_log.db     # SQLite auto-généré (journal d'activité)
```