# Referências de mapa (estudo, não cópia)

> Estudo de 2026-11-15. Fonte 1: capturas em `memory-palace/04-game-design/referencias/imagens/` de um mapa famoso do gênero (vista do editor).
> Fonte 2: jogos do Roblox populares com progressão linear. Regra do projeto (ADR 0001): **não copiamos
> layout, nomes ou arte**. Daqui saem só **padrões de design** (tipos de trecho, ritmo, estrutura), que
> viram trechos desenhados do zero no nosso mapa.

## 1. O que o mapa de referência faz (padrões observados nas capturas)

| # | Padrão | Como aparece | Para que serve |
|---|---|---|---|
| P1 | **Sala de início com regras** | Sala com ponto de nascimento e placas ("seja educado, não bloqueie os outros") | Primeiro contato; sem perigo |
| P2 | **Corredor de aquecimento com pilares** | Pilares altos, plataformas alternadas, faixas de gelo no chão entre elas | Ensinar gancho + gelo sem risco de morte |
| P3 | **Corredor de balanço** | Tubo longo com pontos de gancho alternando teto/chão | Ritmo: engancha, balança, solta, repete |
| P4 | **Rampas em V** | Túnel que desce e sobe | Ganhar velocidade e "voar" no fim |
| P5 | **Escadaria serpentina** | Andares horizontais empilhados, descendo em zigue-zague, com blocos não-grudáveis na ponta | Forçar a soltar o gancho no lugar certo |
| P6 | **Labirinto apertado** | Corredores estreitos de 1 bloco | Mudança de ritmo; precisão, não velocidade |
| P7 | **Campo de blocos flutuantes** | Grade de bloquinhos soltos numa sala grande | Liberdade: cada um faz sua rota com o gancho |
| P8 | **Poço vertical / corredor em S** | Subidas longas, curvas fechadas | Teste de controle do gancho em espaço curto |
| P9 | **Linhas de morte** | Faixas vermelhas em rampas e chão | Punição clara e visível |
| P10 | **Marcos centrais (sóis)** | Um grande marco brilhante no meio de cada região, trechos em volta | Orientação: "estou na região X"; checkpoint |
| P11 | **Teia, não linha** | O mapa é enorme e ramificado, regiões ligadas por salas centrais | Rejogabilidade, mas fácil se perder |

**O que não serve para o Roblox:** o tamanho (horas de jogo), a teia sem direção clara (P11) e a
dependência de dupla em quase tudo. Isso conflita com "solo primeiro" (ADR 0023) e com sessões curtas.

## 2. Jogos do Roblox com progressão linear (como os mapas deles funcionam)

| Jogo | Estrutura do mapa | O que aprender |
|---|---|---|
| **+1 Speed Keyboard Escape** (e variações "+1 Speed … Escape") | Pista linear dividida em **estágios** numerados; cada estágio é um tema/obstáculo (paredes que fecham, labirinto fixo no estágio 12). Placas amarelas de vitória no fim. Esteiras e *rebirth* para ganhar velocidade. Mundos novos reaproveitam a fórmula. | Estágios curtos e numerados = progresso visível; recompensa no fim de cada um; um labirinto fixo como "estágio especial" |
| **Escape Tsunami for Brainrots** | Faixa longa em **zonas** por distância (ex.: 225 m, 275 m), com **zonas seguras**; tudo aberto, o limite é o seu atributo de velocidade; uma torre depois da última zona. | Distância como placar; zonas seguras = checkpoints que dão alívio; meta grande visível no fim |
| **Tower of Hell** *(conhecimento geral, não confirmado nesta pesquisa)* | Torre vertical montada com **seções sorteadas** empilhadas; sem checkpoints; cronômetro do servidor. | Seções curtas e intercambiáveis; altura como progresso; cronômetro gera urgência |
| **Doors** | Sequência linear de **salas numeradas** sorteadas de um conjunto de *prefabs* (corredor, sala especial, bifurcação), cada uma com entrada e saída fixas; andares/subandares. | Número da sala = progresso; prefabs com encaixe padrão facilitam fazer muitos trechos |
| **Steal An Egg / Brookhaven / Blox Fruits** (topo das paradas em nov/2026) | Não são lineares. | Mostram o que domina hoje: coletar, ter coisas e jogar com amigos. Vale para monetização, não para o mapa |

## 3. Síntese: como seria o nosso mapa (proposta para discutir)

Uma **pista linear em estágios**, com rotas alternativas **dentro** de cada estágio (ADR 0012), usando
os padrões P1–P10 recriados do nosso jeito:

```
[Saguão] → Est.1 Aquecimento (P2) → Est.2 Corredor de balanço (P3) → ☀ Marco/Checkpoint
        → Est.3 Rampas (P4) → Est.4 Serpentina (P5) → ☀
        → Est.5 Labirinto (P6) ou Campo flutuante (P7)  ← escolha de rota
        → Est.6 Poço final (P8) → ☀ Fim + placar
```

- Cada estágio é um **prefab** com entrada e saída padrão (como em Doors). Assim dá para reordenar,
  sortear depois e montar mapas novos rápido.
- Número do estágio e barra de progresso sempre visíveis (como +1 Speed / Doors).
- Marco grande e visível de longe em cada checkpoint (P10), a cada ~3 min (ADR 0018).
- Estágio 1 fica no tamanho do nosso greybox atual.
