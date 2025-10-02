# 📦 Importação de bibliotecas
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# ⚙️ Configuração da página
st.set_page_config(layout='wide')

# 🔧 Função auxiliar para formatar números
def formata_numero(valor, prefixo=''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

# 🛒 Título do dashboard
st.title('DASHBOARD DE VENDAS 🛒')

# 🌐 Fonte de dados
url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

# 🎛️ Filtros na barra lateral
st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)
regiao_param = '' if regiao == 'Brasil' else regiao.lower()

todos_anos = st.sidebar.checkbox('Dados de todo o período', value=True)
ano_param = '' if todos_anos else st.sidebar.slider('Ano', 2020, 2023)

# 🔍 Requisição à API com tratamento de erro
query_string = {'regiao': regiao_param, 'ano': ano_param}
response = requests.get(url, params=query_string)

if response.status_code == 200:
    try:
        dados = pd.DataFrame.from_dict(response.json())
    except Exception as e:
        st.error("Erro ao decodificar JSON da resposta.")
        st.write("Conteúdo bruto:", response.text[:500])
        st.stop()
else:
    st.error(f"Erro na requisição: {response.status_code}")
    st.stop()

# 📅 Conversão da coluna de data
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

# 🧑‍💼 Filtro de vendedores
filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

# 📊 Tabelas de receita
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(
    receita_estados, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False)

receita_mensal = dados.groupby(pd.Grouper(key='Data da Compra', freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

# 📦 Tabelas de quantidade de vendas
vendas_estados = pd.DataFrame(dados.groupby('Local da compra')['Preço'].count())
vendas_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(
    vendas_estados, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False)

vendas_mensal = dados.groupby(pd.Grouper(key='Data da Compra', freq='M'))['Preço'].count().reset_index()
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mes'] = vendas_mensal['Data da Compra'].dt.month_name()

vendas_categorias = dados.groupby('Categoria do Produto')['Preço'].count().sort_values(ascending=False)

# 🧑‍💼 Tabela de vendedores
vendedores = dados.groupby('Vendedor')['Preço'].agg(['sum', 'count'])

# 📈 Gráficos de receita
fig_mapa_receita = px.scatter_geo(receita_estados, lat='lat', lon='lon', scope='south america',
                                  size='Preço', template='seaborn', hover_name='Local da compra',
                                  hover_data={'lat': False, 'lon': False}, title='Receita por estado')

fig_receita_mensal = px.line(receita_mensal, x='Mes', y='Preço', markers=True,
                             range_y=(0, receita_mensal['Preço'].max()), color='Ano',
                             line_dash='Ano', title='Receita mensal')
fig_receita_mensal.update_layout(yaxis_title='Receita')

fig_receita_estados = px.bar(receita_estados.head(), x='Local da compra', y='Preço',
                              text_auto=True, title='Top estados (receita)')
fig_receita_estados.update_layout(yaxis_title='Receita')

fig_receita_categorias = px.bar(receita_categorias, text_auto=True, title='Receita por categoria')
fig_receita_categorias.update_layout(yaxis_title='Receita')

# 📈 Gráficos de vendas
fig_mapa_vendas = px.scatter_geo(vendas_estados, lat='lat', lon='lon', scope='south america',
                                 template='seaborn', size='Preço', hover_name='Local da compra',
                                 hover_data={'lat': False, 'lon': False}, title='Vendas por estado')

fig_vendas_estados = px.bar(vendas_estados.head(), x='Local da compra', y='Preço',
                             text_auto=True, title='Top 5 estados')
fig_vendas_estados.update_layout(yaxis_title='Quantidade de vendas')

fig_vendas_mensal = px.line(vendas_mensal, x='Mes', y='Preço', markers=True,
                            range_y=(0, vendas_mensal['Preço'].max()), color='Ano',
                            line_dash='Ano', title='Quantidade de vendas mensal')
fig_vendas_mensal.update_layout(yaxis_title='Quantidade de vendas')

fig_vendas_categorias = px.bar(vendas_categorias, text_auto=True, title='Vendas por categoria')
fig_vendas_categorias.update_layout(showlegend=False, yaxis_title='Quantidade de vendas')

# 🖥️ Visualização no Streamlit
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])

with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)

with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_vendas, use_container_width=True)
        st.plotly_chart(fig_vendas_estados, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_vendas_mensal, use_container_width=True)
        st.plotly_chart(fig_vendas_categorias, use_container_width=True)

with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
                                        x='sum', y=vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
                                        text_auto=True, title=f'Top {qtd_vendedores} vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
                                       x='count', y=vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
                                       text_auto=True, title=f'Top {qtd_vendedores} vendedores (quantidade de vendas)')
        st.plotly_chart(fig_vendas_vendedores, use_container_width=True)
