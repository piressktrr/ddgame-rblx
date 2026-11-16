# Design: Bouncer (pistola mágica) e Lâmina mágica

> Rascunho de design para as Fases 3 do [IMPLEMENTATION_PLAN](../../05-arquitetura/IMPLEMENTATION_PLAN.md).
> Base: ADRs 0017, 0019, 0024 e requisitos RF-30..33, RF-40..41.
> Nada aqui é decisão final: os pontos marcados **[decidir]** precisam do dono.

## 1. Controles (PC, ADR 0009)

| Ação | Proposta | Motivo |
|---|---|---|
| Gancho | Segurar **botão esquerdo** | Já definido (ADR 0016) |
| Bouncer (atirar) | **Botão direito** | Mira já está no mouse; dá para combinar com o gancho |
| Lâmina (empurrão) | **E** (ou **F**) | Mão esquerda livre, o mouse continua mirando |

**[decidir]** teclas finais.

## 2. Bouncer — pistola mágica de impulso

### Sensação desejada
"Pulo de foguete" mágico: atirar para baixo te joga para cima, atirar para trás te lança para
frente. Cada tiro é um **estouro** curto, não um voo contínuo.

### Regras (ADR 0017/0024)
- Aparece num **pedestal** (`BouncerPickup`); tocar = pega. Some ao **sair da `BouncerZone`** ou morrer.
- Munição: **3 cargas**; cada carga volta em **1,2 s** (valores em `Config.Bouncer`).
- Tiro empurra o atirador na direção **oposta** à mira, força ~**60** (impulso) e zera a velocidade
  vertical negativa antes (para o tiro para baixo funcionar mesmo caindo).
- Projétil: orbe rápido (~150 studs/s), alcance 40. Se acertar outro jogador: empurrão **pequeno** (~15).
- Congelado não atira (RF-20).

### Implementação
- **Cliente (`BouncerController`)**: lê a mira no plano (`Logic/Aim`), aplica o impulso no próprio
  `HumanoidRootPart` na hora (sem lag), toca efeito e avisa o servidor.
- **Servidor (`BouncerService`)**: dono da munição; recusa tiro sem carga (rate limit). Calcula se o
  orbe acertou alguém (raycast) e, via `InteractionPolicy`, manda o cliente da vítima aplicar o empurrão.
- O modelo é um `Tool`? **Não**: a mochila padrão do Roblox atrapalha. O modelo é **soldado à mão**
  do personagem pelo código enquanto o jogador está na zona (`Motor6D`/`WeldConstraint` em `RightHand`).

## 3. Lâmina mágica — empurrão

### Sensação desejada
Golpe rápido e curto, tipo "tapa de energia": empurra e **descongela** quem acerta (ADR 0024).
Sempre disponível, sem pegar em lugar nenhum.

### Regras
- Alcance curto: caixa de ~6 × 6 studs à frente do jogador, no plano.
- Cooldown **0,6 s**. Empurrão ~**45** na direção do golpe (+ um pouco para cima).
- Sem dano. Pode empurrar e descongelar qualquer jogador (`InteractionPolicy`).
- Congelado não golpeia.

### Implementação
- **Cliente (`BladeController`)**: anima o golpe (arco de luz por 0,15 s) e pede ao servidor.
- **Servidor (`InteractionService`)**: `GetPartBoundsInBox` na frente do atacante, valida cooldown,
  descongela os atingidos e manda o cliente de cada vítima aplicar o empurrão.
- A lâmina aparece na mão **só durante o golpe** (some depois), para não poluir o visual.

## 4. Visual (greybox agora, tema depois)

| Peça | Greybox (feito com Parts) | Versão final (depois) |
|---|---|---|
| Bouncer | Corpo de latão, cano curto e largo, anel de runa e **cristal magenta** brilhante | Malha de pistola rúnica |
| Lâmina | Cabo escuro + lâmina curta translúcida **branco-azulada** (Neon) | Malha + trilha de partículas |
| Pedestal do Bouncer | Pedestal com o Bouncer flutuando | Altar rúnico |

**Cor do Bouncer:** magenta não conflita com nenhuma cor do mapa (vermelho = morte, verde = gancho 1x,
roxo = não-grudável, laranja = descongelar, azul = gelo, dourado = checkpoint). **[decidir]**

Os modelos greybox ficam em `ServerStorage.Prefabs.Tools` no place: `Bouncer`, `MagicBlade`,
`BouncerPedestal`.

## 5. Ferramentas para modelos melhores

Dá para fazer **greybox e protótipo só com Parts** (o que existe hoje). Para modelos de verdade:

| Opção | O que é | Precisa integrar? |
|---|---|---|
| **Geração de malha do Studio (via MCP)** | O MCP do Studio tem `generate_mesh` / `generate_procedural_model` (IA da própria Roblox) | Não: já está disponível; só testar a qualidade |
| **Blender** + exportar `.fbx` → importar no Studio | Modelagem completa e gratuita | Instalar o Blender; para eu controlar, um **MCP do Blender** (ex.: `blender-mcp`) |
| **Toolbox / Creator Store** | Modelos prontos de terceiros | Não, mas cuidado com licença e originalidade (ADR 0001) |

Recomendação: greybox com Parts agora; quando o tema for aplicado, testar a geração de malha do
Studio e, se não ficar bom, instalar Blender + `blender-mcp`.

## 6. Questões para o dono

1. Teclas: Bouncer no botão direito e lâmina no **E**?
2. Cor do Bouncer: magenta?
3. Valores iniciais ok? (3 cargas, 1,2 s de recarga; lâmina com 0,6 s de cooldown)
