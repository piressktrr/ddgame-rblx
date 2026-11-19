# Versões e rollback

Cada versão estável da `main` recebe uma **tag anotada** `vMAJOR.MINOR.PATCH`.

| Mudança | Exemplo |
|---|---|
| PATCH: correção sem mudar jogabilidade | `v0.1.0` → `v0.1.1` |
| MINOR: mecânica, fase ou mapa novo | `v0.1.1` → `v0.2.0` |
| MAJOR: lançamento público / quebra de save | `v0.x` → `v1.0.0` |

## Fluxo

1. Trabalho em branch própria (`feature/...`, `fix/...`, `chore/...`), commits locais.
2. Revisão → push → PR → merge na `main`.
3. Depois do merge, tag na `main`:

```powershell
git switch main
git pull
git tag -a v0.2.0 -m "v0.2.0: resumo"
git push origin v0.2.0
```

## Voltar para uma versão

```powershell
git tag -n1                                  # lista as versões
git switch -c volta-v0.1.0 v0.1.0            # abre a versão numa branch, sem mexer na main
```

Com o `rojo serve` rodando, o Studio recebe o código daquela versão. O mapa vem do
`place/RaceAndEscape.rbxl` da mesma versão (reabra o arquivo no Studio).

Para desfazer um merge já na `main` sem reescrever histórico:

```powershell
git revert -m 1 <hash-do-merge>
```

## Versões

| Tag | Commit | Conteúdo |
|---|---|---|
| `v0.1.0` | `c51bffc` | Fase 3 (zonas, corrida, HUD), mapa da Fase 2, tutorial do gancho |
