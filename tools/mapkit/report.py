"""Relatório do validador (ADR 0052, etapa 3): Markdown em PT-BR para o dono e desenho SVG do mapa.

Usado por `tools/mapkit/validate.py` (não roda sozinho). `render(v)` devolve (markdown, svg).
"""

from __future__ import annotations

import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.mapkit.validate import (
    FILTERS,
    INF,
    REACTION,
    REFINE_TOLERANCE,
    RETRY,
    SIGMA_MEDIUM,
    STAGE_NAMES,
    STEP_MAX,
    WINDOW_CAP,
    Edge,
    Validation,
    p_success,
)

KIND_PT = {
    "walk": "andar/cair",
    "jump": "pulo",
    "double": "pulo duplo",
    "hook": "gancho",
    "jump+hook": "pulo + gancho",
    "hook+momentum": "gancho + embalo",
    "hook+double": "gancho + pulo duplo",
}
KIND_ORDER = list(KIND_PT)
ROUTE_PT = {"fastest": "mais rápida", "medium": "jogador médio", "safest": "mais segura"}
ZONE_PT = {"cp1": "checkpoint 1", "cp2": "checkpoint 2", "cp3": "checkpoint 3", "fin": "chegada"}


def br(v: float | None, d: int = 1) -> str:
    if v is None:
        return "—"
    if v == INF:
        return "∞"
    text = f"{v:.{d}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text.replace(".", ",")


def pct(a: float, b: float) -> str:
    return "—" if not b else f"{round(100 * a / b)}%"


def secs(v: float | None) -> str:
    if v is None:
        return "—"
    if v >= 60:
        return f"{int(v // 60)} min {round(v % 60):02d} s"
    return f"{br(v)} s"


def win_txt(w: float) -> str:
    if w == INF or w >= WINDOW_CAP:
        return "livre"
    return f"{br(w, 2)} s"


def difficulty(w: float) -> str:
    if w < 0.1:
        return "muito difícil"
    if w < 0.2:
        return "difícil"
    if w < 0.4:
        return "médio"
    return "fácil"


def zone_pt(z: str) -> str:
    return ZONE_PT.get(z, z)


def stage_pt(code: str) -> str:
    name = STAGE_NAMES.get(code)
    if name:
        return f"{code} ({name})"
    if code.startswith("R"):
        return f"{code} (respiro)"
    return code


def _where(v: Validation, x: float, y: float) -> str:
    return f"({br(x, 0)}, {br(y, 0)}) {v.geo.stage_of(x, y)}"


def _feet(v: Validation, nid: int) -> tuple[float, float]:
    n = v.graph.nodes[nid]
    return n.x, n.y - v.geo.params.feet_offset


def edge_where(v: Validation, e: Edge) -> str:
    a = _feet(v, e.src)
    b = _feet(v, e.dst)
    return f"{_where(v, *a)} → ({br(b[0], 0)}, {br(b[1], 0)})"


def _hardest_dim(e: Edge) -> str:
    r = e.refined or {}
    h = r.get("hardest")
    return h or "—"


# --------------------------------------------------------------------------------------------------
# Achados do resumo
# --------------------------------------------------------------------------------------------------


def _route_kind_share(summ: dict[str, Any]) -> tuple[int, int, int]:
    """(manobras com gancho, manobras sem gancho, total)."""
    hook = sum(d["count"] for k, d in summ["by_kind"].items() if "hook" in k)
    total = summ["maneuvers"]
    return hook, total - hook, total


