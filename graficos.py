#!/usr/bin/python3
"""Gráficos de um ou mais treinos a partir do fitness.csv de cada pasta.

Uso: python graficos.py <pasta> [<pasta> ...] [--mostrar]
"""

import argparse
import csv
import os
import sys


def le(pasta):
    """Linhas do fitness.csv da pasta como listas de números por coluna, ou levanta FileNotFoundError."""
    with open(os.path.join(pasta, "fitness.csv"), newline="") as f:
        linhas = list(csv.DictReader(f))
    colunas = linhas[0].keys() if linhas else []
    return {c: [float(l[c]) for l in linhas] for c in colunas}


def _figura(titulo, ylabel, xlabel="geração"):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.set_title(titulo)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.3)
    return fig, ax


def aptidao(d):
    import numpy as np

    fig, ax = _figura("Aptidão por geração", "score")
    g = d["geracao"]
    media, desvio = np.array(d["media"]), np.array(d.get("desvio", [0.0] * len(g)))
    if "desvio" in d:
        ax.fill_between(g, media - desvio, media + desvio, alpha=0.2, label="média ± desvio")
    ax.plot(g, d["melhor"], label="melhor")
    if "mediana" in d:
        ax.plot(g, d["mediana"], label="mediana")
    ax.plot(g, d["media"], label="média")
    if "pior" in d:
        ax.plot(g, d["pior"], label="pior")
    ax.legend()
    return fig


def aptidao_por_frames(d):
    import numpy as np

    fig, ax = _figura("Aptidão pelo custo de simulação", "score", "frames simulados (acumulado)")
    x = np.cumsum(d["frames"])
    ax.plot(x, d["melhor"], label="melhor")
    ax.plot(x, d["media"], label="média")
    ax.legend()
    return fig


def mortes(d):
    fig, ax = _figura("Mortes por tipo de obstáculo", "dinos")
    ax.bar(d["geracao"], d["mortes_cacto"], label="cacto")
    ax.bar(d["geracao"], d["mortes_ptera"], bottom=d["mortes_cacto"], label="ptera")
    ax.legend()
    return fig


def obstaculos(d):
    fig, ax = _figura("Obstáculos vencidos", "obstáculos")
    ax.plot(d["geracao"], d["obstaculos_melhor"], label="melhor")
    ax.plot(d["geracao"], d["obstaculos_media"], label="média")
    ax.legend()
    return fig


def diversidade(d):
    fig, ax = _figura("Diversidade da população", "média do desvio por gene")
    ax.plot(d["geracao"], d["diversidade"], label="diversidade")
    return fig


def comparacao(treinos):
    """`treinos`: lista de (nome, dados). Uma curva de média por treino."""
    fig, ax = _figura("Comparação entre treinos: média por geração", "score")
    for nome, d in treinos:
        ax.plot(d["geracao"], d["media"], label=nome)
    ax.legend()
    return fig


# arquivo -> (função, colunas que ela precisa)
GRAFICOS = {
    "aptidao.png": (aptidao, {"geracao", "melhor", "media"}),
    "aptidao_por_frames.png": (aptidao_por_frames, {"melhor", "media", "frames"}),
    "mortes.png": (mortes, {"geracao", "mortes_cacto", "mortes_ptera"}),
    "obstaculos.png": (obstaculos, {"geracao", "obstaculos_melhor", "obstaculos_media"}),
    "diversidade.png": (diversidade, {"geracao", "diversidade"}),
}


def main(argv=None):
    """Grava os gráficos e devolve o código de saída."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pastas", nargs="+", metavar="PASTA")
    parser.add_argument("--mostrar", action="store_true", help="abre os gráficos depois de gravá-los")
    args = parser.parse_args(argv)

    import matplotlib

    if not args.mostrar:
        matplotlib.use("Agg")  # só grava arquivos, nenhuma janela
    import matplotlib.pyplot as plt

    treinos = []
    for pasta in args.pastas:
        try:
            dados = le(pasta)
        except FileNotFoundError:
            print(f"Sem fitness.csv em: {pasta}")
            return 1
        if not dados:
            print(f"Sem gerações em: {pasta}")
            return 1
        treinos.append((os.path.basename(os.path.normpath(pasta)), dados))
        for arquivo, (grafico, colunas) in GRAFICOS.items():
            if not colunas <= dados.keys():
                print(f"Gráfico pulado, faltam colunas: {arquivo}")
                continue
            fig = grafico(dados)
            fig.savefig(os.path.join(pasta, arquivo), dpi=120, bbox_inches="tight")
            if not args.mostrar:
                plt.close(fig)

    if len(treinos) > 1:
        fig = comparacao(treinos)
        fig.savefig("comparacao.png", dpi=120, bbox_inches="tight")
        if not args.mostrar:
            plt.close(fig)

    if args.mostrar:
        plt.show()
    return 0


if __name__ == "__main__":
    sys.exit(main())
