#%%
import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
from pyvis.network import Network
import streamlit.components.v1 as components

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Análise de Rede - Fighting Games", layout="wide")
st.title("Análise da Rede de Fighting Games")
st.write("Aplicação para visualizar e analisar uma rede de conhecimento sobre jogos de luta, extraída da Wikipédia.")

# --- 2. CARREGAMENTO DO GRAFO ---
# Usar cache para otimizar o carregamento
@st.cache_data
def carregar_grafo():
    try:
        return nx.read_graphml("fighting_games_network.graphml")
    except FileNotFoundError:
        st.error("Arquivo 'fighting_games_network.graphml' não encontrado. Certifique-se de que ele está na mesma pasta que o app.py.")
        return None

G = carregar_grafo()
#%%

# --- 3. EXIBIÇÃO DO GRAFO ---
st.sidebar.title("Opções de Visualização")
subgraph_option = st.sidebar.selectbox(
    "Selecione um subconjunto para visualizar:",
    ("Grafo Completo", "Maior Componente Conectado (Fracamente)", "Núcleo Principal (k-core)")
)
# Configuração do k-core
k_core_value = 1
if subgraph_option == "Núcleo Principal (k-core)":
    k_core_value = st.sidebar.slider("Selecione o valor de k para o k-core:", 1, 15, 2)

physics_enabled = st.sidebar.checkbox("Habilitar física interativa", value=True)

#%%

