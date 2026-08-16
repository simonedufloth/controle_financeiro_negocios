import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Controle Financeiro de Empreendimentos", page_icon="💎", layout="wide")

# Estilo visual do cabeçalho idêntico ao layout
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
EXCEL_FILE = "controle_financeiro.xlsx"

# Abas de navegação superiores
nav_option = st.radio("", ["Novo Lançamento", "Consultar e Resumos"], horizontal=True, label_visibility="collapsed")

# Dicionário estrito de Categorias Dinâmicas vinculadas aos Tipos de Movimentação
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
        
        # Tipo de Movimentação (sem form para reagir e atualizar instantaneamente as categorias)
        tipo = st.selectbox("Tipo de Movimentação", ["Receita", "Despesa", "Investimento"], key="tipo_mov")
        
    with col2:
        # Data com formato explícito DD/MM/YYYY
        data = st.date_input("Data do Lançamento", value=datetime.today(), format="DD/MM/YYYY")
        
        # Categoria Específica atualizada dinamicamente com base no Tipo escolhido acima
        categorias_disponiveis = categorias_dict.get(tipo, ["Outras"])
        categoria = st.selectbox("Categoria Específica (Dinâmica)", categorias_disponiveis)
        
    descricao = st.text_input("📝 Descrição / Fornecedor / Observação", placeholder="Ex: Aquisição de equipamentos para o projeto...")
    valor = st.number_input("💰 Valor (R$)", min_value=0.00, format="%.2f")
    
    if st.button("💾 Salvar Lançamento no Sistema", use_container_width=True):
        # Converte a data para o padrão de texto dd/mm/yyyy para gravação
        data_formatada = data.strftime("%d/%m/%Y")
        
        nova_linha = pd.DataFrame({
            "Data": [data_formatada],
            "Projeto": [projeto],
            "Tipo": [tipo],
            "Categoria": [categoria],
            "Valor": [valor],
            "Descrição": [descricao]
        })
        
        try:
            # Salva na aba específica do projeto correspondente na planilha Excel
            if os.path.exists(EXCEL_FILE):
                with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                    try:
                        df_existing = pd.read_excel(EXCEL_FILE, sheet_name=projeto)
                        df_updated = pd.concat([df_existing, nova_linha], ignore_index=True)
                        df_updated.to_excel(writer, sheet_name=projeto, index=False)
                    except ValueError:
                        nova_linha.to_excel(writer, sheet_name=projeto, index=False)
            else:
                with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
                    nova_linha.to_excel(writer, sheet_name=projeto, index=False)
            
            st.success("✅ Lançamento salvo com sucesso e vinculado à planilha do projeto!")
        except Exception as e:
            if "transactions" not in st.session_state:
                st.session_state["transactions"] = pd.DataFrame(columns=["Data", "Projeto", "Tipo", "Categoria", "Valor", "Descrição"])
            st.session_state["transactions"] = pd.concat([st.session_state["transactions"], nova_linha], ignore_index=True)
            st.success("✅ Lançamento salvo com sucesso no sistema!")

elif nav_option == "Consultar e Resumos":
    st.subheader("📊 Painel de Consultas e Resumos")
    
    filtro_projeto = st.selectbox("Filtrar visualização por Projeto", ["Todos os Projetos"] + projects)
    
    try:
        df_filtered = pd.DataFrame()
        if os.path.exists(EXCEL_FILE):
            if filtro_projeto == "Todos os Projetos":
                dfs = []
                for p in projects:
                    try:
                        df_p = pd.read_excel(EXCEL_FILE, sheet_name=p)
                        dfs.append(df_p)
                    except Exception:
                        pass
                if dfs:
                    df_filtered = pd.concat(dfs, ignore_index=True)
            else:
                try:
                    df_filtered = pd.read_excel(EXCEL_FILE, sheet_name=filtro_projeto)
                except Exception:
                    st.info(f"Ainda não há dados salvos para o {filtro_projeto}.")
        else:
            if "transactions" in st.session_state:
                df_filtered = st.session_state["transactions"]
                if filtro_projeto != "Todos os Projetos":
                    df_filtered = df_filtered[df_filtered["Projeto"] == filtro_projeto]
        
        if df_filtered.empty:
            st.info("Nenhum lançamento cadastrado até o momento.")
        else:
            if "Data" in df_filtered.columns:
                df_filtered["Data"] = df_filtered["Data"].astype(str)
            
            st.dataframe(df_filtered, use_container_width=True)
            
            receitas = df_filtered[df_filtered["Tipo"] == "Receita"]["Valor"].sum()
            despesas = df_filtered[df_filtered["Tipo"] == "Despesa"]["Valor"].sum()
            investimentos = df_filtered[df_filtered["Tipo"] == "Investimento"]["Valor"].sum()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Receitas", f"R$ {receitas:,.2f}")
            col2.metric("Total Despesas", f"R$ {despesas:,.2f}")
            col3.metric("Total Investimentos", f"R$ {investimentos:,.2f}")
            
    except Exception as e:
        st.info("Aguardando o primeiro lançamento para gerar os resumos.")