# 0006 — Servidor manda no estado, cliente na sensação
- Status: Aceita
- Data: 2026-11-11
## Decisão
Servidor é a autoridade de estado (congelado, checkpoint, tempo, Bond). Cliente controla a sensação
do próprio movimento (gancho solo, câmera, efeitos). Zonas usam tags do CollectionService + consultas espaciais.
Lógica pura separada de efeitos colaterais (para poder testar).