# --- 4. CORPO PRINCIPAL COM ABAS ---
if G is not None:
    # Lógica para filtrar o grafo com base na seleção da barra lateral
    if subgraph_option == "Grafo Completo":
        G_display = G.copy()
        st.sidebar.info(f"Exibindo o grafo completo com **{G_display.number_of_nodes()}** nós e **{G_display.number_of_edges()}** arestas.")
    
    elif subgraph_option == "Maior Componente Conectado (Fracamente)":
        wcc_nodes = max(nx.weakly_connected_components(G), key=len)
        G_display = nx.DiGraph(G.subgraph(wcc_nodes))
        st.sidebar.info(f"Exibindo o maior componente conectado com **{G_display.number_of_nodes()}** nós e **{G_display.number_of_edges()}** arestas.")

    else: # Núcleo Principal (k-core)
        try:
            # Calcula o subgrafo k-core
            k_core_subgraph = nx.k_core(G.to_undirected(), k=k_core_value)
            if not k_core_subgraph.nodes():
                 st.sidebar.warning(f"Não existe um {k_core_value}-core nesta rede. Tente um valor de 'k' menor.")
                 G_display = nx.DiGraph() # Grafo vazio para evitar erros
            else:
                G_display = nx.DiGraph(k_core_subgraph)
                st.sidebar.info(f"Analisando o {k_core_value}-core com **{G_display.number_of_nodes()}** nós e **{G_display.number_of_edges()}** arestas.")
        except Exception as e:
            st.sidebar.error(f"Erro ao calcular o k-core: {e}")
            G_display = G.copy()


    tab_metricas, tab_dist, tab_centralidade, tab_rede = st.tabs([
        "📊 Métricas", 
        "📈 Distribuição de Grau", 
        "🏆 Centralidade", 
        "🕸️ Rede Interativa"
    ])

    with tab_metricas:
        st.header(f"Métricas Estruturais: {subgraph_option}")
        
        if G_display.number_of_nodes() > 0:
            # Calcula as métricas para o grafo em exibição (G_display)
            densidade = nx.density(G_display)
            try:
                assortatividade = nx.degree_assortativity_coefficient(G_display, x='out', y='in')
                assort_str = f"{assortatividade:.4f}"
            except Exception:
                assort_str = "Não aplicável"

            coef_clustering = nx.average_clustering(G_display.to_undirected())
            
            num_scc = nx.number_strongly_connected_components(G_display)
            num_wcc = nx.number_weakly_connected_components(G_display)

            # Exibe as métricas em colunas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Densidade", f"{densidade:.4f}", help="Mede quão conectada a rede é (0 a 1). Valores baixos indicam uma rede esparsa.")
            with col2:
                st.metric("Assortatividade", assort_str, help="Tendência de nós se conectarem a outros com grau similar. (+): ricos com ricos.")
            with col3:
                st.metric("Coef. de Clustering", f"{coef_clustering:.4f}", help="Mede a tendência dos nós formarem 'clusters' ou grupos fechados (triângulos).")

            st.subheader("Componentes Conectados")
            col4, col5 = st.columns(2)
            with col4:
                st.metric("Componentes Fortemente Conectados", num_scc, help="Grupos onde cada nó alcança todos os outros seguindo a direção das arestas.")
            with col5:
                st.metric("Componentes Fracamente Conectados", num_wcc, help="Grupos de nós que estariam conectados se as direções das arestas fossem ignoradas.")
        else:
            st.warning("Não há nós no subgrafo selecionado para calcular as métricas.")


    with tab_dist:
        st.header(f"Distribuição de Grau: {subgraph_option}")

        if G_display.number_of_nodes() > 0:
            degree_type = st.radio(
                "Selecione o tipo de grau para visualizar:",
                ("Grau Total", "Grau de Entrada (In-degree)", "Grau de Saída (Out-degree)"),
                horizontal=True
            )
            
            if degree_type == "Grau Total":
                degrees = [val for (node, val) in G_display.degree]
                title = "Distribuição de Grau Total"
                xlabel = "Grau Total"
            elif degree_type == "Grau de Entrada (In-degree)":
                degrees = [val for (node, val) in G_display.in_degree]
                title = "Distribuição de Grau de Entrada (In-degree)"
                xlabel = "Grau de Entrada"
            else: # Grau de Saída (Out-degree)
                degrees = [val for (node, val) in G_display.out_degree]
                title = "Distribuição de Grau de Saída (Out-degree)"
                xlabel = "Grau de Saída"

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(degrees, bins=30)
            ax.set_title(title, fontsize=16)
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel("Frequência (Nº de Nós)", fontsize=12)
            ax.grid(axis='y', alpha=0.75)

            st.pyplot(fig)
        else:
            st.warning("Não há nós no subgrafo selecionado para exibir a distribuição.")
                
    with tab_centralidade:
        st.header("Ranking de Nós por Centralidade")

        if G_display.number_of_nodes() == 0:
            st.warning("Não há nós no subgrafo selecionado para calcular centralidades.")
        else:
            k = st.slider("Quantos nós (top-k) mostrar em cada métrica?", 1, 20, 10)

            # 1. Calcular centralidades
            # Degree centrality
            deg_cent = nx.degree_centrality(G_display)
            # Eigenvector centrality (precisa de grafo não direcionado)
            eigen_cent = nx.eigenvector_centrality_numpy(G_display.to_undirected())
            # Closeness centrality
            close_cent = nx.closeness_centrality(G_display)
            # Betweenness centrality
            btw_cent = nx.betweenness_centrality(G_display)

            df_cent = pd.DataFrame({
                "Degree": deg_cent,
                "Eigenvector": eigen_cent,
                "Closeness": close_cent,
                "Betweenness": btw_cent
            }).reset_index().rename(columns={"index": "Node"})

            # 3. Mostrar rankings em colunas
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader(f"Top {k} por Degree Centrality")
                st.table(df_cent.nlargest(k, "Degree")[["Node", "Degree"]].set_index("Node"))
                st.subheader(f"Top {k} por Closeness")
                st.table(df_cent.nlargest(k, "Closeness")[["Node", "Closeness"]].set_index("Node"))
            with col_b:
                st.subheader(f"Top {k} por Eigenvector")
                st.table(df_cent.nlargest(k, "Eigenvector")[["Node", "Eigenvector"]].set_index("Node"))
                st.subheader(f"Top {k} por Betweenness")
                st.table(df_cent.nlargest(k, "Betweenness")[["Node", "Betweenness"]].set_index("Node"))
        
    with tab_rede:
        st.header(f"Visualização Interativa: {subgraph_option}")
        
        if G_display.number_of_nodes() > 0:
            try:
                net = Network(height="750px", width="100%", bgcolor="#D8D8D8", directed=True, notebook=False)
                net.toggle_physics(physics_enabled)
                if physics_enabled:
                    net.show_buttons(filter_=['physics'])
                net.from_nx(G_display)
                html_file = net.generate_html('graph.html')
                components.html(html_file, height=800, scrolling=True)
            except Exception as e:
                st.error(f"Ocorreu um erro ao gerar o grafo: {e}")
        else:
            st.warning("Não há nós no subconjunto selecionado para exibir.")
else:
    st.warning("O grafo não pôde ser carregado. Verifique o arquivo .graphml.")
