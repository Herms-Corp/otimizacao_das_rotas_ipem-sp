"""IPEM-SP — MVP acadêmico v2.
Consulta 800 agrupamentos RLD_ID; planejamento limitado a visitas geolocalizadas.
Base 2018. Não interpreta HORARIO_INICIO/FIM como duração de atendimento.
"""
from pathlib import Path
from html import escape
import io
import numpy as np
import pandas as pd
import requests
import folium
import streamlit as st
import streamlit.components.v1 as components
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

st.set_page_config(page_title="IPEM-SP | Rotas e Fiscalizações", page_icon="🗺️", layout="wide")
BASE = Path(__file__).resolve().parent / "dados_ipem"
POLO = (-23.179828551507942, -45.88085325270693)
COLS_COORD = ["RLD_ID", "COD_PROPR", "LATITUDE", "LONGITUDE", "STATUS_GEO", "FONTE_GEO"]

@st.cache_data

def ler_historico():
    p = BASE / "rotas_historicas.csv"
    df = pd.read_csv(p, encoding="utf-8-sig", low_memory=False)
    obrig = {"RLD_ID", "COD_PROPR", "ORDEM_HISTORICA", "ESTABELECIMENTO", "ENDERECO"}
    if not obrig.issubset(df.columns):
        raise ValueError(f"Colunas históricas ausentes: {sorted(obrig-set(df.columns))}")
    for c in ("RLD_ID", "COD_PROPR", "ORDEM_HISTORICA"):
        df[c] = pd.to_numeric(df[c], errors="raise").astype(int)
    return df.sort_values(["RLD_ID", "ORDEM_HISTORICA"]).reset_index(drop=True)

@st.cache_data