def findings(v: Validation) -> list[str]:
    r = v.results
    g = v.graph
    out: list[str] = []
    order = r["order"]
    reach = r["stage_reach"]
    if all(reach):
        out.append(
            f"**O mapa se completa** sozinho na simulação: spawn → {' → '.join(zone_pt(z) for z in order)}. "
            f"{len(g.reached)} de {sum(1 for q in v.geo.platforms if q.in_region)} plataformas foram alcançadas."
        )
    else:
        first = next(i for i, ok in enumerate(reach) if not ok)
        out.append(f"**O validador não chegou ao {zone_pt(order[first])}** (pode ser falta de manobra amostrada; ver Limitações).")
    fast = r["routes"].get("fastest")
    med = r["routes"].get("medium")
    safe = r["routes"].get("safest")
    if fast and med:
        out.append(
            f"**Tempo:** rota mais rápida (entrada perfeita) {secs(fast['time'])}; jogador médio (erra e refaz) "
            f"≈ {secs(med['expected_medium'])} na rota que ele escolheria."
        )
    if fast:
        h, nh, tot = _route_kind_share(fast)
        no_hook = r["filters"].get("sem gancho")
        only_hook = r["filters"].get("só gancho (sem pulo nenhum)")
        out.append(
            f"**Gancho em quase tudo:** na rota mais rápida, {h} de {tot} manobras ({pct(h, tot)}) usam o gancho e "
            f"{nh} são só pulo/andar. Terminar **sem gancho**: "
            f"{'não dá' if no_hook is None else 'dá, em ' + secs(no_hook['time'])}. **Só com gancho, sem apertar pulo**: "
            f"{'não dá (o pulo é o ajudante do gancho: sair do chão, pulo duplo depois de soltar)' if only_hook is None else 'dá, em ' + secs(only_hook['time'])}."
        )
    st = r["stages"]
    passable_no_dj = [s["stage"] for s in st if s["stage"].startswith("E") and s["filters"].get("sem pulo duplo") is not None]
    passable_no_mom = [s["stage"] for s in st if s["stage"].startswith("E") and s["filters"].get("sem embalo") is not None]
    e_stages = [s["stage"] for s in st if s["stage"].startswith("E")]
    if e_stages:
        out.append(
            f"**Mecânicas que sobram:** {len(passable_no_dj)} de {len(e_stages)} estágios passam sem pulo duplo "
            f"({', '.join(passable_no_dj) or 'nenhum'}) e {len(passable_no_mom)} sem embalo de gancho "
            f"({', '.join(passable_no_mom) or 'nenhum'}). Nenhum estágio exige martelo nem parceiro (o simulador não tem)."
        )
    multi = [s for s in st if s["stage"].startswith("E") and len([d for d in s.get("disjoint", []) if d["spread"] >= 12]) >= 1]
    single = [s["stage"] for s in st if s["stage"].startswith("E") and s not in multi]
    if e_stages:
        out.append(
            f"**Bifurcações:** só {len(multi)} de {len(e_stages)} estágios têm um 2º caminho por plataformas diferentes "
            f"({', '.join(s['stage'] for s in multi) or 'nenhum'}); {', '.join(single) or 'nenhum'} têm um caminho só "
            f"(o rascunho previa 2–3 rotas por estágio)."
        )
    if med:
        wins = [g.edges[ei].w_eff for ei in med["edges"] if g.edges[ei].maneuver]
        hard = sum(1 for w in wins if w < 0.1)
        easy = sum(1 for w in wins if w >= 0.4)
        out.append(
            f"**Desafio:** na rota do jogador médio, {hard} de {len(wins)} manobras têm janela de acerto < 0,1 s "
            f"(muito difíceis) e {easy} têm ≥ 0,4 s (fáceis); o jogador médio erra ≈ {br(med['expected_errors'], 0)} vezes "
            f"no mapa (o maior peso vem das manobras de poucos quadros)."
        )
    drops = _route_blind(v, "medium")
    steps = r["steps"]
    big = [s for s in steps if s["class"] in ("só gancho", "2+ ganchos")]
    out.append(
        f"**Alturas:** {len(drops)} quedas às cegas na rota do jogador médio (destino mais de "
        f"{br(v.limits['below_feet'])} studs abaixo dos pés, fora da tela ao sair); {len(big)} degraus entre plataformas "
        f"(até {br(STEP_MAX, 0)} studs) passam de {br(v.rules.get('step_needs_hook', 24), 0)} studs e só sobem com gancho; "
        f"{len(steps) - len(big)} são de pulo/pulo duplo."
    )
    anc = r["anchors"]
    cnt = Counter(a.status for a in anc)
    out.append(
        f"**Pontos de gancho:** dos {len(anc)} pontos de gancho de propósito (verdes, soltos, nível 2), "
        f"{cnt.get('usado', 0)} são usados, {cnt.get('alcançável, não usado', 0)} alcançáveis mas nunca usados, "
        f"{cnt.get('só fora da tela', 0)} só alcançáveis fora da tela e {cnt.get('fora do alcance', 0)} fora do alcance."
    )
    out.append(
        f"**Ilhas e armadilhas:** {len(r['islands'])} plataformas da área jogável nunca foram alcançadas; "
        f"{len(r['traps'])} alcançadas não levam à chegada (só se sai morrendo/recomeçando, ou a saída não foi amostrada)."
    )
    return out


def _route_blind(v: Validation, key: str) -> list[tuple[Edge, float]]:
    summ = v.results["routes"].get(key)
    if not summ:
        return []
    out = []
    for ei in summ["edges"]:
        e = v.graph.edges[ei]
        if not e.maneuver:
            continue
        a, b = _feet(v, e.src), _feet(v, e.dst)
        if a[1] - b[1] > v.limits["below_feet"]:
            out.append((e, a[1] - b[1]))
    return out


# --------------------------------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------------------------------


