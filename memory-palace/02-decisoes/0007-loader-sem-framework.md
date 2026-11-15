# 0007 — Loader próprio Init/Start, sem Knit
- Status: Aceita
- Data: 2026-11-11
## Decisão
`src/shared/Util/Loader.luau` carrega Services (servidor) e Controllers (cliente): todos os `Init`
em ordem, depois cada `Start` em sua própria task. Sem Knit ou framework parecido.
## Consequências
Módulos novos só precisam expor `Init`/`Start` opcionais e ficar na pasta certa.
