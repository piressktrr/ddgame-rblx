# Game Design Document — Race and Escape (v0.4)

> Jogo original no gênero de corrida cooperativa. Nada de arte, nomes ou mapas copiados.
> Visão simples: [README](../../README.md). Decisões numeradas: [02-decisoes/](../02-decisoes/README.md).

## 1. Pitch

Plataforma de **fantasia em 2.5D** num servidor aberto. Cada mapa é um percurso visto de lado,
que o dono vai reformular (Q31). Os jogadores usam um **gancho mágico** para se puxar
uns aos outros, desviam de **gelo mágico** e usam o **Bouncer**, uma pistola mágica de impulso, em
trechos especiais. Qualquer um pode **salvar ou atrapalhar** qualquer outro.

**Tema:** fantasia (ruínas flutuantes, florestas mágicas, cavernas de cristal, torres de magos).

**Pilares (toda decisão de design deve servir a pelo menos um):**

1. **Caos social divertido:** puxar estranhos, salvar alguém no último segundo ou atrapalhar de
   brincadeira. Jogar junto é mais rápido, mas sozinho sempre dá.
2. **Movimento com skill:** gancho, Bouncer e lâmina têm teto de habilidade alto (momentum, timing).
3. **Ritmo rápido:** nada de ficar esperando. Congelar é um relógio de 15 s, não uma espera parada.
4. **Conquista que se sente:** checkpoints espaçados (a cada 3 estágios, ADR 0034) tornam cada um uma vitória.
5. **Legibilidade:** a cor de uma superfície diz o que ela faz (§6).

## 2. Core loop

```
Entra no mapa → corre entre checkpoints (sozinho ou ajudando/atrapalhando outros)
   → descobre rotas e atalhos → chega ao fim → tempo pessoal no ranking → tenta de novo mais rápido
```

## 3. Mecânicas

| Mecânica | Como funciona | Decisão |
|---|---|---|
| **Gancho** | Ver §3.3. Mira com o mouse no plano; um **clique** puxa o personagem direto ao alvo; **segurar** o botão o deixa preso no ponto. Gruda em qualquer peça do plano, exceto **roxas**; em **verde**, uma vez por jogador (volta ao morrer ou passar de checkpoint). Em outro jogador, **puxa os dois** (só depois do mapa aprovado). | 0003, 0016, 0036, 0037, 0039, 0042 |
| **Gelo** | Tocar no gelo congela por **15 s**: não anda nem usa ferramentas, mas pode ser puxado/empurrado. Se chegar a uma zona de descongelar, volta ao normal. Se o tempo acabar, **morre**. | 0014 |
| **Descongelar** | Zona **laranja-brasa** que tira o congelamento na hora. Fica perto do gelo para que outro jogador possa salvar. | 0014, 0021 |
| **Zona mortal** | Vermelha. Mata na hora → volta ao último checkpoint. O gancho gruda nela. | 0015, 0021 |
| **Bouncer** | Pistola mágica pega num ponto do mapa e usada num trecho. Cada tiro empurra o próprio jogador para o lado oposto da mira; empurra **um pouco** quem for atingido. Munição que recarrega sozinha. Some ao sair do trecho. | 0017, 0024 |
| **Lâmina mágica** | É o empurrão: golpe corpo a corpo que empurra e **descongela** quem acerta. Sem dano. | 0019, 0024 |
| **Checkpoints** | **Por jogador**. Um a cada 3 estágios. A corrida completa tem meta de 10 a 15 min. | 0018, 0034, 0040 |
| **Objetos mágicos (solo)** | Ajudam quem está sozinho no lugar de um parceiro (§3.2). | 0004, 0020 |

### 3.1 Interação entre jogadores (MVP: sem Bond)

- Todos interagem com todos: gancho, Bouncer e lâmina afetam qualquer jogador (ADR 0013).
- Não existe equipe no sistema. "Grupo" é só quem combina de se ajudar.
- Tempo, checkpoint e ranking são **pessoais**, mesmo jogando junto.
- **Depois do MVP** o Bond volta como formação de grupo, **sem proteção**: grupos diferentes
  continuam podendo se atrapalhar (ADR 0023).
- Risco de troll aceito nos testes. Toda regra de "posso afetar esse jogador?" fica num único
  módulo (`InteractionPolicy`), para religar alguma proteção no futuro.

### 3.3 Gancho em detalhe

- **Tipo:** puxão direto ao alvo (ADR 0042, substitui o balanço do ADR 0036). Um clique prende e puxa em linha reta,
  com aceleração suave, a ~58 studs/s; ao chegar, solta com parte do embalo. Segurando o botão, fica preso no ponto.
- **Mira:** cursor no plano; se o raio não acerta, uma esfera de ajuda (raio inicial 3 studs, `Config.Hook.AimAssistRadius`) pega o alvo "quase na mira". Alcance inicial 40 studs, contado do centro do personagem.
- **Uso:** funciona no ar e em sequência; clicar em outro alvo durante o voo troca de alvo. Bater numa parede no caminho solta.
- **Voo:** pose de voo durante o puxão (braço para o alvo, corpo inclinado); ao pousar com embalo, desliza e freia.
- **Superfícies:** só peças na profundidade do plano de jogo (ADR 0039).
- **Em outro jogador:** o servidor valida e cada cliente se puxa em direção ao outro (caminho A). O caminho C (dar ao atacante a física do alvo) é o plano B (ADR 0037).
- **Evolução:** alcance e raio da esfera crescem com o nível do gancho (§7).

