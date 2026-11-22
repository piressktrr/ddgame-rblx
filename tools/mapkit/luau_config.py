"""Leitor do `src/shared/Config.luau` (fonte única dos números do jogo).

Lê a tabela `local Config = { ... }` e devolve um dict aninhado com os valores. Nada de número
copiado à mão: quem precisa de uma medida (simulador, métricas, validador) chama `load_config()`.

Valores aceitos:
- números (inteiros, decimais, hexadecimais, notação científica) e expressões simples com
  `+ - * / ^` e parênteses (ex.: `1 / 60`);
- `true`, `false`, strings ('...' ou "...");
- tabelas aninhadas `{ Chave = valor, ... }` e listas `{ a, b, c }` (viram list);
- `Vector3.new(a, b, c)` e `Vector2.new(a, b)` viram tuplas de floats.

Ignorados (a chave fica de fora): `Color3.*(...)`, `Enum.*`, `nil` e qualquer outra expressão que o
parser não entenda. A lista do que ficou de fora sai em `ConfigData.skipped` (para depuração).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "src" / "shared" / "Config.luau"

_BLOCK_COMMENT_RE = re.compile(r"--\[(=*)\[")
_LONG_STRING_RE = re.compile(r"\[(=*)\[")
_SKIP = object()  # valor que o parser não converte (Color3, Enum...)

_TOKEN_RE = re.compile(
    r"""
    (?P<ws>\s+)
  | (?P<number>0[xX][0-9a-fA-F_]+|(?:\d[\d_]*\.?[\d_]*|\.\d[\d_]*)(?:[eE][+-]?\d+)?)
  | (?P<string>"(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*')
  | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<op>\.\.|[{}()\[\]=,;.:+\-*/^%#<>~])
    """,
    re.VERBOSE,
)


@dataclass
class ConfigData:
    """Resultado da leitura: valores, caminho, hash do arquivo e chaves ignoradas."""

    values: dict[str, Any]
    path: Path
    sha256: str
    skipped: list[str] = field(default_factory=list)

    def __getitem__(self, key: str) -> Any:
        return self.values[key]

    def get(self, dotted: str, default: Any = None) -> Any:
        """Valor por caminho com pontos, ex.: `cfg.get("Movement.Gravity")`."""
        node: Any = self.values
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node


def strip_comments(source: str) -> str:
    """Tira comentários Luau (`--` de linha e `--[[ ]]`/`--[==[ ]==]` de bloco), respeitando strings."""
    out: list[str] = []
    i = 0
    n = len(source)
    while i < n:
        ch = source[i]
        if ch in "\"'":
            j = i + 1
            while j < n and source[j] != ch and source[j] != "\n":
                j += 2 if source[j] == "\\" else 1
            out.append(source[i : j + 1])
            i = j + 1
            continue
        if source.startswith("--", i):
            block = _BLOCK_COMMENT_RE.match(source, i)
            if block:
                close = "]" + block.group(1) + "]"
                end = source.find(close, block.end())
                i = n if end < 0 else end + len(close)
                out.append(" ")
            else:
                end = source.find("\n", i)
                i = n if end < 0 else end
            continue
        block = _LONG_STRING_RE.match(source, i) if ch == "[" else None
        if block:
            close = "]" + block.group(1) + "]"
            end = source.find(close, block.end())
            stop = n if end < 0 else end + len(close)
            out.append('"' + source[block.end() : end if end >= 0 else n].replace('"', "'") + '"')
            i = stop
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _tokenize(source: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    pos = 0
    while pos < len(source):
        match = _TOKEN_RE.match(source, pos)
        if not match:
            raise ValueError(f"caractere inesperado no Config: {source[pos:pos + 20]!r}")
        pos = match.end()
        kind = match.lastgroup
        if kind == "ws":
            continue
        tokens.append((kind or "", match.group()))
    return tokens


def _parse_number(text: str) -> float | int:
    text = text.replace("_", "")
    if text.lower().startswith("0x"):
        return int(text, 16)
    value = float(text)
    if value.is_integer() and re.fullmatch(r"\d+", text):
        return int(value)
    return value


def _unescape(text: str) -> str:
    body = text[1:-1]
    return re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), body)


class _Parser:
    def __init__(self, tokens: list[tuple[str, str]]):
        self.tokens = tokens
        self.pos = 0
        self.skipped: list[str] = []
        self.path: list[str] = []

    # --- utilidades ---
    def peek(self, offset: int = 0) -> tuple[str, str]:
        index = self.pos + offset
        return self.tokens[index] if index < len(self.tokens) else ("eof", "")

    def take(self) -> tuple[str, str]:
        token = self.peek()
        self.pos += 1
        return token

    def expect(self, value: str) -> None:
        kind, text = self.take()
        if text != value:
            raise ValueError(f"esperava {value!r}, achei {text!r} (em {'.'.join(self.path)})")

    def accept(self, value: str) -> bool:
        if self.peek()[1] == value:
            self.pos += 1
            return True
        return False

    # --- tabela ---
    def parse_table(self) -> dict[str, Any] | list[Any]:
        self.expect("{")
        named: dict[str, Any] = {}
        listed: list[Any] = []
        while not self.accept("}"):
            kind, text = self.peek()
            key: str | None = None
            if kind == "name" and self.peek(1)[1] == "=":
                key = text
                self.pos += 2
            elif text == "[":
                self.pos += 1
                raw = self.parse_expr()
                self.expect("]")
                self.expect("=")
                key = str(raw)
            self.path.append(key if key is not None else str(len(listed) + 1))
            value = self.parse_expr()
            self.path.pop()
            if value is _SKIP:
                self.skipped.append(".".join([*self.path, key or str(len(listed) + 1)]))
            elif key is not None:
                named[key] = value
            else:
                listed.append(value)
            if not (self.accept(",") or self.accept(";")):
                self.expect("}")
                break
        if listed and not named:
            return listed
        return named

    # --- expressões ---
    def parse_expr(self) -> Any:
        left = self.parse_term()
        while self.peek()[1] in ("+", "-"):
            op = self.take()[1]
            right = self.parse_term()
            left = _arith(op, left, right)
        return left

    def parse_term(self) -> Any:
        left = self.parse_power()
        while self.peek()[1] in ("*", "/", "%"):
            op = self.take()[1]
            right = self.parse_power()
            left = _arith(op, left, right)
        return left

    def parse_power(self) -> Any:
        base = self.parse_unary()
        if self.peek()[1] == "^":
            self.take()
            exponent = self.parse_power()
            return _arith("^", base, exponent)
        return base

    def parse_unary(self) -> Any:
        if self.accept("-"):
            value = self.parse_unary()
            return _SKIP if value is _SKIP or isinstance(value, bool) else -value
        return self.parse_atom()

    def parse_atom(self) -> Any:
        kind, text = self.peek()
        if kind == "number":
            self.pos += 1
            return _parse_number(text)
        if kind == "string":
            self.pos += 1
            return _unescape(text)
        if text == "{":
            return self.parse_table()
        if text == "(":
            self.pos += 1
            value = self.parse_expr()
            self.expect(")")
            return value
        if kind == "name":
            if text in ("true", "false"):
                self.pos += 1
                return text == "true"
            if text == "nil":
                self.pos += 1
                return _SKIP
            return self.parse_call_or_path()
        raise ValueError(f"valor inesperado {text!r} (em {'.'.join(self.path)})")

    def parse_call_or_path(self) -> Any:
        parts = [self.take()[1]]
        while self.peek()[1] in (".", ":") and self.peek(1)[0] == "name":
            self.pos += 1
            parts.append(self.take()[1])
        dotted = ".".join(parts)
        if self.peek()[1] != "(":
            return _SKIP  # Enum.Font.X, referências a outras variáveis
        self.pos += 1
        args: list[Any] = []
        while not self.accept(")"):
            args.append(self.parse_expr())
            if not self.accept(","):
                self.expect(")")
                break
        if dotted in ("Vector3.new", "Vector2.new") and all(
            isinstance(a, (int, float)) and not isinstance(a, bool) for a in args
        ):
            return tuple(float(a) for a in args)
        return _SKIP  # Color3.fromRGB(...) e outras chamadas


def _arith(op: str, left: Any, right: Any) -> Any:
    numeric = (int, float)
    if left is _SKIP or right is _SKIP:
        return _SKIP
    if not isinstance(left, numeric) or not isinstance(right, numeric):
        return _SKIP
    if isinstance(left, bool) or isinstance(right, bool):
        return _SKIP
    if op == "+":
        return left + right
    if op == "-":
        return left - right
    if op == "*":
        return left * right
    if op == "/":
        return left / right
    if op == "%":
        return left % right
    return float(left) ** float(right)


def parse_config_source(source: str) -> tuple[dict[str, Any], list[str]]:
    """Acha `local Config = {` no texto Luau e devolve (valores, chaves ignoradas)."""
    clean = strip_comments(source)
    match = re.search(r"\blocal\s+Config\s*(?::[^=]+)?=\s*\{", clean)
    if not match:
        raise ValueError("não achei `local Config = {` no arquivo")
    start = match.end() - 1
    parser = _Parser(_tokenize(clean[start:]))
    table = parser.parse_table()
    if not isinstance(table, dict):
        raise ValueError("a tabela Config não tem chaves nomeadas")
    return table, parser.skipped


def load_config(path: str | Path | None = None) -> ConfigData:
    """Lê o Config.luau (padrão: `src/shared/Config.luau` deste repositório)."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    raw = config_path.read_bytes()
    values, skipped = parse_config_source(raw.decode("utf-8"))
    return ConfigData(
        values=values,
        path=config_path,
        sha256=hashlib.sha256(raw).hexdigest(),
        skipped=skipped,
    )


if __name__ == "__main__":
    import json

    data = load_config()
    print(json.dumps(data.values, indent=2, ensure_ascii=False, default=list))
    print(f"# sha256 {data.sha256}; ignoradas: {len(data.skipped)}")