def ler_piloto():
    p = BASE / "fiscalizacoes.csv"
    if not p.exists():
        return pd.DataFrame(columns=["RLD_ID", "COD_PROPR", "ENDERECO", "LATITUDE", "LONGITUDE"])
    df = pd.read_csv(p, encoding="utf-8-sig", low_memory=False)
    for c in ["RLD_ID", "COD_PROPR", "LATITUDE", "LONGITUDE"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def ler_manuais():
    p = BASE / "coordenadas_historicas.csv"
    if not p.exists() or p.stat().st_size == 0:
        return pd.DataFrame(columns=COLS_COORD)
    df = pd.read_csv(p, encoding="utf-8-sig")
    for c in COLS_COORD:
        if c not in df.columns:
            df[c] = None
    for c in ["RLD_ID", "COD_PROPR", "LATITUDE", "LONGITUDE"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["RLD_ID", "COD_PROPR"])
    if df.empty:
        return df[COLS_COORD]
    df["RLD_ID"] = df["RLD_ID"].astype(int)
    df["COD_PROPR"] = df["COD_PROPR"].astype(int)
    return df[COLS_COORD].drop_duplicates(["RLD_ID", "COD_PROPR"], keep="last")


def completar_geografia(historico, piloto, manuais):
    base = historico.copy()
    # Apenas registros do mesmo empreendimento com o MESMO endereço cadastral.
    campos = ["COD_PROPR", "ENDERECO", "LATITUDE", "LONGITUDE"]
    if set(campos).issubset(piloto.columns):
        p = piloto[campos].dropna().copy()
        p = p[p["LATITUDE"].between(-90, 90) & p["LONGITUDE"].between(-180, 180)]
        # Impede associar endereço+estabelecimento a múltiplas coordenadas conflitantes.
        p = p.groupby(["COD_PROPR", "ENDERECO"], dropna=False).filter(
            lambda x: len(x[["LATITUDE", "LONGITUDE"]].drop_duplicates()) == 1
        ).drop_duplicates(["COD_PROPR", "ENDERECO"])
        base = base.merge(p, on=["COD_PROPR", "ENDERECO"], how="left", validate="many_to_one")
    else:
        base["LATITUDE"] = np.nan
        base["LONGITUDE"] = np.nan
    base["STATUS_GEO"] = np.where(base["LATITUDE"].notna(), "PILOTO_A_CONFERIR", "PENDENTE")
    base["FONTE_GEO"] = np.where(base["LATITUDE"].notna(), "Coordenadas de demonstração", "")
    if len(manuais):
        base = base.merge(manuais, on=["RLD_ID", "COD_PROPR"], how="left",
                          validate="one_to_one", suffixes=("", "_MANUAL"))
        manual_ok = base["LATITUDE_MANUAL"].between(-90, 90) & base["LONGITUDE_MANUAL"].between(-180, 180)
        for c in ["LATITUDE", "LONGITUDE", "STATUS_GEO", "FONTE_GEO"]:
            base.loc[manual_ok, c] = base.loc[manual_ok, f"{c}_MANUAL"]
            base.drop(columns=[f"{c}_MANUAL"], inplace=True)
    valida = base["LATITUDE"].between(-90, 90) & base["LONGITUDE"].between(-180, 180)
    base.loc[~valida, ["LATITUDE", "LONGITUDE"]] = np.nan
    base["LOCALIZADA"] = valida
    return base


def posicoes_unicas(registros):
    return (registros[registros["LOCALIZADA"]]
            .sort_values(["RLD_ID", "ORDEM_HISTORICA"])
            .drop_duplicates(["LATITUDE", "LONGITUDE"])
            .reset_index(drop=True))

@st.cache_data(ttl=86400, show_spinner=False)
def consultar_matriz(coords):
    # coords: tupla de (latitude,longitude), polo incluído.
    if len(coords) > 26:
        raise ValueError("Limite de 25 posições físicas por simulação para proteger o serviço público OSRM.")
    texto = ";".join(f"{lon:.9f},{lat:.9f}" for lat, lon in coords)
    resposta = requests.get(
        f"https://router.project-osrm.org/table/v1/driving/{texto}",
        params={"annotations":"distance,duration"}, timeout=45)
    resposta.raise_for_status()
    dados = resposta.json()
    if dados.get("code") != "Ok":
        raise RuntimeError(f"OSRM: {dados.get('code', 'erro desconhecido')}")
    dist = np.asarray(dados["distances"], dtype=float)
    dur = np.asarray(dados["durations"], dtype=float)
    if dist.shape != (len(coords),len(coords)) or not np.isfinite(dist).all() or not np.isfinite(dur).all():
        raise RuntimeError("Serviço de rotas retornou distâncias ou tempos incompletos.")
    return dist, dur

@st.cache_data(ttl=86400, show_spinner=False)
def consultar_geometria(coords):
    texto = ";".join(f"{lon:.9f},{lat:.9f}" for lat,lon in coords)
    resposta = requests.get(f"https://router.project-osrm.org/route/v1/driving/{texto}",
         params={"overview":"full", "geometries":"geojson", "steps":"false"}, timeout=45)
    resposta.raise_for_status()
    dados = resposta.json()
    if dados.get("code") != "Ok" or not dados.get("routes"):
        raise RuntimeError(f"OSRM: {dados.get('code','sem trajeto')}")
    return dados["routes"][0]["geometry"]


def otimizar_matriz(dist_m, modalidade, destino_idx=None):
    # Polo = índice 0; demais índices 1..N, preservados.
    n = len(dist_m)
    custos = np.rint(dist_m).astype(np.int64)
    if modalidade == "Circuito fechado":
        fim = 0
    elif modalidade == "Destino específico":
        if destino_idx is None or not 1 <= destino_idx < n:
            raise ValueError("Escolha um destino entre as posições de fiscalização.")
        fim = int(destino_idx)
    else:
        # Nó virtual absorve o término sem custo adicional.
        nova = np.zeros((n + 1, n + 1), dtype=np.int64)
        nova[:n, :n] = custos
        custos = nova
        fim = n
    manager = pywrapcp.RoutingIndexManager(len(custos), 1, [0], [fim])
    routing = pywrapcp.RoutingModel(manager)
    def custo(i, j):
        return int(custos[manager.IndexToNode(i),manager.IndexToNode(j)])
    transit = routing.RegisterTransitCallback(custo)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)
    pars = pywrapcp.DefaultRoutingSearchParameters()
    pars.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    pars.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    pars.time_limit.seconds = 4
    sol = routing.SolveWithParameters(pars)
    if not sol:
        raise RuntimeError("Nenhuma solução foi encontrada.")
    seq = []
    idx = routing.Start(0)
    while not routing.IsEnd(idx):
        seq.append(manager.IndexToNode(idx))
        idx = sol.Value(routing.NextVar(idx))
    if modalidade != "Rota aberta":
        seq.append(manager.IndexToNode(idx))
    visitados = [i for i in seq if i != 0]
    if len(visitados) != n-1 or set(visitados) != set(range(1,n)):
        raise RuntimeError("A validação de atendimento dos destinos falhou.")
    return seq


