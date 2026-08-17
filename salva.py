import streamlit as st
import pandas as pd
from datetime import datetime
import json
import tempfile
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Controle Financeiro de Empreendimentos", page_icon="💎", layout="wide")

# Configuração da Conexão com o Google Sheets usando st.secrets
scope = [
    "https://www.googleapis.com/spreadsheets/v3/json",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def conectar_google_sheets():
    # Lê as credenciais seguras do Streamlit Secrets
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # Tratamento avançado e automático da chave privada para eliminar qualquer erro de formato ou "extra data"
    if "private_key" in creds_dict:
        pk = creds_dict["private_key"]
        pk = pk.replace("\\n", "\n").strip()
        
        # Corta qualquer caractere ou espaço indesejado que venha após o fim da chave
        end_marker = "-----END PRIVATE KEY-----"
        if end_marker in pk:
            idx = pk.find(end_marker) + len(end_marker)
            pk = pk[:idx] + "\n"
        creds_dict["private_key"] = pk
        
    # Cria um arquivo JSON temporário seguro para evitar qualquer erro de leitura PEM
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(creds_dict, f)
        temp_path = f.name

    creds = Credentials.from_service_account_file(temp_path, scopes=scope)
    client = gspread.authorize(creds)
    
    # Abre a planilha diretamente pelo ID correto do seu Google Drive
    spreadsheet = client.open_by_key("1xpGfT_dbl3bQY0gpc9ZiLWrl5en7tLLZX2H1XuntYq8")
    return spreadsheet

# Estilo visual do cabeçalho
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #1b4d3e 0%, #3a8a6b 100%);
        padding: 25px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .main-header h1 {
        font-size: 2rem;
        margin-bottom: 5px;
    }
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.9;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="main-header">
        <h1>💎 Controle Financeiro de Empreendimentos</h1>
        <p>Sistema Integrado e Dinâmico para Gestão de Projetos</p>
    </div>
""", unsafe_allow_html=True)

projects = ["Projeto Alfa", "Projeto Beta", "Projeto Delta", "Projeto Gama", "Projeto Omega"]

# Abas de navegação superiores
nav_option = st.radio("", ["Novo Lançamento", "Consultar e Resumos"], horizontal=True, label_visibility="collapsed")

# Dicionário de Categorias Dinâmicas
categorias_dict = {
    "Receita": [
        "Receita de Venda de Produtos",
        "Receita de Venda de Serviços",
        "Receita de Honorários",
        "Receita de Comissão",
        "Outras"
    ],
    "Despesa": [
        "Alimentação",
        "Combustível",
        "Hospedagem",
        "Material de Consumo",
        "Taxas e Impostos",
        "Passagens Aéreas e/ou Terrestres",
        "Aluguéis de Veículos",
        "Aluguéis de Salas ou Espaços para Trabalho",
        "Equipamentos",
        "Remunerações",
        "Outras Despesas"
    ],
    "Investimento": [
        "Empréstimos e Financiamentos",
        "Aporte dos Recursos Próprios do Investor",
        "Dividendos Oriundos de Empreendimentos"
    ]
}

if nav_option == "Novo Lançamento":
    st.subheader("📥 Registrar Nova Movimentação Financeira")
    
    col1, col2 = st.columns(2)
    with col1:
        projeto = st.selectbox("Selecione o Projeto", projects)
        tipo = st.selectbox("Tipo de Movimentação", ["Receita", "Despesa", "Investimento"], key="tipo_mov")
        
    with col2:
        data = st.date_input("Data do Lançamento", value=datetime.today(), format="DD/MM/YYYY")
        categorias_disponiveis = categorias_dict.get(tipo, ["Outras"])
        categoria = st.selectbox("Categoria Específica (Dinâmica)", categorias_disponiveis)
        
    descricao = st.text_input("📝 Descrição / Fornecedor / Observação", placeholder="Ex: Aquisição de equipamentos...")
    valor = st.number_input("💰 Valor (R$)", min_value=0.00, format="%.2f")
    
    if st.button("💾 Salvar Lançamento no Sistema", use_container_width=True):
        data_formatada = data.strftime("%d/%m/%Y")
        
        try:
            # Conecta ao Google Sheets e insere os dados na aba correspondente
            sh = conectar_google_sheets()
            worksheet = sh.worksheet(projeto)
            
            # Adiciona a linha na aba do Google Sheets
            worksheet.append_row([data_formatada, projeto, tipo, categoria, valor, descricao])
            
            st.success("✅ Lançamento salvo com sucesso diretamente na sua planilha do Google Drive!")
        except Exception as e:
            st.error(f"Erro ao salvar na planilha: {e}")

elif nav_option == "Consultar e Resumos":
    st.subheader("📊 Painel de Consultas e Resumos")
    
    filtro_projeto = st.selectbox("Filtrar visualização por Projeto", ["Todos os Projetos"] + projects)
    
    try:
        sh = conectar_google_sheets()
        dfs = []
        
        if filtro_projeto == "Todos os Projetos":
            for p in projects:
                try:
                    ws = sh.worksheet(p)
                    dados = ws.get_all_records()
                    if dados:
                        df_p = pd.DataFrame(dados)
                        dfs.append(df_p)
                except Exception:
                    pass
            if dfs:
                df_filtered = pd.concat(dfs, ignore_index=True)
            else:
                df_filtered = pd.DataFrame()
        else:
            ws = sh.worksheet(filtro_projeto)
            dados = ws.get_all_records()
            df_filtered = pd.DataFrame(dados)
            
        if df_filtered.empty:
            st.info("Nenhum lançamento cadastrado até o momento nesta aba.")
        else:
            if "Data" in df_filtered.columns:
                df_filtered["Data"] = df_filtered["Data"].astype(str)
            
            st.dataframe(df_filtered, use_container_width=True)
            
            receitas = df_filtered[df_filtered["Tipo"] == "Receita"]["Valor"].sum() if "Tipo" in df_filtered.columns else 0
            despesas = df_filtered[df_filtered["Tipo"] == "Despesa"]["Valor"].sum() if "Tipo" in df_filtered.columns else 0
            investimentos = df_filtered[df_filtered["Tipo"] == "Investimento"]["Valor"].sum() if "Tipo" in df_filtered.columns else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Receitas", f"R$ {receitas:,.2f}")
            col2.metric("Total Despesas", f"R$ {despesas:,.2f}")
            col3.metric("Total Investimentos", f"R$ {investimentos:,.2f}")
            
    except Exception as e:
        st.info("Aguardando o primeiro lançamento para gerar os resumos ou verifique a conexão.")