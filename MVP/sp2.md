# 📌 MVP — PLANEJAMENTO E OTIMIZAÇÃO DE ROTAS DE FISCALIZAÇÃO
## Sprint 02 — IPEM-SP

### 🎯 Objetivo do MVP

O objetivo da segunda sprint é evoluir o painel interativo desenvolvido na Sprint 1 para uma aplicação web capaz de **consultar, planejar, simular e otimizar rotas de fiscalização do IPEM-SP**.

A solução utiliza dados históricos de fiscalizações realizadas em 2018, algoritmos de otimização e serviços de roteamento geográfico para apoiar a tomada de decisão no planejamento das atividades em campo.

Com essa evolução, buscamos contribuir para:

- Reduzir deslocamentos desnecessários entre estabelecimentos.
- Melhorar a sequência de visitas das equipes de fiscalização.
- Identificar oportunidades de otimização de distância e tempo.
- Facilitar a visualização de rotas históricas e planejadas.
- Disponibilizar uma ferramenta de apoio à gestão operacional.

Esta sprint constitui a etapa de desenvolvimento e validação do modelo de roteirização, preparando a solução para os aprimoramentos da Sprint 3.

---

### 📝 Descrição da Solução

Foi desenvolvido um MVP web utilizando **Python e Streamlit**, integrando tratamento de dados, geolocalização, cálculo de distâncias viárias e otimização matemática de rotas.

A aplicação permite consultar as rotas históricas cadastradas, visualizar estabelecimentos fiscalizados e realizar simulações de planejamento com diferentes condições de origem e destino.

**Principais funcionalidades implementadas:**

**1. Dashboard gerencial**
- Consulta às 800 rotas históricas identificadas na base de 2018.
- Indicadores consolidados de fiscalizações e cobertura geográfica.
- Identificação de registros geolocalizados e pendentes.
- Consulta de informações por rota.

**2. Visualização geográfica**
- Mapas interativos desenvolvidos com Folium.
- Exibição dos pontos de fiscalização com sequência numérica.
- Representação de trajetos pelas ruas e rodovias utilizando OSRM.
- Identificação do Polo Regional do IPEM-SP como origem operacional.

**3. Planejamento de rotas**
- Seleção de estabelecimentos cadastrados.
- Agrupamento de fiscalizações que compartilham uma posição geográfica.
- Configuração de três modalidades: rota fechada, rota aberta e destino específico.
- Otimização da sequência de visitas utilizando Google OR-Tools.
- Apresentação de distância, tempo estimado e sequência recomendada.

**4. Comparação de desempenho**
- Comparação entre a sequência histórica consolidada e a sequência otimizada.
- Cálculo da distância viária e do tempo estimado de deslocamento.
- Identificação de oportunidades de redução nos trajetos entre estabelecimentos.

**5. Gestão de coordenadas**
- Indicadores de cobertura geográfica.
- Identificação de estabelecimentos sem coordenadas disponíveis.
- Estrutura para cadastro e atualização progressiva das localizações.

### Limitações identificadas

A base histórica ainda apresenta cobertura geográfica limitada, impedindo a otimização integral de todas as rotas.

Os horários registrados foram classificados como referências cronológicas, pois não demonstraram confiabilidade suficiente para calcular o tempo efetivo de fiscalização.

Além disso, a variável `RLD_ID` foi utilizada como agrupamento histórico de registros. Sua correspondência exata com uma rota operacional executada ainda depende de confirmação.

Consequentemente, os resultados de otimização representam **simulações de roteirização**, não economias operacionais efetivamente observadas.

---

### 👥 Personas / Usuários-Alvo

**Gestor do IPEM-SP**

Necessita de informações consolidadas e ferramentas de planejamento para avaliar o deslocamento das equipes, identificar oportunidades de melhoria e apoiar a distribuição das fiscalizações.

**Fiscal de campo**

Necessita visualizar os estabelecimentos programados, consultar sua sequência de atendimento e obter sugestões de percursos mais eficientes.

**Responsável pelo planejamento operacional**

Necessita configurar novas rotas, avaliar alternativas de deslocamento e estimar distâncias e tempos necessários para o atendimento dos estabelecimentos.

---

### 🔑 User Stories — Backlog do MVP