### 3.2 Jogo solo com objetos mágicos

O mesmo mapa serve para quem está sozinho e para quem está em grupo. Quem está sozinho conta com
objetos que fazem o papel do colega (ADR 0026):

| Situação de coop | Objeto mágico | Como ajuda |
|---|---|---|
| Elevar o parceiro | **Pedra-âncora** | Ponto que puxa o jogador para cima com mais força. |
| Lançar o parceiro | **Orbe de impulso** | Enganchado, arremessa o jogador na direção marcada. |
| Salvar do gelo | **Cristal de degelo** | Atingido pelo gancho, descongela (funciona mesmo congelado; alcance curto). |
| Segurar botão | **Totem de peso** | Bloco que o jogador arrasta com o gancho até o botão. |

No MVP (solo primeiro, ADR 0023) os objetos ficam **sempre ativos para todos**. Com o Bond, passam a
aparecer só para quem não está em grupo.

## 4. Estrutura de mundo (MVP)

- MVP: **um** mapa 2.5D, jogável sozinho e em grupo (ADR 0022); estrutura a ser reformulada pelo dono (Q31). Sem hub elaborado.
- Meta de duração: **10 a 15 minutos** por corrida completa; checkpoint a cada 3 estágios (ADR 0034, 0040).
- Depois do MVP: hub, tutorial, mapas por dificuldade.

## 5. Princípios de design de fases

1. **Ensinar → Testar → Torcer.** Cada mecânica aparece primeiro num lugar seguro, depois sob
   pressão e depois combinada com outra.
2. **Os primeiros 60 segundos decidem a retenção.** Enganchar algo nos primeiros 10 s.
3. **Tensão e alívio** em "dentes de serra". Com checkpoints espaçados, cada trecho precisa ter
   pequenas vitórias no meio (atalhos, vistas, rotas descobertas) para a morte não frustrar.
4. **Várias rotas:** toda seção tem pelo menos uma rota segura e uma rápida/arriscada. Bouncer e
   superfícies verdes são ótimas chaves de atalho.
5. **Gelo sempre com resgate possível:** descongelar ao alcance de um gancho ou empurrão.
6. **Linhas de condução:** luz, cor e geometria apontam o caminho.
7. **Falha visível e justa:** hitboxes do tamanho do visual.
8. **PC primeiro** (ADR 0009): timings pensados para teclado e mouse.
9. **Orçamento de tamanho:** prefabs reutilizáveis.

### 5.1 Processo de produção de um mapa

1. **Papel:** seções, rotas e mecânica central de cada uma.
2. **Greybox** só com blocos nas cores da §6.
3. **Playtest** sozinho e em grupo: tempo por seção, onde as pessoas morrem.
4. **Iterar.** Arte e iluminação só depois do layout aprovado.

### 5.2 Câmera: 2.5D lateral (ADR 0011)

Todo o jogo acontece num plano (Z = 0); a profundidade é só visual (ADR 0038, 0039).

- Câmera lateral com **altura visível fixa**; telas largas veem mais nas laterais.
- A/D andam, Espaço pula; W/S não tiram do plano e não mexem no gancho.
- Jogadores **colidem** entre si. Desvio de Z é corrigido no cliente e no servidor.
- Estágios podem ter trechos verticais, não só avanço para a direita.

## 6. Linguagem visual

| Elemento | Cor | Tag (CollectionService) |
|---|---|---|
| Superfície comum (gancho gruda) | Neutra (pedra, madeira, cristal) | (padrão) |
| Não-grudável | **Roxo** | `NoHook` |
| Gruda uma vez por jogador | Verde | `HookOnce` |
| Congela | Azul-gelo | `FreezeZone` |
| Descongelar | **Laranja-brasa** `#FF8A1F` ([referência](referencias/cores-descongelar.html)) | `UnfreezeZone` |
| Mortal | Vermelho | `KillZone` |
| Checkpoint | Dourado | `Checkpoint` |
| Ponto do Bouncer | A definir | `BouncerPickup` / `BouncerZone` |
| Início / Fim | Arcos com placa | `RaceStart` / `RaceFinish` |

Além da cor, cada zona tem **forma** própria (cristais no gelo, chamas/runas no descongelar etc.)
para ajudar daltônicos.

## 7. Progressão e monetização

**No MVP (ADR 0030, 0033, 0040):** o jogador ganha **níveis do gancho** jogando (alcance e raio da esfera de
ajuda). Regra de ganho: Q23; persistência entre sessões: Q41. Velocidade como atributo fica para depois.

**Depois do MVP (ADR 0025), e a monetização é essencial:**

- XP e moedas por mapa concluído; bônus por recorde pessoal.
- Cosméticos (trilha, skin do gancho/Bouncer/lâmina, efeito de gelo).
- **Boosts e perks com vantagem são permitidos** (ex.: congelar por menos tempo, mais munição no
  Bouncer). Os valores do Config são o padrão sem boost; perks aplicam modificadores por jogador.
- Rankings por mapa, pessoais. A definir: separar ou não quem usou boost.

## 8. Escopo do MVP

Gancho (com nível), gelo/descongelar, zona mortal, checkpoints por jogador, timer pessoal, Bouncer,
lâmina, objetos mágicos do solo, tutorial do gancho (ADR 0041), um mapa 2.5D. Fora do MVP: Bond, rebirth, hub, loja,
boosts, salvar recordes entre sessões. Ordem de construção: ver o plano de implementação (ADR 0040).