def _sketch_routes(name: str) -> dict[str, int]:
    """Rotas previstas no rascunho (só map01; tools/map_sketch_fase2.py)."""
    if name != "Map01":
        return {}
    tools = Path(__file__).resolve().parents[1]
    try:
        sys.path.insert(0, str(tools))
        import map_sketch_fase2 as sketch  # type: ignore  # noqa: PLC0415

        return dict(Counter(r[0] for r in sketch.routes))
    except Exception:  # noqa: BLE001
        return {}
    finally:
        if sys.path and sys.path[0] == str(tools):
            sys.path.pop(0)


def render(v: Validation, svg_name: str = "validacao.svg", tiles_path: str = "") -> tuple[str, str]:
    return render_markdown(v, svg_name, tiles_path), render_svg(v)


def render_markdown(v: Validation, svg_name: str, tiles_path: str) -> str:
    r = v.results
    g = v.graph
    geo = v.geo
    s = v.settings
    L: list[str] = []
    a = L.append
    quick = s.node_spacing > 10
    a(f"# Validação do mapa {geo.tiles.name} (gerado)")
    a("")
    a("> **Arquivo gerado** por `tools/mapkit/validate.py` (ADR 0052, etapa 3). Não edite à mão: rode de novo.")
    a(f"> Comando: `python -I -X utf8 tools/mapkit/validate.py {tiles_path}{' --quick' if quick else ''}` · "
      f"modo {'rápido (--quick)' if quick else 'completo'} · {secs(v.seconds)} de execução.")
    a(f"> Simulação: {g.stats['sims']} manobras simuladas, {len(g.reached)} plataformas alcançadas, "
      f"{g.stats['hang_nodes']} pontos pendurados, {g.stats['edges']} ligações (arestas). Desenho: [{svg_name}]({svg_name}).")
    a("")
    a("O validador \"joga\" o mapa sozinho: de cada ponto onde dá para ficar em pé (ou pendurado), testa um conjunto")
    a("de manobras com o simulador do movimento (`tools/mapkit/physics.py`, números do `Config.luau`) e anota aonde")
    a("cada uma leva, quanto tempo leva e **quanta folga** ela tem (a *janela de acerto*: quanto dá para errar o")
    a("momento de pular/soltar/onde pular e ainda dar certo). Leia as [limitações](#limitações) antes de decidir.")
    a("")
    a("## Resumo")
    a("")
    for k, f in enumerate(findings(v), 1):
        a(f"{k}. {f}")
    a("")
    a("**Como ler a janela de acerto:** < 0,1 s = muito difícil (poucos quadros); 0,1–0,2 s = difícil; 0,2–0,4 s =")
    a(f"médio; ≥ 0,4 s = fácil; \"livre\" = sem tempo certo (andar, segurar o gancho). Uma variação \"dá certo\" se o")
    a(f"jogador não fica mais de {br(REFINE_TOLERANCE)} s atrás de onde a manobra original o deixaria.")
    a("")

    # --- tempo
    a("## Tempo estimado")
    a("")
    a("| Rota | Tempo (sem errar) | Tempo esperado do jogador médio | Manobras | Erros esperados do jogador médio |")
    a("|---|---|---|---|---|")
    for key in ("fastest", "medium", "safest"):
        summ = r["routes"].get(key)
        if not summ:
            a(f"| {ROUTE_PT[key]} | não achada | | | |")
            continue
        a(f"| {ROUTE_PT[key]} | {secs(summ['time'])} | {secs(summ['expected_medium'])} | {summ['maneuvers']} | "
          f"{br(summ['expected_errors'], 0)} |")
    a("")
    a(f"*Mais rápida* = menor tempo com entrada perfeita. *Jogador médio* = rota que minimiza o tempo esperado de quem")
    a(f"erra o tempo das teclas com desvio de {br(SIGMA_MEDIUM * 1000, 0)} ms, pensa {br(REACTION, 2)} s antes de cada manobra")
    a(f"e perde {br(RETRY, 0)} s a cada erro. *Mais segura* = a que maximiza a chance de não errar (o tempo só desempata).")
    a("")
    fast = r["routes"].get("fastest")
    med = r["routes"].get("medium")
    if fast:
        a("Por trecho:")
        a("")
        a("| Trecho | Mais rápida | Jogador médio (esperado) | Manobras (rápida / médio) |")
        a("|---|---|---|---|")
        prev = "spawn"
        for k, sec in enumerate(fast["sections"]):
            ms = med["sections"][k] if med and k < len(med["sections"]) else None
            a(f"| {prev} → {zone_pt(sec['zone'])} | {secs(sec['time'])} | {secs(ms['expected_medium']) if ms else '—'} | "
              f"{sec['maneuvers']} / {ms['maneuvers'] if ms else '—'} |")
            prev = zone_pt(sec["zone"])
        a("")

    # --- alcançabilidade
    a("## Alcançabilidade")
    a("")
    order = r["order"]
    prev = "spawn"
    for z, ok in zip(order, r["stage_reach"]):
        a(f"- {prev} → {zone_pt(z)}: {'**alcançável**' if ok else '**NÃO alcançado**'}")
        prev = zone_pt(z)
    n_region = sum(1 for q in geo.platforms if q.in_region)
    a(f"- Plataformas: {len(geo.platforms)} no mapa, {n_region} na área jogável (ligadas por ar ao spawn), "
      f"{len(g.reached)} alcançadas pela simulação.")
    a("")
    isl = sorted(r["islands"], key=lambda q: -q.width)
    a(f"### Ilhas ({len(isl)} plataformas nunca alcançadas)")
    a("")
    if isl:
        by_stage = Counter(q.stage for q in isl)
        a("Por estágio: " + ", ".join(f"{k} {n}" for k, n in sorted(by_stage.items())) + ".")
        a("")
        a("| Estágio | Plataforma (studs) | Largura |")
        a("|---|---|---|")
        for q in isl[:15]:
            a(f"| {q.stage} | {q.label()} | {br(q.width, 0)} |")
        if len(isl) > 15:
            a(f"| … | mais {len(isl) - 15} (menores) | |")
        a("")
        a("Ilha pode ser decoração (topo de pilar, borda de rocha) ou um lugar que o dono queria acessível. Pode também")
        a("ser alcançável com uma manobra que o validador não testa (gancho em parceiro, martelo, 2 ganchos no ar).")
        a("")
    traps = sorted(r["traps"], key=lambda q: (q.stage, q.x0))
    a(f"### Armadilhas ({len(traps)} plataformas alcançadas de onde não se chega à chegada)")
    a("")
    if traps:
        a("| Estágio | Plataforma (studs) |")
        a("|---|---|")
        for q in traps[:20]:
            a(f"| {q.stage} | {q.label()} |")
        if len(traps) > 20:
            a(f"| … | mais {len(traps) - 20} |")
        a("")
        a("Sozinho, quem cai aqui só sai morrendo (Kill) ou recomeçando. Com parceiro pode haver saída (puxão).")
        a("")

    # --- tipos de manobra
    a("## Tipos de manobra (\"só gancho\"?)")
    a("")
    a("| Manobra | " + " | ".join(ROUTE_PT[k] for k in ("fastest", "medium", "safest")) + " |")
    a("|---|---|---|---|")
    for kind in KIND_ORDER:
        cells = []
        for key in ("fastest", "medium", "safest"):
            summ = r["routes"].get(key)
            if not summ:
                cells.append("—")
                continue
            c = summ["by_kind"].get(kind, {"count": 0})["count"]
            cells.append(f"{c} ({pct(c, summ['maneuvers'])})")
        a(f"| {KIND_PT[kind]} | " + " | ".join(cells) + " |")
    a("")
    a("Dá para terminar o mapa inteiro…")
    a("")
    for name, summ in r["filters"].items():
        a(f"- **{name}**: {'não' if summ is None else 'sim, em ' + secs(summ['time'])}")
    a("")
    a("Por estágio (cruzando o estágio do ponto onde a rota mais rápida entra até onde sai; \"não\" = não passa):")
    a("")
    names = [n for n in FILTERS if n != "tudo"]
    a("| Estágio | Tempo | Manobras na rota | " + " | ".join(names) + " |")
    a("|---|---|---|" + "---|" * len(names))
    for st in r["stages"]:
        kinds = ", ".join(f"{KIND_PT[k]} {n}" for k, n in sorted(st["kinds"].items(), key=lambda kv: -kv[1]))
        cells = []
        for n in names:
            t = st["filters"].get(n)
            cells.append("não" if t is None else ("sim" if t <= st["time"] * 1.3 + 0.5 else f"sim ({secs(t)})"))
        a(f"| {stage_pt(st['stage'])} | {secs(st['time'])} | {kinds or '—'} | " + " | ".join(cells) + " |")
    a("")
    a("\"sim\" sozinho = passa sem perder quase nada (até 30% mais lento); \"sim (tempo)\" = passa, mas mais devagar.")
    a("Onde \"sem pulo duplo\" ou \"sem embalo\" dá \"sim\", aquela mecânica **nunca é necessária** no estágio.")
    a("")

    # --- bifurcações
    a("## Bifurcações")
    a("")
    sketch = _sketch_routes(geo.tiles.name)
    a("Caminhos por plataformas diferentes entre a entrada e a saída de cada estágio (o validador acha o mais rápido,")
    a("proíbe as plataformas do meio dele e procura outro). \"Afastamento\" = distância média (studs) do caminho até o")
    a("primeiro; abaixo de ~12 é praticamente o mesmo caminho por outro degrau.")
    a("")
    a("| Estágio | Previstas no rascunho | Caminhos achados | Diferentes de verdade (afastamento ≥ 12) | Tempos | Menor janela de cada |")
    a("|---|---|---|---|---|---|")
    for st in r["stages"]:
        if not st["stage"].startswith("E"):
            continue
        ds = st.get("disjoint", [])
        real = 1 + sum(1 for d in ds[1:] if d["spread"] >= 12) if ds else 0
        a(f"| {stage_pt(st['stage'])} | {sketch.get(st['stage'], '—')} | {len(ds)} | {real} | "
          f"{' / '.join(secs(d['time']) for d in ds) or '—'} | {' / '.join(win_txt(d['min_window']) for d in ds) or '—'} |")
    a("")

    # --- desafio
    a("## Desafio")
    a("")
    if med:
        a("Rota do jogador médio, por estágio (janela = folga da manobra mais apertada; refinada quadro a quadro):")
        a("")
        a("| Estágio | Manobras | Menor janela | Muito difíceis (< 0,1 s) | Fáceis (≥ 0,4 s) | Classe |")
        a("|---|---|---|---|---|---|")
        curve = _stage_curve(v, med)
        for st, wins in curve:
            mn = min(wins) if wins else INF
            a(f"| {stage_pt(st)} | {len(wins)} | {win_txt(mn)} | {sum(1 for w in wins if w < 0.1)} | "
              f"{sum(1 for w in wins if w >= 0.4)} | {difficulty(mn) if wins else '—'} |")
        a("")
        a("Curva de dificuldade (menor janela por estágio, na ordem da corrida; o ADR 0052 quer alternar difícil e fácil):")
        a("")
        a("```")
        for st, wins in curve:
            mn = min(wins) if wins else WINDOW_CAP
            bar = "█" * max(1, round((1 - min(mn, 0.5) / 0.5) * 20))
            a(f"{st:>4} {bar:<20} {win_txt(mn)}")
        a("```")
        a("(barra maior = mais difícil)")
        a("")
        a("Manobras mais apertadas da rota do jogador médio:")
        a("")
        a("| Onde (pés, studs) | Manobra | Janela | O que aperta | Mira (graus) |")
        a("|---|---|---|---|---|")
        es = sorted((g.edges[ei] for ei in med["edges"] if g.edges[ei].maneuver), key=lambda e: e.w_eff)
        for e in es[:12]:
            aim = (e.refined or {}).get("aim_deg")
            a(f"| {edge_where(v, e)} | {KIND_PT.get(e.label, e.label)} | {win_txt(e.w_eff)} | {_hardest_dim(e)} | "
              f"{br(aim, 0) if aim else '—'} |")
        a("")
        triv = [st for st, wins in curve if wins and min(wins) >= 0.4]
        a(f"Estágios triviais (tudo com janela ≥ 0,4 s): {', '.join(triv) or 'nenhum'}.")
        a("")

    # --- alturas
    a("## Alturas")
    a("")
    steps = r["steps"]
    cnt = Counter(s_["class"] for s_ in steps)
    a(f"Degraus (fim de plataforma encostado numa parede de até {br(STEP_MAX, 0)} studs com outra plataforma em cima), "
      f"pelas regras de `MEDIDAS_DO_MAPA.md`: " + ", ".join(f"{k} {n}" for k, n in cnt.most_common()) + ".")
    a("")
    odd = [s_ for s_ in steps if s_["class"] in ("no limite do pulo duplo", "só gancho", "2+ ganchos") and s_["reached_from"]]
    if odd:
        a("| Onde (studs) | Altura | Classe | Subido pelo validador com |")
        a("|---|---|---|---|")
        for s_ in sorted(odd, key=lambda d: -d["height"])[:15]:
            a(f"| {_where(v, s_['x'], s_['y'])} | {br(s_['height'], 0)} | {s_['class']} | "
              f"{', '.join(KIND_PT.get(k, k) for k in s_['climbed_with']) or 'não subiu daqui'} |")
        a("")
    a(f"**Quedas às cegas** (o destino fica mais de {br(v.limits['below_feet'])} studs abaixo dos pés: fora da tela ao sair):")
    a("")
    for key in ("fastest", "medium"):
        bl = _route_blind(v, key)
        a(f"- rota {ROUTE_PT[key]}: {len(bl)}" + (": " + "; ".join(
            f"{br(h, 0)} studs em {v.geo.stage_of(*_feet(v, e.src))}" for e, h in sorted(bl, key=lambda q: -q[1])[:8]) if bl else ""))
    a(f"- no mapa todo: {len(r['drops']['pairs'])} pares de plataformas ligados por uma queda assim (qualquer manobra).")
    a("")
    if med:
        a("Altura dos pés ao longo da rota do jogador médio, por estágio (mín.–máx., studs):")
        a("")
        prof: dict[str, list[float]] = defaultdict(list)
        seq: list[str] = []
        for nid in med["nodes"]:
            x, y = _feet(v, nid)
            stn = v.geo.stage_of(x, y)
            if stn not in prof:
                seq.append(stn)
            prof[stn].append(y)
        a(", ".join(f"{k} {br(min(prof[k]), 0)}–{br(max(prof[k]), 0)}" for k in seq) + ".")
        a("")

    # --- gancho
    a("## Alcance do gancho")
    a("")
    anc = r["anchors"]
    a(f"Pontos de gancho \"de propósito\": peças HookOnce (verdes), blocos pequenos soltos (até 40 células) e peças com")
    a(f"`RequiresHookLevel`. \"Alcançável\" = algum ponto alcançado (em pé, no topo do pulo/pulo duplo ou pendurado) vê o")
    a(f"ponto no alcance ({br(v.geo.params.hook_range, 0)} studs) e na tela (até {br(v.limits['up'])} acima e "
      f"{br(v.limits['down'])} abaixo do root).")
    a("")
    a("| Tipo | Usado | Alcançável, não usado | Só fora da tela | Fora do alcance |")
    a("|---|---|---|---|---|")
    for kind in ("HookOnce", "solto", "nível 2"):
        cnt = Counter(x.status for x in anc if x.kind == kind)
        a(f"| {kind} | {cnt.get('usado', 0)} | {cnt.get('alcançável, não usado', 0)} | {cnt.get('só fora da tela', 0)} | "
          f"{cnt.get('fora do alcance', 0)} |")
    a("")
    bad = [x for x in anc if x.status != "usado"]
    if bad:
        a("| Ponto (centro, studs) | Tipo | Situação | Mais perto que se mira |")
        a("|---|---|---|---|")
        for x in sorted(bad, key=lambda q: (q.status, q.stage)):
            a(f"| {_where(v, *x.center)} | {x.kind} | {x.status} | {br(x.best_distance, 0) + ' studs' if x.best_distance < INF else '—'} |")
        a("")
    a("O nível do gancho (`RequiresHookLevel`) é ignorado pelo simulador: as peças de nível 2 contam como prendíveis.")
    a("")

    # --- limitações
    a("## Limitações")
    a("")
    a("- **Um jogador só.** Sem gancho em parceiro, martelo, empurrão, modo solo. Gelo (Freeze) conta como fracasso")
    a("  (sem parceiro para soltar). Os trechos pensados para a dupla aparecem como difíceis, armadilhas ou ilhas.")
    a("- **Amostragem.** Cada ponto testa um conjunto pequeno de manobras (alguns momentos de pulo duplo, alguns")
    a(f"  alvos de gancho por setor de ângulo, soltar em {len(s.release_times)} momentos, 1 gancho por manobra ou um")
    a("  gancho de cada vez a partir de pendurado). Rotas que precisam de algo fora disso não aparecem: **\"não alcançado\",")
    a("  ilha, armadilha e \"não passa sem X\" querem dizer \"o validador não achou\", não \"impossível\"**. Os tempos são")
    a("  um teto (um jogador bom acha atalhos) e as bifurcações, um piso.")
    a("- **Janela de acerto** = variação de cada entrada sozinha (as outras fixas), em passos de 1 quadro (tempo), 1 stud")
    a("  (lugar) e 1 grau (mira); a janela da manobra é a da entrada mais apertada. Só as manobras das rotas são")
    a("  refinadas assim; as outras usam a janela grosseira da família de manobras.")
    a("- **Simulador** (ver o topo de `physics.py`): caixa 2 × 5,5 sem atrito, sem subida automática de degrau, mundo")
    a("  em grade (rampas viraram degraus de 2 studs), Humanoid com velocidade instantânea. Pousar \"com embalo\" conta")
    a("  como parar no ponto de pouso.")
    a("- **Câmera:** \"na tela\" usa a área visível parada (16:9), sem o adiantamento da câmera nem o atraso na queda.")
    a("- **Checkpoint e chegada** contam como no jogo (root na coluna acima da peça, até ZoneHeight); morrer volta ao")
    a("  checkpoint, mas o validador não usa isso como atalho.")
    a("")
    return "\n".join(L) + "\n"


