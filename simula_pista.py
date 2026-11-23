#!/usr/bin/python3
"""
Investiga se a pista gera situações impossíveis.

Para cada semente, roda a Pista real e, em paralelo, mantém TODOS os estados que um
dino poderia ter (busca exaustiva sobre pular/abaixar a cada frame, com a física e
as máscaras de colisão do próprio jogo). Quando nenhum estado sobrevive, a pista é
impossível naquele frame: nenhum dino, por melhor que seja, passaria dali.

    python simula_pista.py                       # sementes 1..200
    python simula_pista.py --treino treinos/X    # as pistas daquele treino (semente + 1, + 2...)
"""
import argparse
import collections
import copy
import csv
import json
import os
import random
import statistics

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame  # noqa: E402

import DinoGame as dg  # noqa: E402

ACOES = [(p, a) for p in (0, 1) for a in (0, 1)]  # (pular, abaixar)


def chave(d):
    return (d.rect.y, d.rect.width, round(d.movement[1], 4), d.isJumping, d.index, d.isDucking)


def clona(d):
    c = copy.copy(d)
    c.rect = d.rect.copy()
    c.movement = list(d.movement)
    return c


def nome(o):
    return "ptera" if isinstance(o, dg.Ptera) else "cacto"


def resolve(semente, max_frames):
    """Devolve (frame_limite ou None, info da morte, [(velocidade, par, gap)] dos nascimentos)."""
    random.seed(semente)
    pista = dg.Pista()
    inicial = dg.Dino(44, 47)
    estados = {chave(inicial): inicial}
    transicao = {}  # (chave, acao, t % 5) -> dino resultante; o dino não depende da pista
    vistos, ultimo, nascimentos, gap_de = {}, None, [], {}  # vistos guarda o objeto: id() não é reutilizado

    for t in range(max_frames):
        obstaculos = [*pista.cacti, *pista.pteras]
        for o in obstaculos:  # registra o espaço deixado para cada obstáculo novo
            if id(o) not in vistos:
                vistos[id(o)] = o
                if ultimo is not None and ultimo.alive():
                    gap_de[id(o)] = (pista.gamespeed, f"{nome(ultimo)}->{nome(o)}", o.rect.left - ultimo.rect.right)
                    nascimentos.append(gap_de[id(o)])
                ultimo = o

        vivos, assassinos = {}, collections.Counter()
        for k, d in estados.items():
            bateu = [o for o in obstaculos if pygame.sprite.collide_mask(d, o)]
            if bateu:
                assassinos[bateu[0]] += 1
            else:
                vivos[k] = d
        if not vivos:
            o = assassinos.most_common(1)[0][0]
            vel, par, gap = gap_de.get(id(o), (pista.gamespeed, f"sozinho->{nome(o)}", None))
            return t, {"velocidade": pista.gamespeed, "par": par, "gap": gap,
                       "altura_ptera": o.rect.bottom if nome(o) == "ptera" else None}, nascimentos

        estados = {}
        for k, d in vivos.items():
            for acao in ACOES:
                tk = (k, acao, t % 5)
                novo = transicao.get(tk)
                if novo is None:
                    novo = clona(d)
                    novo.counter = t  # só t % 5 importa: escolhe o quadro da animação
                    novo.agir([[acao[0]], [acao[1]]])
                    novo.update()
                    transicao[tk] = novo
                estados[chave(novo)] = novo
        pista.passo()
    return None, None, nascimentos


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sementes", type=int, default=200, help="quantas pistas (padrão 200)")
    ap.add_argument("--semente", type=int, default=0, help="semente base, como no treino")
    ap.add_argument("--treino", help="pasta de um treino: usa a semente dele; em treino antigo, de uma pista por geração, compara com o fitness.csv")
    ap.add_argument("--max-frames", type=int, default=14000, help="teto da simulação (14000 = score 2000)")
    ap.add_argument("--saida", default="pistas.csv")
    args = ap.parse_args(argv)

    melhores = {}
    if args.treino:
        with open(os.path.join(args.treino, "config.json")) as f:
            config = json.load(f)
        args.semente = config["semente"]
        # treino antigo (sem "pistas"): a geração g correu na pista semente + g, então dá
        # para comparar o melhor dela com o limite da pista. Com pistas fixas (AD-009) a
        # pista i é a i-ésima de treino e "melhor" é uma média: não há o que comparar.
        if "pistas" not in config:
            with open(os.path.join(args.treino, "fitness.csv")) as f:
                melhores = {int(l["geracao"]): int(l["melhor"]) for l in csv.DictReader(f)}

    dg.DinoGame()  # cria a tela (dummy) para carregar os sprites
    linhas, gaps = [], []
    for g in range(1, args.sementes + 1):
        limite, info, nasc = resolve(args.semente + g, args.max_frames)
        gaps += nasc
        info = info or {}
        linhas.append({"geracao": g, "limite_frames": limite, "limite_score": limite // 7 if limite else None,
                       **{c: info.get(c) for c in ("velocidade", "par", "gap", "altura_ptera")},
                       "melhor_do_treino": melhores.get(g)})
        print(f"\r{g}/{args.sementes}", end="", flush=True)
    print()

    with open(args.saida, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    mortas = [l for l in linhas if l["limite_frames"]]
    print(f"Pistas impossíveis antes do score {args.max_frames // 7}: {len(mortas)} de {len(linhas)}")
    if mortas:
        s = sorted(l["limite_score"] for l in mortas)
        print(f"Score máximo possível: mín {s[0]}, mediana {statistics.median(s)}, máx {s[-1]}")
        print("\nOnde a pista fica impossível (velocidade, situação -> nº de pistas, gaps em px):")
        causas = collections.defaultdict(list)
        for l in mortas:
            causas[(l["velocidade"], l["par"])].append(l["gap"])
        for (vel, par), gs in sorted(causas.items()):
            gs = [x for x in gs if x is not None]
            faixa = f"gap {min(gs)}..{max(gs)}" if gs else ""
            print(f"  vel {vel:2d}  {par:14s} {len(causas[(vel, par)]):4d}  {faixa}")
    print("\nEspaço deixado para cada obstáculo novo (px), por situação:")
    por_par = collections.defaultdict(list)
    for _, par, gap in gaps:
        por_par[par].append(gap)
    for par, gs in sorted(por_par.items()):
        print(f"  {par:14s} n={len(gs):6d}  mín {min(gs)}  mediana {statistics.median(gs)}  máx {max(gs)}")
    if melhores:
        com = [l for l in mortas if l["melhor_do_treino"] is not None]
        acima = [l for l in com if l["melhor_do_treino"] > l["limite_score"] + 1]
        colados = [l for l in com if l["melhor_do_treino"] >= l["limite_score"] - 1]
        print(f"\nTreino: melhor dino acima do limite calculado em {len(acima)} gerações (deve ser 0)")
        print(f"Treino: melhor dino morreu no limite da pista em {len(colados)} de {len(com)} gerações")
    print(f"\nDetalhe por pista: {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
