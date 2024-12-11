from datetime import datetime
import numpy as np
import streamlit as st
import pandas as pd
import plotly.express as px
from query import *
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import smtplib
import email.message

# Inicialização do Streamlit
st.set_page_config(page_title="SP Respira", layout="wide")

# Consulta no banco de dados
query = "SELECT * FROM tb_registro"

# Carregar os dados do MySQL
df = conexao(query)

# Botão para atualização dos dados
if st.button("Atualizar dados"):
    df = conexao(query)

# Adicionando CSS customizado para aplicar o fundo branco
st.markdown(
    """
    <style>
        /* Fundo da página */
        .main {
            background-color: #FFFFFF;  /* Branco */
        }

        /* Título principal */
        h1 {
            color: #006400;  /* Verde escuro */
        }

        /* Títulos dos gráficos */
        .chart-container .plotly .modebar {
            background-color: #006400; /* Verde escuro nos controles de gráficos */
        }
    </style>
    """,
    unsafe_allow_html=True
)


def obter_dados_mais_recentes():
    query = """
    SELECT temperatura, umidade, co2, poeira
    FROM tb_registro
    ORDER BY tempo_registro DESC
    LIMIT 1
    """
    # Execute a consulta no banco de dados para obter os valores mais recentes
    dados = conexao(query)
    
    if dados.empty:
        return None  # Se não houver dados, retorna None
    
    # Retorne os valores mais recentes como uma tupla
    return dados.iloc[0]  # Pega o primeiro registro que é o mais recente

# Função para exibir informações principais na tela
def Home():
    # Informações principais
    if not df.empty:
        media_umidade = df['umidade'].mean()
        media_temperatura = df['temperatura'].mean()
        media_co2 = df['co2'].mean()
        media_poeira = df['poeira'].mean()  # Calcula a média de poeira

        # Ajustando para 4 colunas
        media1, media2, media3, media4 = st.columns(4, gap='large')
        with media1:
            st.metric(label='Média de Umidade', value=f'{media_umidade:.1f}')
        with media2:
            st.metric(label='Média de Temperatura', value=f'{media_temperatura:.1f}')
        with media3:
            st.metric(label='Média de CO2', value=f'{media_co2:.1f}')
        with media4:
            st.metric(label='Média de Poeira', value=f'{media_poeira:.1f}')

            

    # Exibe uma tabela com os dados filtrados
    with st.expander("Visualizar Em Tabela"):
        mostrarDados = st.multiselect("Filtros:", df.columns, default=[], key="showData_home")
        if mostrarDados:
            st.write(df[mostrarDados])
    
def graficos():
    # Título principal da aplicação
    st.markdown(
        """
        <h1 style='text-align: center; font-size: 600%; margin-bottom: 65px;'>
            SP Respira® Monitoramento
        </h1>
        """,
        unsafe_allow_html=True
    )