def _stage_curve(v: Validation, summ: dict[str, Any]) -> list[tuple[str, list[float]]]:
    out: list[tuple[str, list[float]]] = []
    for ei in summ["edges"]:
        e = v.graph.edges[ei]
        stn = v.graph.node_stage(e.src)
        if not out or out[-1][0] != stn:
            out.append((stn, []))
        if e.maneuver:
            out[-1][1].append(e.w_eff)
    merged: list[tuple[str, list[float]]] = []
    for stn, wins in out:
        if merged and merged[-1][0] == stn:
            merged[-1][1].extend(wins)
        elif not wins and stn.startswith("Mapa"):
            continue
        else:
            merged.append((stn, list(wins)))
    return merged


def console_summary(v: Validation) -> str:
    lines = ["", "Resumo:"]
    for k, f in enumerate(findings(v), 1):
        lines.append(f" {k}. {f.replace('**', '')}")
    return "\n".join(lines)


# --------------------------------------------------------------------------------------------------
# SVG
# --------------------------------------------------------------------------------------------------

COLORS = {
    "Block": "#8a8f98",
    "Unhookable": "#7b4fa8",
    "HookOnce": "#3fbf5a",
    "HookThrough": "#b0c4de",
    "Kill": "#d9363e",
    "Freeze": "#7fd3f0",
    "Unfreeze": "#f2b134",
    "Checkpoint": "#ffd84a",
    "FinishLine": "#ffffff",
    "RaceStart": "#4a90e2",
    "OneWay": "#c0a060",
}
DIFF_COLOR = [(0.1, "#d7191c"), (0.2, "#fd8d3c"), (0.4, "#fecc5c"), (INF, "#1a9641")]


