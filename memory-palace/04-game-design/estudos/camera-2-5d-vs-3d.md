# Câmera: 2.5D ou 3D? (análise de 2026-11-15)

> Contexto: foco do dono em **monetização e alcance** (muitos jogadores), progressão por atributo estilo
> "+1 Speed" (ADR 0030), mapa em 6 estágios lineares (ADR 0029). A decisão atual é 2.5D (ADR 0011).

## 1. Comparação

| Critério | 2.5D lateral (atual) | 3D em 3ª pessoa |
|---|---|---|
| **Cara de "jogo do Roblox"** | Rara na plataforma; parece jogo de nicho | É o padrão de quase todos os jogos no topo das paradas |
| **Miniatura e primeiro minuto** | Diferente, mas pode afastar quem procura "o de sempre" | Familiar: o jogador já sabe jogar ao entrar |
| **Combina com "+1 Speed"** | Velocidade alta num plano vira precisão difícil | Correr cada vez mais rápido numa pista longa é exatamente o que esses jogos vendem |
| **Mira do gancho** | Simples: mouse no plano | Mais difícil; precisa de mira no centro da tela + ajuda de mira (prender no ponto mais próximo da mira) |
| **Puxar/atrapalhar outros jogadores** | Fácil de ver quem está onde | Mais caótico (bom para vídeos/clipes), mas mais difícil de ler |
| **Custo de fazer mapa** | Exige medidas precisas em cada pulo (o que estamos sofrendo) | Pista linear larga com prefabs por estágio é mais tolerante e mais rápida de montar |
| **Atalhos dentro do estágio** | Só em cima/embaixo | Esquerda, direita, cima, baixo: mais espaço para atalhos pequenos |
| **Celular (futuro)** | Melhor | Padrão do Roblox, já resolvido pelos controles nativos |
| **Diferencial do jogo** | A câmera é o diferencial | O diferencial passa a ser o **gancho que puxa os dois** + Bouncer + caos |
| **O que já fizemos** | Câmera e trava no plano prontas; mapa 01 greybox | Câmera: quase nada a fazer (é a padrão). Mapa 01 seria refeito |

## 2. Opção do meio: "3D sobre trilhos"

Câmera 3D em 3ª pessoa (a padrão do Roblox, com *shift lock*), mas **cada estágio é uma pista larga que
sempre avança para frente**, como nos jogos "+1 Speed … Escape". A pista tem a legibilidade de um jogo
lateral (o caminho é óbvio) com a cara e a liberdade de um jogo 3D. Os padrões do estudo de referência
continuam valendo, só que em 3D: corredor de balanço, rampas, serpentina, labirinto, campo flutuante e
poço.

## 3. Recomendação

**Mudar para 3D, no formato "3D sobre trilhos".** Motivos, em ordem de peso:

1. **Alcance:** o objetivo é muitos jogadores, e todos os jogos de referência (lineares e de monetização)
   são 3D. A 2.5D é um risco de nicho que não ajuda a meta.
2. **Combina com a progressão escolhida:** velocidade crescente funciona melhor em pista 3D longa.
3. **Mapa mais rápido de fazer:** pista larga em prefabs tolera erro de medida; a 2.5D pede precisão de
   pixel em cada pulo.
4. **Custo baixo de trocar agora:** só temos um greybox e uma câmera simples. Daqui a duas fases ficaria caro.

O que piora: a mira do gancho fica mais difícil e precisa de **ajuda de mira** desde o início (requisito
novo). E perdemos a câmera como diferencial; o diferencial passa a ser a mecânica.

## 4. Se aprovado, o que muda

- Novo ADR substituindo o 0011. `CameraController` e `CharacterController` (trava de plano) saem; volta
  a câmera padrão do Roblox com *shift lock*.
- Mapa 01 refeito como pista 3D de 6 estágios (o `layout.json` passa a ter profundidade Z).
- Requisitos RF-01..03 e RF-10 reescritos (mira 3D com ajuda de mira).