| ID | User Story | Prioridade | Estimativa | Status |
|---|---|---|---|---|
| US01 | Como gestor, quero consultar as rotas históricas para compreender a distribuição das fiscalizações realizadas. | Alta | 5 | Concluído |
| US02 | Como gestor, quero visualizar indicadores de cobertura geográfica para identificar registros pendentes de localização. | Alta | 4 | Concluído |
| US03 | Como fiscal, quero visualizar os pontos numerados no mapa para compreender a sequência de visitas. | Alta | 5 | Concluído |
| US04 | Como responsável pelo planejamento, quero selecionar estabelecimentos para montar uma nova rota de fiscalização. | Alta | 5 | Concluído para os pontos cadastrados |
| US05 | Como gestor, quero otimizar a sequência das visitas para reduzir a distância estimada de deslocamento. | Alta | 5 | Concluído para rotas geolocalizadas |
| US06 | Como fiscal, quero configurar o destino final para adaptar o planejamento às necessidades da equipe. | Média | 4 | Concluído |
| US07 | Como gestor, quero comparar rotas históricas e otimizadas para identificar oportunidades de melhoria. | Alta | 5 | Validado na rota piloto |
| US08 | Como responsável pelo planejamento, quero ampliar a geolocalização dos endereços para otimizar mais rotas históricas. | Alta | 5 | Parcial — evolução na Sprint 3 |

*As estimativas representam esforço relativo do backlog, em pontos.*

---

### 📅 Sprints Relacionadas

| Sprint | Entregas principais | Status |
|---|---|---|
| 01 | Dashboard interativo com dados gerais das fiscalizações de 2018 e análise histórica das atividades. | Concluído |
| **02** | **Aplicação web com consulta histórica, mapas numerados, planejamento de rotas, otimização por OR-Tools e comparação de indicadores viários.** | **Concluído — MVP validado** |
| 03 | Ampliação da cobertura geográfica, aprimoramento da roteirização, validações operacionais e evolução do sistema para utilização em cenários mais abrangentes. | Planejado |

---

### 📊 Critérios de Aceitação

Para considerar a Sprint 2 concluída, foram estabelecidos os seguintes critérios:

- [x] Disponibilizar uma aplicação web funcional.
- [x] Permitir consultar os 800 agrupamentos históricos identificados.
- [x] Exibir indicadores de cobertura geográfica.
- [x] Apresentar marcadores numerados nos mapas das rotas localizadas.
- [x] Permitir selecionar estabelecimentos para planejamento.
- [x] Implementar otimização utilizando OR-Tools.
- [x] Calcular distâncias e tempos de deslocamento pela malha viária com OSRM.
- [x] Permitir configurar diferentes modalidades de encerramento da rota.
- [x] Validar o funcionamento do algoritmo em uma rota piloto.
- [x] Preservar separadamente fiscalizações registradas e posições geográficas distintas.

**Critério de qualidade:** o sistema deve identificar limitações de geolocalização e não apresentar rotas incompletas como otimizações integrais.

---

### 📈 Métricas de Validação

#### 1. Base histórica

| Indicador | Resultado |
|---|---:|
| Agrupamentos históricos identificados (`RLD_ID`) | 800 |
| Combinações consolidadas de rota e estabelecimento | 5.381 |
| Registros com coordenadas disponíveis na base de demonstração inicial | 26 |
| Cobertura geográfica inicial | Aproximadamente 0,5% |

A baixa cobertura geográfica representa uma limitação da base de endereços, não do algoritmo de otimização.

#### 2. Rota piloto — RLD_ID 1863587

| Indicador | Resultado |
|---|---:|
| Fiscalizações históricas | 27 |
| Fiscalizações com coordenadas | 26 |
| Posições geográficas distintas | 21 |
| Distância histórica consolidada simulada | 186,82 km |
| Distância otimizada | 175,15 km |
| Redução estimada de distância | 11,68 km |
| Redução percentual estimada | 6,25% |
| Tempo de deslocamento histórico estimado | 217,38 minutos |
| Tempo de deslocamento otimizado estimado | 193,80 minutos |
| Redução estimada de tempo | 23,6 minutos |

**Metodologia de comparação:** foram consideradas as mesmas 21 posições geográficas, com saída e retorno simulados ao Polo Regional do IPEM-SP. As distâncias e os tempos foram calculados utilizando o OSRM, e a sequência otimizada foi obtida pelo OR-Tools.

As fiscalizações repetidas em uma mesma posição geográfica foram consolidadas para o cálculo dos deslocamentos, mantendo-se separada sua contabilização como atividades registradas.

**Os resultados indicam potencial de melhoria no cenário simulado, não uma redução comprovada da operação histórica.**

#### 3. Validação funcional

- Consulta às rotas históricas: validada.
- Marcadores numerados: validados na rota piloto.
- Seleção de estabelecimentos: validada.
- Otimização de rotas com OR-Tools: validada.
- Visualização dos trajetos viários: validada.
- Publicação e testes de acesso por usuários externos: sujeitos à confirmação após disponibilização.

**Número de usuários que testaram o MVP:** a registrar.

**Feedback qualitativo:** a consolidar a partir dos testes com integrantes do projeto e usuários convidados.

---