def total_percurso(matriz, sequencia):
    return sum(float(matriz[a,b]) for a,b in zip(sequencia[:-1],sequencia[1:]))


def mapa_numerado(coords, titulos, sequencia, desenho_viario=True):
    pts = [coords[i] for i in sequencia]
    mapa = folium.Map(location=list(POLO), zoom_start=10, tiles=None)
    folium.TileLayer(tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        attr="Map data: OpenStreetMap contributors | Map style: OpenTopoMap").add_to(mapa)
    teve_vias = False
    if desenho_viario and len(pts) > 1:
        try:
            geo = consultar_geometria(tuple(pts))
            folium.GeoJson(geo, style_function=lambda _: {"color":"#2563eb","weight":4,"opacity":0.8}).add_to(mapa)
            teve_vias = True
        except (requests.RequestException, RuntimeError, ValueError, KeyError) as exc:
            st.warning(f"Traçado viário indisponível: {exc}. Exibindo apenas paradas, sem inventar trajeto.")
    grupos = {}
    contador = 0
    for ordem, idx in enumerate(sequencia):
        lat,lon = coords[idx]
        if idx == 0:
            numero = "P"
        else:
            contador += 1
            numero = str(contador)
        grupos.setdefault((lat,lon), []).append((numero, titulos[idx]))
    for (lat,lon), dados in grupos.items():
        numeros = [num for num,_ in dados if num != "P"]
        rotulo = ", ".join(numeros) if numeros else "P"
        texto = "<hr>".join(f"{escape(a)} — {escape(str(b))}" for a,b in dados)
        tamanho = min(175, max(32, 14+len(rotulo)*8))
        cor = "#1d4ed8" if numeros else "#b91c1c"
        html = (f'<div style="width:{tamanho}px;min-height:29px;line-height:29px;'
                f'border-radius:16px;border:2px solid white;background:{cor};color:white;'
                f'font-size:12px;font-weight:700;text-align:center;white-space:nowrap">{escape(rotulo)}</div>')
        folium.Marker([lat,lon],tooltip=f"Parada(s): {rotulo}",
                      popup=folium.Popup(texto,max_width=420),
                      icon=folium.DivIcon(html=html,icon_size=(tamanho,32),icon_anchor=(tamanho//2,16))).add_to(mapa)
    mapa.fit_bounds(pts)
    return mapa, teve_vias


def exibir_mapa(mapa):
    components.html(mapa._repr_html_(),height=540,scrolling=False)


def detalhar_comparacao(base, coords, posicoes, modalidade, termino):
    with st.spinner("Consultando distâncias viárias e calculando o percurso..."):
        dist_m, tempo_s = consultar_matriz(tuple(coords))
        seq = otimizar_matriz(dist_m, modalidade, termino)
    km = total_percurso(dist_m,seq)/1000
    mins = total_percurso(tempo_s,seq)/60
    titulos = ["Polo Regional IPEM-SP"] + [str(r.ESTABELECIMENTO)+" | "+str(r.ENDERECO) for r in posicoes.itertuples()]
    c1,c2,c3 = st.columns(3)
    c1.metric("Posições atendidas", len(posicoes))
    c2.metric("Distância viária estimada", f"{km:.2f} km")
    c3.metric("Tempo de viagem estimado", f"{mins:.1f} min")
    tabela = pd.DataFrame({"ETAPA":range(len(seq)),"LOCAL":[titulos[i] for i in seq]})
    st.dataframe(tabela,hide_index=True,use_container_width=True)
    st.download_button("Baixar sequência otimizada (CSV)",
        tabela.to_csv(index=False).encode("utf-8-sig"),"sequencia_otimizada_v2.csv",mime="text/csv")
    mapa, vias = mapa_numerado(coords,titulos,seq)
    exibir_mapa(mapa)
    st.caption("Paradas numeradas; números agrupados indicam posições coincidentes. " +
               ("Linha pelas vias obtida do OSRM." if vias else "Sem traçado viário disponível."))
    return km, mins, seq, dist_m, tempo_s


def painel_geo(rota, manuais):
    st.subheader("Cadastrar ou corrigir coordenadas")
    st.caption("Somente coordenadas verificadas. Salva em CSV no computador; não faça cadastros em hospedagem pública sem persistência de dados.")
    opcoes = rota["COD_PROPR"].astype(int).tolist()
    if not opcoes:
        return
    nomes = dict(zip(rota["COD_PROPR"], rota["ESTABELECIMENTO"]))
    cod = st.selectbox("Registro", opcoes,format_func=lambda x: f"{x} | {nomes[x]}")
    atual = rota.loc[rota["COD_PROPR"]==cod].iloc[0]
    with st.form("form_geo_v2"):
        lat = st.number_input("Latitude",value=float(atual.LATITUDE) if pd.notna(atual.LATITUDE) else -23.0, min_value=-90.0,max_value=90.0,format="%.9f")
        lon = st.number_input("Longitude",value=float(atual.LONGITUDE) if pd.notna(atual.LONGITUDE) else -45.0,min_value=-180.0,max_value=180.0,format="%.9f")
        qualidade = st.selectbox("Qualidade",["CONFIRMADA","APROXIMADA"])
        fonte = st.text_input("Fonte / evidência da coordenada")
        salvar = st.form_submit_button("Salvar no cadastro local")
    if salvar:
        if not fonte.strip():
            st.error("Informe a fonte antes de salvar.")
        else:
            novo = pd.DataFrame([{"RLD_ID":int(atual.RLD_ID),"COD_PROPR":int(cod),
                "LATITUDE":lat,"LONGITUDE":lon,"STATUS_GEO":qualidade,"FONTE_GEO":fonte.strip()}])
            anterior = manuais.loc[~((manuais["RLD_ID"]==int(atual.RLD_ID)) &
                (manuais["COD_PROPR"]==int(cod)))].copy()
            final = pd.concat([anterior,novo],ignore_index=True)
            try:
                BASE.mkdir(exist_ok=True)
                final.to_csv(BASE/"coordenadas_historicas.csv",index=False,encoding="utf-8-sig")
                st.success("Coordenada salva localmente. Atualize a página para refletir a alteração.")
            except OSError as exc:
                st.error(f"Não foi possível salvar: {exc}")


st.title("IPEM-SP | Gestão e Planejamento de Fiscalizações")
st.warning("VERSÃO DEMONSTRATIVA: nomes, endereços, equipes, identificadores e coordenadas fictícios. Não utilizar para decisões operacionais.")
try:
    hist = ler_historico()
    piloto = ler_piloto()
    manuais = ler_manuais()
    base = completar_geografia(hist,piloto,manuais)
except (OSError, ValueError, KeyError) as exc:
    st.error(f"Falha ao carregar os dados: {exc}")
    st.stop()

resumo = base.groupby("RLD_ID",as_index=False).agg(
    DATA=("DATA","first"),FISCAL=("FISCAL","first"),
    FISCALIZACOES=("COD_PROPR","size"), LOCALIZADAS=("LOCALIZADA","sum"),
    ENDERECOS=("ENDERECO","nunique"))
resumo["PENDENTES"] = resumo["FISCALIZACOES"]-resumo["LOCALIZADAS"]
resumo["COBERTURA_%"] = (100*resumo["LOCALIZADAS"]/resumo["FISCALIZACOES"]).round(1)

aba_geral, aba_historicas, aba_planejar = st.tabs(["Visão geral","Rotas históricas e otimização","Planejar nova rota"])
with aba_geral:
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Agrupamentos históricos",len(resumo))
    c2.metric("Fiscalizações consolidadas",len(base))
    c3.metric("Fiscalizações com coordenadas",int(base.LOCALIZADA.sum()))
    c4.metric("Cobertura geográfica",f"{100*base.LOCALIZADA.mean():.1f}%")
    st.caption("Os 5.381 registros consolidados não são iguais aos registros brutos de verificação. "
               "A cobertura indica presença de coordenadas, não validação de precisão.")
    st.dataframe(resumo,hide_index=True,use_container_width=True,height=360)
    st.download_button("Baixar indicadores por rota",resumo.to_csv(index=False).encode("utf-8-sig"),
        "indicadores_ipem.csv",mime="text/csv")
    st.info("RLD_ID é um agrupamento cadastral. HORARIO_INICIO e HORARIO_FIM servem apenas como referências cronológicas. "
            "A origem informada é o Polo Regional; o destino real de cada rota histórica pode ser diferente.")

with aba_historicas:
    ids = resumo["RLD_ID"].astype(int).tolist()
    pidx = ids.index(100421) if 100421 in ids else 0
    escolha = st.selectbox("Selecionar RLD_ID",ids,index=pidx,
        format_func=lambda x: f"{x} | {int(resumo.loc[resumo.RLD_ID==x,'FISCALIZACOES'].iloc[0])} fiscalizações")
    rota = base[base.RLD_ID==escolha].sort_values("ORDEM_HISTORICA").copy()
    local = rota[rota.LOCALIZADA].copy()
    unico = posicoes_unicas(rota)
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Fiscalizações",len(rota))
    c2.metric("Com coordenadas",len(local))
    c3.metric("Posições distintas",len(unico))
    c4.metric("Pendências",len(rota)-len(local))
    st.progress(len(local)/len(rota),text=f"Cobertura de localização: {len(local)}/{len(rota)}")
    st.dataframe(rota[["ORDEM_HISTORICA","ESTABELECIMENTO","ENDERECO","COD_PROPR","STATUS_GEO","LATITUDE","LONGITUDE"]],
                 hide_index=True,use_container_width=True,height=310)
    st.download_button("Baixar registros da rota",rota.to_csv(index=False).encode("utf-8-sig"),
                       f"ipem_rota_{escolha}.csv",mime="text/csv")
    if len(local):
        st.subheader("Mapa histórico: ordem cronológica dos registros localizados")
        # Histórico numerado pelos números originais, inclusive lacunas. Mesmo local agrega rótulos.
        coords_hist=[POLO]+[(float(r.LATITUDE),float(r.LONGITUDE)) for r in local.itertuples()]
        tit_hist=["Polo IPEM"]+[f"{int(r.ORDEM_HISTORICA)} — {r.ESTABELECIMENTO}" for r in local.itertuples()]
        # Rótulo do histórico será a ordem original através de helper específico abaixo.
        m=folium.Map(location=[float(local.LATITUDE.mean()),float(local.LONGITUDE.mean())],zoom_start=13,tiles=None)
        folium.TileLayer(tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
                         attr="OpenStreetMap contributors | OpenTopoMap").add_to(m)
        pontos_grupo={}
        for r in local.itertuples():
            p=(float(r.LATITUDE),float(r.LONGITUDE))
            pontos_grupo.setdefault(p,[]).append((int(r.ORDEM_HISTORICA),f"{r.ESTABELECIMENTO} | {r.ENDERECO}"))
        for (lat,lon), registros in pontos_grupo.items():
            rotulo=",".join(str(n) for n,_ in registros)
            largura=min(180,max(32,20+len(rotulo)*8))
            texto="<hr>".join(f"{n}. {escape(v)}" for n,v in registros)
            html=f'<div style="border:2px solid white;border-radius:14px;color:white;background:#2563eb;text-align:center;font-weight:bold;padding:6px;white-space:nowrap">{escape(rotulo)}</div>'
            folium.Marker([lat,lon],tooltip=f"Fiscalizações: {rotulo}",popup=folium.Popup(texto,max_width=420),
               icon=folium.DivIcon(html=html,icon_size=(largura,34),icon_anchor=(largura//2,17))).add_to(m)
        folium.Marker(POLO,tooltip="Polo de partida",icon=folium.Icon(color="red",icon="home")).add_to(m)
        # Deliberadamente não conecta visitas incompletas como rota verdadeira.
        m.fit_bounds([POLO]+list(pontos_grupo))
        exibir_mapa(m)
        st.caption("Números = ordem cronológica original; ausência de número indica visita sem coordenadas. "
                   "Sem traçado de percurso completo quando há visitas não localizadas.")
    else:
        st.info("Esta rota está catalogada, mas ainda não possui visitas geolocalizadas.")
    st.subheader("Otimização para a rota selecionada")
    if len(local) != len(rota):
        st.warning("Rota geograficamente incompleta: a otimização possível será PARCIAL e não poderá demonstrar economia histórica integral.")
    if len(unico)>25:
        st.warning("Mais de 25 posições: selecione um subconjunto na aba Planejar nova rota.")
    elif len(unico):
        modalidades=["Circuito fechado","Rota aberta","Destino específico"]
        mod=st.radio("Condição de encerramento simulada",modalidades,horizontal=True,key="mod_hist")
        fim = None
        if mod=="Destino específico":
            fim=st.selectbox("Último estabelecimento",list(range(1,len(unico)+1)),
               format_func=lambda i: f"{unico.iloc[i-1]['ESTABELECIMENTO']} | {unico.iloc[i-1]['ENDERECO']}",key="fim_hist")
        if st.button("Otimizar esta rota",type="primary",key="otim_hist"):
            try:
                coords=[POLO]+[(float(r.LATITUDE),float(r.LONGITUDE)) for r in unico.itertuples()]
                km,mins,seq,dist_m,tempo_s=detalhar_comparacao(rota,coords,unico,mod,fim)
                if len(local)==len(rota):
                    # Comparação consolidada: mesmíssimas posições, ordem por primeira ocorrência.
                    indice_coord={p:i for i,p in enumerate(coords)}
                    seq_hist=[0]+[indice_coord[(float(r.LATITUDE),float(r.LONGITUDE))] for r in unico.itertuples()]
                    if mod=="Circuito fechado":
                        seq_hist += [0]
                    elif mod=="Destino específico":
                        # Não se pode fixar o último ponto sem modificar a ordem histórica observada.
                        seq_hist=[]
                    if seq_hist:
                        hist_km=total_percurso(dist_m,seq_hist)/1000
                        st.metric("Histórica consolidada (mesma hipótese de término)",f"{hist_km:.2f} km")
                        st.caption("Comparação ilustrativa: agrupamento por primeira visita, não reconstituição auditada. "
                                   "A rota aberta termina na última visita histórica, que pode diferir do ponto final otimizado.")
                else:
                    st.caption("Não há comparação total porque faltam posições geográficas.")
            except (requests.RequestException,RuntimeError,ValueError,AssertionError) as exc:
                st.error(f"Não foi possível otimizar: {exc}")
    with st.expander("Cadastrar coordenadas para esta rota"):
        painel_geo(rota,manuais)

with aba_planejar:
    st.subheader("Planejamento livre a partir das fiscalizações cadastradas")
    st.caption("Selecione locais de qualquer rota histórica com coordenadas disponíveis. "
               "Dois registros na mesma coordenada contam como duas fiscalizações, mas uma parada.")
    disponiveis=base[base.LOCALIZADA].copy().reset_index(drop=True)
    disponiveis["ID_SELECAO"]=disponiveis.index
    nomes={int(r.ID_SELECAO): f"Rota {r.RLD_ID} | {r.ESTABELECIMENTO} | {r.ENDERECO}" for r in disponiveis.itertuples()}
    ids_sel=st.multiselect("Fiscalizações a incluir",options=disponiveis.ID_SELECAO.tolist(),
                           format_func=lambda i:nomes[i], key="selecoes_v2")
    escolhidas=disponiveis[disponiveis.ID_SELECAO.isin(ids_sel)].copy()
    pontos=escolhidas.drop_duplicates(["LATITUDE","LONGITUDE"]).reset_index(drop=True)
    c1,c2=st.columns(2)
    c1.metric("Fiscalizações selecionadas",len(escolhidas))
    c2.metric("Paradas físicas distintas",len(pontos))
    if len(escolhidas):
        st.dataframe(escolhidas[["RLD_ID","ESTABELECIMENTO","ENDERECO"]],hide_index=True,use_container_width=True)
    modo=st.radio("Encerramento",["Circuito fechado","Rota aberta","Destino específico"],horizontal=True,key="mod_livre")
    fim=None
    if modo=="Destino específico" and len(pontos):
        fim=st.selectbox("Local de encerramento",list(range(1,len(pontos)+1)),
                         format_func=lambda i:f"{pontos.iloc[i-1]['ESTABELECIMENTO']} | {pontos.iloc[i-1]['ENDERECO']}")
    if len(pontos)>25:
        st.warning("Para evitar sobrecarregar a API de demonstração do OSRM, selecione até 25 posições físicas por planejamento.")
    if st.button("Calcular rota planejada",type="primary",disabled=not (1<=len(pontos)<=25)):
        try:
            coords=[POLO]+[(float(r.LATITUDE),float(r.LONGITUDE)) for r in pontos.itertuples()]
            detalhar_comparacao(escolhidas,coords,pontos,modo,fim)
        except (requests.RequestException,RuntimeError,ValueError,AssertionError) as exc:
            st.error(f"Não foi possível otimizar: {exc}")
    st.info("As localizações podem ser ampliadas pelo cadastro de coordenadas na aba Rotas históricas. "
            "Não há geocodificação automática em massa nesta versão; a API pública OSRM é usada apenas para pequenos conjuntos de destinos.")