def _diff_color(w: float) -> str:
    for lim, c in DIFF_COLOR:
        if w < lim:
            return c
    return DIFF_COLOR[-1][1]


def render_svg(v: Validation, scale: float = 0.75) -> str:
    geo = v.geo
    tm = geo.tiles
    x0, y0, x1, y1 = tm.bounds()
    W = (x1 - x0) * scale
    H = (y1 - y0) * scale
    legend_h = 120

    def X(x: float) -> float:
        return round((x - x0) * scale, 1)

    def Y(y: float) -> float:
        return round((y1 - y) * scale, 1)

    o: list[str] = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{round(W)}" height="{round(H + legend_h)}" '
             f'viewBox="0 0 {round(W)} {round(H + legend_h)}" font-family="sans-serif">')
    o.append(f'<rect width="{round(W)}" height="{round(H + legend_h)}" fill="#1c1f26"/>')
    # peças
    for rc in tm.rects():
        cx, cy = tm.cell_min(rc.i, rc.j)
        c = COLORS.get(rc.element, "#888")
        o.append(f'<rect x="{X(cx)}" y="{Y(cy + rc.h * tm.cell)}" width="{round(rc.w * tm.cell * scale, 1)}" '
                 f'height="{round(rc.h * tm.cell * scale, 1)}" fill="{c}" opacity="0.55"/>')
    # estágios
    for name, sx1, sy1, sx2, sy2 in geo.stages:
        if not name.startswith("E"):
            continue
        o.append(f'<rect x="{X(sx1)}" y="{Y(sy2)}" width="{round((sx2 - sx1) * scale, 1)}" height="{round((sy2 - sy1) * scale, 1)}" '
                 f'fill="none" stroke="#9fb3c8" stroke-dasharray="6,4" stroke-width="1"/>')
        o.append(f'<text x="{X(sx1) + 4}" y="{Y(sy2) + 14}" fill="#cfe0f0" font-size="13" font-weight="bold">{name}</text>')
    # plataformas
    reached = v.graph.reached
    islands = {q.pid for q in v.results["islands"]}
    traps = {q.pid for q in v.results["traps"]}
    for q in geo.platforms:
        if not q.in_region:
            continue
        if q.pid in traps:
            col, w = "#ff4fd8", 3
        elif q.pid in reached:
            col, w = "#5cff7a", 2
        elif q.pid in islands:
            col, w = "#ff9f1c", 3
        else:
            continue
        o.append(f'<line x1="{X(q.x0 - 1)}" y1="{Y(q.floor_y)}" x2="{X(q.x1 + 1)}" y2="{Y(q.floor_y)}" stroke="{col}" stroke-width="{w}"/>')
    # rotas: segura (tracejada) e jogador médio (cor = dificuldade)
    traj = v.results["trajectories"]
    for key, style in (("safest", 'stroke="#c8a2ff" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.8"'),):
        summ = v.results["routes"].get(key)
        if not summ:
            continue
        for ei in summ["edges"]:
            pts = traj.get(ei) or []
            if len(pts) >= 2:
                o.append(f'<polyline fill="none" {style} points="{" ".join(f"{X(x)},{Y(y - 3)}" for x, y in pts)}"/>')
    med = v.results["routes"].get("medium")
    if med:
        for ei in med["edges"]:
            e = v.graph.edges[ei]
            pts = traj.get(ei) or []
            if len(pts) < 2:
                continue
            col = _diff_color(e.w_eff) if e.maneuver else "#1a9641"
            o.append(f'<polyline fill="none" stroke="{col}" stroke-width="2.5" points="{" ".join(f"{X(x)},{Y(y - 3)}" for x, y in pts)}"/>')
    fast = v.results["routes"].get("fastest")
    if fast:
        for ei in fast["edges"]:
            pts = traj.get(ei) or []
            if len(pts) >= 2:
                o.append(f'<polyline fill="none" stroke="#4fc3ff" stroke-width="1.2" opacity="0.9" '
                         f'points="{" ".join(f"{X(x)},{Y(y - 3)}" for x, y in pts)}"/>')
    # pontos de gancho com problema
    for x in v.results["anchors"]:
        cx, cy = X(x.center[0]), Y(x.center[1])
        if x.status == "fora do alcance":
            o.append(f'<g stroke="#ff2d2d" stroke-width="2.5"><line x1="{cx - 6}" y1="{cy - 6}" x2="{cx + 6}" y2="{cy + 6}"/>'
                     f'<line x1="{cx - 6}" y1="{cy + 6}" x2="{cx + 6}" y2="{cy - 6}"/></g>')
        elif x.status == "só fora da tela":
            o.append(f'<circle cx="{cx}" cy="{cy}" r="7" fill="none" stroke="#ff9f1c" stroke-width="2.5"/>')
        elif x.status == "alcançável, não usado":
            o.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="none" stroke="#e0e0e0" stroke-width="1.5" stroke-dasharray="2,2"/>')
    # zonas e spawn
    for z in geo.zones:
        o.append(f'<text x="{X(z.x0)}" y="{Y(z.y1) - 2}" fill="#ffd84a" font-size="13" font-weight="bold">{zone_pt(z.zid)}</text>')
    sx, sy = geo.spawn
    o.append(f'<circle cx="{X(sx)}" cy="{Y(sy + 3)}" r="6" fill="#4a90e2" stroke="#fff"/>')
    o.append(f'<text x="{X(sx) + 8}" y="{Y(sy + 3) - 6}" fill="#fff" font-size="12">spawn</text>')
    # legenda
    ly = H + 18
    items = [
        ("line", "#5cff7a", "plataforma alcançada"),
        ("line", "#ff9f1c", "ilha (não alcançada)"),
        ("line", "#ff4fd8", "armadilha (não leva à chegada)"),
        ("line", "#4fc3ff", "rota mais rápida"),
        ("dash", "#c8a2ff", "rota mais segura"),
        ("line", "#1a9641", "rota do jogador médio: fácil (≥ 0,4 s)"),
        ("line", "#fecc5c", "médio (0,2–0,4 s)"),
        ("line", "#fd8d3c", "difícil (0,1–0,2 s)"),
        ("line", "#d7191c", "muito difícil (< 0,1 s)"),
        ("x", "#ff2d2d", "ponto de gancho fora do alcance"),
        ("circle", "#ff9f1c", "ponto de gancho só fora da tela"),
        ("dot", "#e0e0e0", "ponto de gancho alcançável, nunca usado"),
    ]
    col_w = W / 3
    for k, (kind, col, text) in enumerate(items):
        cx = 16 + (k % 3) * col_w
        cy = ly + (k // 3) * 24
        if kind == "line":
            o.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + 28}" y2="{cy}" stroke="{col}" stroke-width="3"/>')
        elif kind == "dash":
            o.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + 28}" y2="{cy}" stroke="{col}" stroke-width="2" stroke-dasharray="4,3"/>')
        elif kind == "x":
            o.append(f'<g stroke="{col}" stroke-width="2.5"><line x1="{cx + 8}" y1="{cy - 6}" x2="{cx + 20}" y2="{cy + 6}"/>'
                     f'<line x1="{cx + 8}" y1="{cy + 6}" x2="{cx + 20}" y2="{cy - 6}"/></g>')
        elif kind == "circle":
            o.append(f'<circle cx="{cx + 14}" cy="{cy}" r="7" fill="none" stroke="{col}" stroke-width="2.5"/>')
        else:
            o.append(f'<circle cx="{cx + 14}" cy="{cy}" r="6" fill="none" stroke="{col}" stroke-width="1.5" stroke-dasharray="2,2"/>')
        o.append(f'<text x="{cx + 36}" y="{cy + 4}" fill="#e8e8e8" font-size="13">{text}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


__all__ = ["console_summary", "findings", "render", "render_markdown", "render_svg", "p_success"]
