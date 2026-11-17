# Gancho: o que é necessário para fazer (estudo de 2026-11-16)

> **Atualização (ADR 0042):** o protótipo começou com o balanço (B), mas o dono trocou para o
> **puxão direto (A)**: um clique vai ao alvo, segurar fica preso, sem W/S. O resto deste estudo fica como histórico.

> Contexto: o gancho é a habilidade central e o que o jogador evolui (ADR 0033), em câmera 2.5D
> lateral (ADR 0011, 0038). Regras já decididas: ADR 0003 (em jogador, puxa os dois) e ADR 0016 (gruda em tudo menos
> roxo `NoHook`; verde `HookOnce` uma vez por jogador; segurar o botão = preso).
> Fontes: fóruns de desenvolvedores do Roblox (links no fim) + conhecimento geral da engine.
> O que veio de fórum é opinião da comunidade, não medição nossa: tudo aqui precisa de protótipo.

## 1. As peças do gancho

| # | Peça | O que faz | Onde roda |
|---|---|---|---|
| 1 | **Entrada** | Botão do mouse pressionado/solto vira "disparar" / "soltar" | Cliente |
| 2 | **Mira com ajuda** | Acha o ponto onde o gancho vai prender, a partir do cursor no plano | Cliente |
| 3 | **Validação de superfície** | Recusa roxo (`NoHook`), controla o uso do verde (`HookOnce`), confere alcance | Cliente decide na hora; servidor confirma |
| 4 | **Física do puxão/balanço** | Move o personagem enquanto está preso | Cliente (dono da física do próprio personagem) |
| 5 | **Corda visível** | Desenha a corda para o jogador e para os outros | Todos os clientes |
| 6 | **Rede** | Avisa o servidor (prendeu/soltou); servidor repassa e valida | Servidor |
| 7 | **Gancho em outro jogador** | Puxa os dois, um em direção ao outro | Servidor + os dois clientes |
| 8 | **Retorno ao jogador** | Mira na tela, som, corda esticando, erro visível ao acertar roxo | Cliente |
| 9 | **Evolução** | Atributos do gancho que crescem (alcance, força, recarga) | Servidor guarda; Config define |

## 2. Decisão que muda tudo: que tipo de gancho é?

O ADR 0016 diz "segurar = preso", mas não diz **o que acontece enquanto está preso**. Há três
comportamentos, e cada um dá um jogo diferente:

| Tipo | Como se comporta | Sensação | Dificuldade de fazer |
|---|---|---|---|
| **A. Puxão** | O personagem é puxado em linha reta até o ponto | Simples, rápido, fácil de entender | Baixa |
| **B. Balanço (pêndulo)** | A corda tem comprimento fixo; o personagem balança e ganha impulso ao soltar | Mais habilidade, mais "uau" | Média |
| **C. Misto** | Balança como pêndulo e a corda vai encurtando (ou o jogador recolhe com uma tecla) | Mais expressivo e mais difícil de dominar | Média/alta |

O gênero de referência usa o **C** (a corda puxa com força e o personagem balança). Para o Roblox,
o mais comum e mais legível é começar pelo **B com um puxão leve**, e ajustar.

## 3. Como fazer a física (opções)

1. **RopeConstraint + força extra.** Um `Attachment` no ponto atingido, outro no personagem, e uma
   `RopeConstraint` entre eles: a engine resolve o pêndulo sozinha. Uma `VectorForce` ou
   `LinearVelocity` no cliente dá o empurrão para balançar/dirigir. É o padrão mais citado nos fóruns.
   - A favor: pouco código, balanço físico de verdade, encurtar a corda é só mudar `Length`
     (há também o modo guincho da própria corda).
   - Contra: relatos de personagem **atravessando paredes** quando o comprimento é forçado de uma
     vez (encurtar aos poucos, por tempo); precisa **limitar a velocidade** para não disparar.
2. **Força calculada por nós a cada quadro** (sem constraint): calcula-se a direção até o ponto e
   aplica-se força/velocidade. Controle total da sensação, mais código e mais ajuste fino.
3. **AlignPosition / LinearVelocity direto ao ponto**: serve para o tipo A (puxão), não balança.

Ponto de atenção comum às três: o `Humanoid` "briga" com forças externas (freia no ar, tenta ficar
em pé). Enquanto está preso, é normal trocar o estado do Humanoid (ex.: `Physics`) ou desligar parte
do controle, e devolver ao soltar. `PlatformStand` é citado como instável para isso.

**Risco 2.5D:** o personagem está preso ao plano Z = 0 (trava no `CharacterController`); o balanço da
corda precisa funcionar sem que a trava "brigue" com a física. É o primeiro ponto a testar no protótipo.

**Recomendação:** protótipo com a opção 1 (RopeConstraint + VectorForce), porque testa o balanço
em um dia; se a sensação não ficar boa, migrar para a 2 reaproveitando mira, rede e corda.

## 4. Mira no plano 2.5D com ajuda

O jogador mira com o **cursor do mouse**; todo o jogo está no plano Z = 0. Passos:

1. Converter o cursor num ponto do plano (raio da câmera cruzando Z = 0) e traçar o raio do
   personagem até esse ponto, limitado a `alcance`.
2. Se o raio não acertar nada grudável, uma **esfera lançada** (`Spherecast`) no mesmo caminho pega
   alvos "quase na mira" (ADR 0036). Quanto maior o raio da esfera, mais fácil.
3. Só valem peças que ocupam o plano do jogo (cenário de fundo não é grudável; ver Q34).
4. Mostrar o cursor em três estados: sem alvo, alvo válido, alvo proibido (roxo / verde já usado).

O raio da ajuda de mira é um ótimo **atributo para evoluir** e para vender como vantagem.

## 5. Rede: quem manda em quê

- O personagem é simulado pelo **cliente do próprio jogador** (é o dono da física dele). Por isso o
  gancho em superfície é 100% local: resposta imediata, sem atraso.
- O servidor **não confia**: recebe "prendi em tal ponto" e confere alcance, linha de visão, tag da
  superfície e intervalo entre disparos. Guarda o uso do verde por jogador (zera ao morrer/checkpoint).
- Para os **outros jogadores** verem a corda, o servidor repassa "fulano prendeu em X / soltou" e
  cada cliente desenha a corda (um `Beam` entre dois `Attachment`).

### Gancho em outro jogador (a parte difícil)

Um cliente **não pode** aplicar força no personagem de outro. Caminhos:

| Caminho | Como | Risco |
|---|---|---|
| **A. Cada cliente se puxa** | Servidor valida e manda aos dois clientes "puxe-se em direção ao outro" | Atraso de rede visível (os dois reagem com ping de diferença); é o mais seguro |
| **B. Servidor assume a física** | Tira a posse da física dos personagens durante o puxão | Controle trava/engasga para o jogador puxado |
| **C. Dar a posse ao atacante** | O atacante simula o outro | Rápido, mas abre porta para trapaça (jogar o outro longe) |

Nossa arquitetura já escolheu o **A**. É o maior risco técnico do jogo e precisa de teste com 2
clientes e latência simulada antes de fecharmos o desenho.

## 6. O que evolui no gancho (para a Q23)

Candidatos, todos valores do `Config.Hook` que viram atributos por jogador:

| Atributo | Efeito | Impacto no mapa |
|---|---|---|
| Alcance | Prende mais longe | **Alto**: abre atalhos; os vãos do mapa dependem dele |
| Força do puxão / velocidade de recolher | Chega mais rápido | Médio |
| Recarga | Dispara de novo mais cedo | Médio |
| Raio da ajuda de mira | Mais fácil acertar | Baixo (não muda o mapa) |
| Usos do verde | Mais de um uso em superfície verde | Alto |

Cuidado: alcance e usos do verde mudam o que é possível no mapa. O mapa precisa ser feito para o
gancho **básico**; os níveis mais altos só abrem atalhos, nunca o caminho principal.

## 7. Ordem de construção sugerida

1. Pista de teste: parede grudável, teto, pilar, peça roxa, peça verde, vãos de 20/30/40 studs.
2. Mira com ajuda + cursor (sem física ainda): imprimir onde prenderia.
3. Física solo (opção 1, com o personagem preso ao plano) + corda local + limites de velocidade. **Aqui se decide o tipo A/B/C jogando.**
4. Regras: `NoHook`, `HookOnce`, alcance, recarga, soltar ao morrer/congelar.
5. Rede: validação no servidor + corda para os outros.
6. Gancho em jogador (com 2 clientes e latência).
7. Atributos de evolução.

## 8. Perguntas para o dono

> Respondidas em 2026-11-16: ver ADR 0036 e 0037.

1. Tipo de gancho: **A** puxão, **B** balanço ou **C** misto? (ou: faço o protótipo com os três numa tecla para comparar)
2. Enquanto preso, o jogador pode **recolher/soltar corda** (teclas) ou é automático?
3. O gancho funciona **no ar** e **em sequência** (soltar e prender de novo sem tocar o chão)?
4. Alcance inicial: os 40 studs do Config servem como ponto de partida?
5. Botão: mouse esquerdo segura o gancho? (o direito gira a câmera no Roblox)
6. O gancho em jogador entra já no primeiro protótipo ou só depois do solo aprovado?

## Fontes

- https://devforum.roblox.com/t/how-do-i-make-my-grapple-system-have-swinging/3323694
- https://devforum.roblox.com/t/help-with-rope-swinging-thingy/3607575
- https://devforum.roblox.com/t/spidermans-web-swingings-vector-math/3292473
- https://devforum.roblox.com/t/grappling-hook-causes-players-to-glitch-through-parts/3346707
- https://create.roblox.com/docs/physics/network-ownership
- https://devforum.roblox.com/t/how-to-make-proper-knockback-for-a-combat-system/3936670
- https://devforum.roblox.com/t/introducing-shapecasts/2320655/1
- https://devforum.roblox.com/t/how-to-make-a-radiusaim-assist-for-mouse-target/2967093
- https://create.roblox.com/docs/reference/engine/enums/HumanoidStateType
- https://devforum.roblox.com/t/smoothly-dragging-other-players/128495