### 🛠️ Tecnologias Utilizadas

| Tecnologia | Aplicação |
|---|---|
| Python | Desenvolvimento do sistema e processamento dos dados |
| Pandas e NumPy | Tratamento, estruturação e análise de dados |
| Streamlit | Interface web interativa |
| Folium | Mapas e visualização geográfica |
| OpenStreetMap | Base cartográfica |
| OSRM | Cálculo de rotas, distâncias e tempos estimados pela malha viária |
| Google OR-Tools | Otimização matemática da sequência de visitas |
| Google Colab | Desenvolvimento e validação do protótipo |
| GitHub | Versionamento, documentação e organização das entregas |

---

### 🔬 Metodologia de Desenvolvimento

O desenvolvimento da Sprint 2 foi organizado nas seguintes etapas:

**Etapa 1 — Preparação dos dados:** identificação dos agrupamentos históricos, tratamento dos estabelecimentos e estruturação dos registros.

**Etapa 2 — Geolocalização:** associação de coordenadas aos estabelecimentos da rota piloto, tratamento de pontos repetidos e identificação de localizações pendentes.

**Etapa 3 — Matriz de distâncias:** utilização inicial da fórmula de Haversine para testes matemáticos e posterior implementação de matrizes viárias com OSRM.

**Etapa 4 — Otimização:** aplicação do OR-Tools para propor sequências de fiscalização com menores custos de deslocamento.

**Etapa 5 — Comparação:** análise das distâncias e dos tempos estimados entre sequências históricas consolidadas e otimizadas, sob condições equivalentes.

**Etapa 6 — Aplicação web:** integração dos indicadores, consultas, mapas e funcionalidades de planejamento em uma interface Streamlit.

---

### 🚀 Próximos Passos — Sprint 03

A terceira sprint terá como foco ampliar a abrangência e a robustez operacional da solução.

Principais atividades previstas:

1. **Ampliar a geocodificação dos estabelecimentos**, incorporando mecanismos automatizados de consulta, validação e armazenamento de coordenadas.

2. **Expandir a otimização para outras rotas históricas**, conforme a disponibilidade e a qualidade dos dados geográficos.

3. **Permitir o cadastramento de novos endereços**, sem limitar o planejamento aos estabelecimentos presentes na base de 2018.

4. **Incorporar restrições operacionais**, como jornada disponível, tempo de atendimento, capacidade das equipes e condições específicas de fiscalização.

5. **Avaliar a distribuição territorial das equipes**, considerando agrupamentos regionais e oportunidades de aumentar a cobertura das fiscalizações.

6. **Validar a solução com usuários**, utilizando feedback dos integrantes do projeto e, quando possível, dos profissionais do IPEM-SP.

7. **Aprimorar os indicadores de desempenho**, diferenciando distâncias percorridas, tempo de deslocamento, tempo de atendimento e produtividade operacional.

---

### 📂 Anexos / Evidências

Recomenda-se manter as evidências organizadas na pasta `Docs`, com registros das seguintes funcionalidades:

- Dashboard gerencial das rotas históricas.
- Consulta às 800 rotas cadastradas.
- Visualização dos estabelecimentos e marcadores numerados.
- Planejamento interativo com seleção de destinos.
- Comparação entre rota histórica e rota otimizada.
- Indicadores de distância e tempo estimado de deslocamento.

**Repositório do projeto:**  
https://github.com/Herms-Corp/otimizacao_das_rotas_ipem-sp

**Aplicação web demonstrativa:**  
Inserir endereço após a publicação.

#### Observações sobre os dados

O projeto utiliza dados históricos de 2018 para desenvolvimento e estudo da metodologia.

Para demonstrações públicas, foi preparada uma versão com dados fictícios, evitando a publicação indiscriminada de informações pessoais e identificadores internos.

A aplicação é um **protótipo acadêmico em desenvolvimento** e não representa uma ferramenta operacional oficialmente implantada pelo IPEM-SP.

<img width="1848" height="875" alt="image" src="https://github.com/user-attachments/assets/75cd9829-6a4a-4f70-a9fc-baa0ca014840" />
<img width="1832" height="773" alt="image" src="https://github.com/user-attachments/assets/cb9d21ef-1aed-4e66-b492-c5edebcbc273" />
<img width="1815" height="817" alt="image" src="https://github.com/user-attachments/assets/ff6ccebe-c03e-40bd-ab8a-13880e56fdfa" />
<img width="1808" height="782" alt="image" src="https://github.com/user-attachments/assets/55f373bb-76a1-405e-93ca-87af74f9a0c5" />
<img width="1802" height="823" alt="image" src="https://github.com/user-attachments/assets/387187a7-10f4-4495-a65a-847174ebe1f9" />
![Uploading image.png…]()