# Verificando se dados existem para exibir
    if df.empty:
        st.write('Nenhum dado está disponível para gerar os gráficos.')
    else:
        # Criando as colunas para os cartões e data/hora centralizados horizontalmente
        temperatura_atual = df['temperatura'].iloc[-1] if 'temperatura' in df.columns else 'N/A'
        umidade_atual = df['umidade'].iloc[-1] if 'umidade' in df.columns else 'N/A'
        poeira_atual = df['poeira'].iloc[-1] if 'poeira' in df.columns else 'N/A'
        
        # Capturando a data/hora atual no formato correto
        data_hora_atual = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        # Criando colunas para os 3 cartões e a data/hora
        col1, col2, col3, col4 = st.columns([2, 2, 2, 3], gap='large')
        
        # Adicionando os cartões com as métricas
        with col1:
            st.metric(label="Temperatura Atual", value=f"{temperatura_atual:.1f} °C" if isinstance(temperatura_atual, (int, float)) else temperatura_atual)
        with col2:
            st.metric(label="Umidade Atual", value=f"{umidade_atual:.1f} %" if isinstance(umidade_atual, (int, float)) else umidade_atual)
        with col3:
            st.metric(label="Poeira Atual", value=f"{poeira_atual:.1f} µg/m³" if isinstance(poeira_atual, (int, float)) else poeira_atual)
        
        # Exibindo a data/hora atual ao lado dos cartões
        with col4:
            st.write(
                f"<p style='font-size: 18px; text-align: left;'>Última atualização: {data_hora_atual}</p>",
                unsafe_allow_html=True
            )

    # Verificando se dados existem para exibir
    if df.empty:
        st.write('Nenhum dado está disponível para gerar os gráficos.')
    else:
        # Criando as colunas para disposição dos gráficos
        col1, col2 = st.columns(2)

            ############### GRÁFICO 1 ---- TEMPERATURA ####################
        # Gráfico de Temperatura
        with col1:
            try:
                # Convertendo tempo para datetime
                df['tempo_registro'] = pd.to_datetime(df['tempo_registro'])

                # Criando o gráfico com linha vermelha
                fig_linha = px.line(
                    df,
                    x='tempo_registro',
                    y='temperatura',
                    title="Variação de Temperatura"
                )

                # Configurando a cor da linha
                fig_linha.update_traces(line=dict(color='red'))

                # Centralizando o título do gráfico
                fig_linha.update_layout(
                    title_x=0.4  # Centraliza horizontalmente
                )

                # Exibindo o gráfico no Streamlit
                st.plotly_chart(fig_linha, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao criar gráfico de linha: {e}")

        ############ GRÁFICO 3 --- TEMPERATURA E UMIDADE ##################
        with col1:
            try:
                # Criando uma nova coluna para identificar as condições de umidade
                df['condicao_umidade'] = df['umidade'].apply(
                    lambda x: 'Ar Seco' if x <= 45 else ('Ar Úmido' if x >= 65 else 'Ideal')
                )
                
                # Mapeando cores para as condições de umidade
                cor_mapeamento = {
                    'Ar Seco': '#FFFF00',  # Amarelo
                    'Ar Úmido': '#FF0000',  # Vermelho
                    'Ideal': '#0000FF'  # Azul
                }

                # Criando o gráfico de dispersão
                fig_disp = px.scatter(
                    df,
                    x="temperatura",
                    y="umidade",
                    color="condicao_umidade",
                    title="Temperatura e Umidade",
                    color_discrete_map=cor_mapeamento,
                    template="plotly_white",
                    labels={"condicao_umidade": "Descrição"}  # Renomeando a legenda
                )
                
                # Ajustando a posição da legenda no layout
                fig_disp.update_layout(
                    legend=dict(
                        title="Descrição",  # Definindo o título da legenda
                        title_font=dict(size=12),  # Tamanho do título
                        orientation="v",  # Orientação vertical
                        y=0.5,  # Alinhado ao centro vertical
                        x=1.02,  # Posicionado na lateral direita
                        xanchor="left",  # Alinhamento à esquerda da posição
                        yanchor="middle"  # Alinhamento ao centro da posição
                    )
                )
                fig_disp.update_layout(title_x=0.3)
                # Exibindo o gráfico no Streamlit
                st.plotly_chart(fig_disp, use_container_width=True)
                
            except Exception as e:
                st.error(f"Erro ao criar gráfico de dispersão: {e}")


        ############### GRÁFICO 2 --- UMIDADE#####################

        with col2:
            try:
                # Criando o gráfico de linha com os dados brutos de umidade
                fig_umidade = px.line(
                    df,
                    x='tempo_registro',
                    y='umidade',
                    title="Variação da Umidade"
                )

                # Configurando a cor da linha e centralizando o título
                fig_umidade.update_traces(line=dict(color='blue'))
                fig_umidade.update_layout(title_x=0.5)

                # Exibindo o gráfico no Streamlit
                st.plotly_chart(fig_umidade, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao criar gráfico de umidade: {e}")


        ################### GRÁFICO 4 -- DISPERSÃO 3D ###################
        with col2:
            try:
                # Criando o gráfico 3D com coloração baseada na poeira
                fig_3d = px.scatter_3d(
                    df,
                    x='temperatura',
                    y='umidade',
                    z='poeira',
                    color='poeira',  # A cor será definida com base nos valores de poeira
                    color_continuous_scale='Viridis',  # Escala de cores (pode ser alterada para 'Plasma', 'Cividis', etc.)
                    title="Temperatura, Umidade e Poeira",
                    labels={"poeira": "Concentração de Poeira (µg/m³)"}
                )
                
                # Ajustando o layout para uma visualização mais clara
                # Centraliza o título horizontalmente
                fig_3d.update_layout(
                    title_x=0.3,
                    scene=dict(
                        xaxis_title="Temperatura (°C)",
                        yaxis_title="Umidade (%)",
                        zaxis_title="Poeira (µg/m³)"
                    )
                )
                

                # Exibindo o gráfico no Streamlit
                st.plotly_chart(fig_3d, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao criar gráfico 3D: {e}")

def exportar_dados(df):
    """
    Função para criar dois botões:
    1. Exportar dados da consulta SQL para CSV.
    2. Exportar dados estatísticos da consulta SQL para CSV.
    """
    if not df.empty:
        col1, col2 = st.columns(2)  # Criando duas colunas para os botões
        with col1:
            st.download_button(
                label="Exportar Dados para CSV",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name='dados_consulta_sql.csv',
                mime='text/csv'
            )
        with col2:
            descricao_estatisticas = df.describe().transpose()
            st.download_button(
                label="Exportar Dados Estatísticos para CSV",
                data=descricao_estatisticas.to_csv().encode('utf-8'),
                file_name='dados_estatisticos.csv',
                mime='text/csv'
            )

########################################################## INÍCIO GMAIL ###############################################################

# Lógica para envio de emails com alerta personalizado
def enviar_email(assunto, destinatario, corpo_email, remetente, senha):
    try:
        # Configuração da mensagem de e-mail
        msg = email.message.Message()
        msg['Subject'] = assunto
        msg['From'] = remetente
        msg['To'] = destinatario
        msg.add_header('Content-Type', 'text/html')
        msg.set_payload(corpo_email)

        # Conexão com o servidor SMTP
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls()
            s.login(remetente, senha)
            s.sendmail(remetente, destinatario, msg.as_string().encode('utf-8'))
        #st.success(f'E-mail enviado para {destinatario} com o assunto: "{assunto}"')

    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")
        print(f"Detalhes do erro: {e}")


def verificar_condicoes_e_enviar_email(temperatura, umidade, co2, poeira, remetente, senha):
    limite_temperatura = 27
    limite_umidade = 45
    limite_co2 = 1000
    limite_poeira = 7000

    # Condições e envio de alerta por email
    if temperatura > limite_temperatura:
        assunto = "Alerta: Temperatura Alta"
        corpo_email = f"""
        <p>A temperatura está acima do limite!</p>
        <p><b>Temperatura Atual:</b> {temperatura}°C</p>
        <p>Por favor, tome as medidas necessárias.</p>
        """
        enviar_email(assunto, 'aline.fernandes.02032002@gmail.com', corpo_email, remetente, senha)

    if umidade < limite_umidade:
        assunto = "Alerta: Umidade Baixa"
        corpo_email = f"""
        <p>A umidade está abaixo do limite!</p>
        <p><b>Umidade Atual:</b> {umidade}%</p>
        <p>Por favor, tome as medidas necessárias.</p>
        """
        enviar_email(assunto, 'aline.fernandes.02032002@gmail.com', corpo_email, remetente, senha)

    if co2 > limite_co2:
        assunto = "Alerta: Nível de CO2 Alto"
        corpo_email = f"""
        <p>O nível de CO2 está acima do limite!</p>
        <p><b>CO2 Atual:</b> {co2} ppm</p>
        <p>Por favor, tome as medidas necessárias.</p>
        """
        enviar_email(assunto, 'aline.fernandes.02032002@gmail.com', corpo_email, remetente, senha)

    if poeira > limite_poeira:
        assunto = "Alerta: Concentração de Poeira Alta"
        corpo_email = f"""
        <p>A concentração de poeira está acima do limite!</p>
        <p><b>Poeira Atual:</b> {poeira} µg/m³</p>
        <p>Por favor, tome as medidas necessárias.</p>
        """
        enviar_email(assunto, 'aline.fernandes.02032002@gmail.com', corpo_email, remetente, senha)

    
if __name__ == "__main__":
    # Obter os dados mais recentes do banco de dados
    dados_mais_recentes = obter_dados_mais_recentes()

    if dados_mais_recentes is not None:
        temperatura_atual = dados_mais_recentes['temperatura']
        umidade_atual = dados_mais_recentes['umidade']
        co2_atual = dados_mais_recentes['co2']
        poeira_atual = dados_mais_recentes['poeira']
    else:
        # Caso não haja dados no banco de dados, defina valores padrão ou gere um erro
        temperatura_atual = 0
        umidade_atual = 0
        co2_atual = 0
        poeira_atual = 0


    # Credenciais do remetente
    email_remetente = "sprespiraoficial@gmail.com"
    senha_remetente = "ysxv ulgy vfjq tvei"

    # Verificar condições e enviar alertas
    verificar_condicoes_e_enviar_email(
        temperatura_atual, 
        umidade_atual, 
        co2_atual, 
        poeira_atual, 
        email_remetente, 
        senha_remetente
    )
    
################################################### FIM GMAIL ########################################################################

def mainPy():

    dados = conexao("SELECT * FROM tb_registro")
    graficos()
    Home()
    exportar_dados(dados)

if __name__ == '__main__':
    mainPy()