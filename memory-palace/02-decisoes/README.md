# Registro de decisões (ADR)

Cada decisão importante vira um arquivo `NNNN-titulo.md`. Decisões não são apagadas: se mudarem,
cria-se uma nova que **substitui** a antiga (e a antiga ganha o status "Substituída por NNNN").

Modelo:

```md
# NNNN — Título
- Status: Aceita | Proposta | Substituída por NNNN
- Data: AAAA-MM-DD
## Contexto
## Decisão
## Consequências
```

## Índice

| # | Decisão | Status |
|---|---|---|
| [0001](0001-genero-e-originalidade.md) | Corrida cooperativa fantasia, 100% original | Aceita |
| [0002](0002-servidores-abertos-e-bond.md) | Servidores abertos + equipes por Bond | Substituída por 0013 |
| [0003](0003-gancho-puxa-os-dois.md) | O gancho puxa os dois jogadores | Aceita |
| [0004](0004-solo-com-objetos-magicos.md) | Todo mapa completável solo com objetos mágicos | Aceita |
| [0005](0005-toolchain-rojo.md) | Rojo + Rokit + Wally, código só em arquivos | Aceita |
| [0006](0006-autoridade-servidor-cliente.md) | Servidor manda no estado, cliente na sensação | Aceita |
| [0007](0007-loader-sem-framework.md) | Loader próprio Init/Start, sem Knit | Aceita |
| [0008](0008-nome-race-and-escape.md) | Nome: Race and Escape | Aceita |
| [0009](0009-foco-pc.md) | Foco total no PC | Aceita |
| [0010](0010-mvp-mapas.md) | MVP: mapa solo + mapa coop (labirinto) | Substituída por 0022 |
| [0011](0011-camera-2-5d.md) | Câmera 2.5D lateral | Aceita (confirmada por 0038) |
| [0012](0012-varias-rotas.md) | Mapas com várias rotas até o final | Aceita |
| [0013](0013-sem-bond-por-enquanto.md) | Sem Bond por enquanto (substitui 0002) | Aceita |
| [0014](0014-gelo-mata.md) | Gelo: 15 s congelado, depois morte | Aceita |
| [0015](0015-cores.md) | Linguagem de cores (parcial) | Aceita |
| [0016](0016-gancho-regras.md) | Regras do gancho | Aceita |
| [0017](0017-bouncer.md) | Bouncer, pistola de impulso | Aceita |
| [0018](0018-progresso-por-jogador.md) | Progresso por jogador, checkpoints ~3 min | Aceita |
| [0019](0019-lamina-magica.md) | Lâmina mágica (empurrão) | Aceita |
| [0020](0020-mesmo-mapa-solo-e-grupo.md) | Mesmo mapa solo e grupo | Aceita |
| [0021](0021-cores-finais.md) | Descongelar laranja-brasa, não-grudável roxo | Aceita |
| [0022](0022-mvp-um-mapa.md) | MVP com um mapa (substitui 0010) | Aceita |
| [0023](0023-solo-primeiro.md) | Solo primeiro; Bond sem proteção depois do MVP | Aceita |
| [0024](0024-detalhes-ferramentas.md) | Bouncer some ao sair do trecho; lâmina descongela; verde volta | Aceita |
| [0025](0025-monetizacao-com-vantagens.md) | Monetização pode dar vantagens | Aceita |
| [0026](0026-objetos-deuses-romanos.md) | Objetos mágicos com nomes de deuses romanos | Aceita |
| [0027](0027-sem-pulo-duplo.md) | Sem pulo duplo: movimento é gancho + Bouncer | Aceita |
| [0028](0028-ranking-separa-boost.md) | Ranking separa quem usou boost | Aceita |
| [0029](0029-mapa-em-estagios.md) | Mapa em 6 estágios, ordem fixa, atalhos dentro dos estágios | Aceita |
| [0030](0030-progressao-de-atributo.md) | Progressão por ganho de atributo (estilo +1 Speed) | Aceita |
| [0031](0031-experimento-de-camera.md) | Experimento de câmera (descartado) | Substituída por 0038 |
| [0032](0032-rebirth-proposta.md) | Ciclo de rebirth | Proposta |
| [0033](0033-gancho-no-centro.md) | Gancho é a habilidade central e evolui; velocidade depois | Aceita |
| [0034](0034-checkpoint-a-cada-3-estagios.md) | Checkpoint a cada 3 estágios | Aceita |
| [0035](0035-mapa-do-experimento-reprovado.md) | Greybox do experimento reprovado (descartado) | Substituída por 0038 |
| [0036](0036-gancho-balanco-ropeconstraint.md) | Gancho: balanço (B) com RopeConstraint, mira com esfera, corda recolhível | Aceita |
| [0037](0037-gancho-em-jogador.md) | Gancho em jogador: caminho A; C como plano B; só após mapa aprovado | Aceita |
| [0038](0038-camera-2-5d-definitiva.md) | O jogo é 2.5D (decisão da equipe) | Aceita |
| [0039](0039-regras-do-plano-2-5d.md) | Regras do plano 2.5D: colisão, gancho, mira, W/S, altura da tela, estágios verticais, correção no servidor | Aceita |
| [0040](0040-checkpoint-mvp-e-ordem-das-fases.md) | Meta de 10–15 min por corrida, nível do gancho no MVP, nova ordem das fases | Aceita |
| [0041](0041-mapa-enrolado-e-tutorial.md) | Mapa enrolado, E1 difícil, tutorial do gancho no MVP, queda = checkpoint | Aceita |
| [0042](0042-gancho-puxao-direto.md) | Gancho vira puxão direto ao alvo (um clique), segurar para ficar preso, sem W/S | Aceita |
