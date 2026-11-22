# 0053 — Regras atuais do jogo: gelo não mata, zona mortal volta ao checkpoint, física do DDNet
- Status: Aceita (responde Q57, Q58, Q59; substitui 0014 e 0045; substitui em parte 0043; confirma 0049)
- Data: 2026-11-22
## Contexto
Os PRs #8–#25 (2026-11-19/20) trouxeram a física inspirada no DDNet, o martelo e o modo solo, e o gelo e a zona
mortal passaram a seguir o DDNet. Os ADRs ainda diziam outra coisa.
## Decisão
- **Gelo não mata:** congela enquanto toca o Freeze e solta ~1 s depois de sair (`Config.Freeze.ReleaseDelay`), ou na
  hora num Unfreeze. Sozinho e preso, o jogador recomeça.
- **Zona mortal (vermelha):** é o único elemento que "mata": leva o jogador **na hora** de volta ao checkpoint, sem
  animação de morte (como está no código).
- **Física do DDNet registrada:** os valores atuais do `Config` (andar 38, gravidade 112,5, pulo 51, pulo duplo 48,
  gancho DDNet) substituem o andar 24 do 0043. O `Config` é a fonte; as medidas derivadas ficam em
  [MEDIDAS_DO_MAPA](../04-game-design/MEDIDAS_DO_MAPA.md).
- **Martelo e modo solo** ficam no jogo.
- **Pulo duplo não recarrega** ao prender o gancho de novo durante o embalo: é de propósito (Q58).
- **O vermelho segura o gancho** também no MapBuilder (Q59; como o 0049).
- **Verde (gancho único)** volta ao renascer, ao recomeçar, ao passar de checkpoint e ao encostar no vermelho.
## Consequências
- 0014 e 0045 ficam substituídos. O validador (`tools/mapkit`) trata gelo como "travado" e vermelho como volta ao
  checkpoint.
