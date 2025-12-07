import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ================================
# CONFIG DASHBOARD
# ================================
st.set_page_config(page_title="Retail Dashboard", layout="wide")

# ====== THEME / STYLE PERSO ======
CUSTOM_CSS = """
<style>
/* Fond général */
.stApp {
    background-color: #0f172a; /* bleu nuit */
    color: #e5e7eb;           /* texte gris clair */
}

/* Titre principal */
h1 {
    color: #fbbf24;           /* jaune-or */
    font-weight: 800;
}

/* Sous-titres */
h2, h3 {
    color: #e5e7eb;
    font-weight: 700;
}

/* Ajustement container */
.block-container {
    padding-top: 1rem;
}

/* Cartes KPI (peut varier selon version Streamlit) */
.stMetric {
    background: #111827;
    padding: 10px;
    border-radius: 12px;
    border: 1px solid #1f2937;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.title("📊 Retail Analytics Dashboard")
st.caption("Dataset : retail.csv")

# ================================
# CHARGEMENT DU DATASET
# ================================
@st.cache_data
def load_data():
    df = pd.read_csv(
        r"C:\Users\matim\OneDrive\Bureau\DataAnalytics_Portfolio\Customer_Churn_Prediction\data\retail.csv"
    )

    # Nettoyage des noms de colonnes
    df.columns = [c.strip() for c in df.columns]

    # Conversion de la date
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Création de Total Amount si manquante
    if "Total Amount" not in df.columns:
        df["Total Amount"] = df["Quantity"] * df["Price per Unit"]

    # Colonnes dérivées
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    df["Day"] = df["Date"].dt.day_name()

    return df

df = load_data()

# ================================
# FILTRES SIDEBAR
# ================================
st.sidebar.header("🧰 Filtres")

# Filtre date
min_date = df["Date"].min()
max_date = df["Date"].max()

date_range = st.sidebar.date_input(
    "Période",
    value=(min_date, max_date)
)

df_filtered = df.copy()

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_filtered = df_filtered[(df_filtered["Date"] >= start) & (df_filtered["Date"] <= end)]

# Filtre catégorie
categories = ["Toutes"] + sorted(df["Product Category"].dropna().unique().tolist())
cat_choice = st.sidebar.multiselect("Catégories de produits", categories, default=["Toutes"])

if "Toutes" not in cat_choice:
    df_filtered = df_filtered[df_filtered["Product Category"].isin(cat_choice)]

# Filtre genre
genders = ["Tous"] + sorted(df["Gender"].dropna().unique().tolist())
gender_choice = st.sidebar.multiselect("Genre", genders, default=["Tous"])

if "Tous" not in gender_choice:
    df_filtered = df_filtered[df_filtered["Gender"].isin(gender_choice)]

# ================================
# KPIs
# ================================
st.subheader("📌 Indicateurs principaux")

col1, col2, col3, col4 = st.columns(4)

if df_filtered.empty:
    total_revenue = 0
    nb_transactions = 0
    avg_basket = 0
    nb_clients = 0
else:
    total_revenue = int(df_filtered["Total Amount"].sum())
    nb_transactions = df_filtered.shape[0]
    avg_basket = df_filtered["Total Amount"].mean()
    nb_clients = df_filtered["Customer ID"].nunique()

col1.metric("💶 Chiffre d'affaires", f"{total_revenue} €")
col2.metric("🧾 Transactions", f"{nb_transactions}")
col3.metric("🧺 Panier moyen", f"{avg_basket:.2f} €")
col4.metric("👤 Clients uniques", f"{nb_clients}")

st.markdown("---")

# ================================
# TABS
# ================================
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Vue globale", "🔥 Heatmaps", "📈 Tendances", "🧑‍🤝‍🧑 Genre"]
)

# ================================
# TAB 1 : VUE GLOBALE (TOP CATÉGORIES)
# ================================
with tab1:
    st.header("1️⃣ Top catégories de produits")

    if df_filtered.empty:
        st.info("Aucune donnée à afficher avec les filtres actuels.")
    else:
        col_top1, col_top2 = st.columns(2)

        with col_top1:
            st.subheader("Par nombre d'achats")
            top_counts = df_filtered["Product Category"].value_counts().reset_index()
            top_counts.columns = ["Product Category", "Count"]

            fig1, ax1 = plt.subplots(figsize=(5, 3))
            sns.barplot(data=top_counts, x="Product Category", y="Count", ax=ax1)
            ax1.set_xlabel("Catégorie")
            ax1.set_ylabel("Nombre d'achats")
            plt.xticks(rotation=30)
            st.pyplot(fig1)

        with col_top2:
            st.subheader("Par chiffre d'affaires")
            top_revenue = (
                df_filtered.groupby("Product Category")["Total Amount"]
                .sum()
                .reset_index()
                .sort_values("Total Amount", ascending=False)
            )

            fig2, ax2 = plt.subplots(figsize=(5, 3))
            sns.barplot(data=top_revenue, x="Product Category", y="Total Amount", ax=ax2)
            ax2.set_xlabel("Catégorie")
            ax2.set_ylabel("CA (€)")
            plt.xticks(rotation=30)
            st.pyplot(fig2)

# ================================
# TAB 2 : HEATMAPS
# ================================
with tab2:
    st.header("2️⃣ Heatmaps (pics d'achats)")

    hcol1, hcol2 = st.columns(2)

    # Heatmap Jour × Catégorie
    with hcol1:
        st.subheader("🔥 Jour de la semaine × Catégorie")

        if df_filtered.empty:
            st.warning("Aucune donnée disponible pour les filtres choisis.")
        else:
            pivot_day = df_filtered.pivot_table(
                index="Day",
                columns="Product Category",
                values="Transaction ID",
                aggfunc="count",
                fill_value=0
            )

            # Réordonner les jours
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            pivot_day = pivot_day.reindex(day_order)

            if pivot_day.size == 0:
                st.info("Impossible d'afficher la heatmap (table vide).")
            else:
                fig3, ax3 = plt.subplots(figsize=(6, 4))
                sns.heatmap(pivot_day.T, cmap="Blues", annot=True, fmt="d", ax=ax3)
                ax3.set_xlabel("Jour de la semaine")
                ax3.set_ylabel("Catégorie")
                st.pyplot(fig3)

    # Heatmap Mois × Catégorie
    with hcol2:
        st.subheader("🔥 Mois × Catégorie")

        if df_filtered.empty:
            st.warning("Aucune donnée disponible pour les filtres choisis.")
        else:
            pivot_month = df_filtered.pivot_table(
                index="Month",
                columns="Product Category",
                values="Transaction ID",
                aggfunc="count",
                fill_value=0
            ).sort_index()

            if pivot_month.size == 0:
                st.info("Impossible d'afficher la heatmap (table vide).")
            else:
                fig4, ax4 = plt.subplots(figsize=(6, 4))
                sns.heatmap(pivot_month.T, cmap="Greens", annot=True, fmt="d", ax=ax4)
                ax4.set_xlabel("Mois")
                ax4.set_ylabel("Catégorie")
                st.pyplot(fig4)

# ================================
# TAB 3 : TENDANCES
# ================================
with tab3:
    st.header("3️⃣ Tendances des ventes")

    tcol1, tcol2 = st.columns(2)

    with tcol1:
        st.subheader("📈 Tendance journalière (CA)")
        if df_filtered.empty:
            st.info("Aucune donnée pour afficher la tendance journalière.")
        else:
            daily = (
                df_filtered.groupby("Date")["Total Amount"]
                .sum()
                .reset_index()
                .sort_values("Date")
            )
            fig5, ax5 = plt.subplots(figsize=(7, 3))
            ax5.plot(daily["Date"], daily["Total Amount"], marker="o")
            ax5.set_xlabel("Date")
            ax5.set_ylabel("CA (€)")
            ax5.set_title("Chiffre d'affaires journalier")
            plt.xticks(rotation=30)
            st.pyplot(fig5)

    with tcol2:
        st.subheader("📈 Tendance mensuelle (CA)")
        if df_filtered.empty:
            st.info("Aucune donnée pour afficher la tendance mensuelle.")
        else:
            monthly = (
                df_filtered.groupby("Month")["Total Amount"]
                .sum()
                .reset_index()
                .sort_values("Month")
            )
            fig6, ax6 = plt.subplots(figsize=(7, 3))
            ax6.bar(monthly["Month"], monthly["Total Amount"])
            ax6.set_xlabel("Mois")
            ax6.set_ylabel("CA (€)")
            ax6.set_title("Chiffre d'affaires mensuel")
            plt.xticks(rotation=45)
            st.pyplot(fig6)

# ================================
# TAB 4 : ANALYSE PAR GENRE
# ================================
with tab4:
    st.header("4️⃣ Analyse par genre")

    gcol1, gcol2 = st.columns(2)

    with gcol1:
        st.subheader("Répartition des clients par genre")
        if df_filtered.empty:
            st.info("Aucune donnée pour afficher la répartition par genre.")
        else:
            gender_counts = df_filtered["Gender"].value_counts()
            fig7, ax7 = plt.subplots(figsize=(4, 4))
            ax7.pie(gender_counts.values, labels=gender_counts.index, autopct="%1.1f%%")
            ax7.set_title("Genre des clients")
            st.pyplot(fig7)

    with gcol2:
        st.subheader("CA par genre et catégorie")
        if df_filtered.empty:
            st.info("Aucune donnée pour cette vue.")
        else:
            pivot_gender = df_filtered.pivot_table(
                index="Gender",
                columns="Product Category",
                values="Total Amount",
                aggfunc="sum",
                fill_value=0
            )
            st.dataframe(pivot_gender.style.format("{:,.0f}"))

st.markdown("---")

st.caption("✅ Dashboard construit avec Streamlit, Matplotlib et Seaborn.")
