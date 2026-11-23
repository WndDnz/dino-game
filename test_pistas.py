"""Testes da spec fixed-test-tracks. Rodam sem janela: python -m pytest test_pistas.py -v"""

import csv
import json
import os
import random

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["MPLBACKEND"] = "Agg"

import numpy as np  # noqa: E402
import pygame  # noqa: E402
import pytest  # noqa: E402

import DinoGame  # noqa: E402
import RedeNeural  # noqa: E402

CFG = (5, 8, 4, 2)


@pytest.fixture
def jogo():
    """Tela dummy, sem som, relogio que nao espera."""
    pygame.init()
    pygame.mixer.quit()
    j = DinoGame.DinoGame()

    class _Relogio:
        def tick(self, fps=0):
            pass

    j.clock = _Relogio()
    return j


def _rede_fixa(pula):
    """Pesos zero: a saida so depende do bias da ultima camada."""
    rede = RedeNeural.RedeNeural(CFG)
    for a in rede.pesos + rede.bias:
        a[:] = 0.0
    rede.bias[-1][:] = [[10.0 if pula else -10.0], [-10.0]]
    return rede


def _redes(n, semente=0):
    np.random.seed(semente)
    return [RedeNeural.RedeNeural(CFG) for _ in range(n)]


# ---- T1: teto de frames ------------------------------------------------------


def test_teto_de_frames(jogo, monkeypatch):
    assert DinoGame.LIMITE_FRAMES == 14000
    # pista sem obstaculos: ninguem morre, so o teto encerra a partida
    monkeypatch.setattr(DinoGame.Pista, "_cabe", lambda self, largura: False)
    for teto, score in ((70, 10), (71, 10), (77, 11)):
        monkeypatch.setattr(DinoGame, "LIMITE_FRAMES", teto)
        redes = [_rede_fixa(pula=False) for _ in range(3)]
        ranked = jogo.roda_geracao(redes, janela=False)
        e = jogo.estatisticas
        assert e["frames"] == teto
        assert [s for s, _ in ranked] == [score] * 3  # 1 ponto a cada 7 frames
        assert [id(r) for _, r in ranked] == [id(r) for r in redes]
        assert e["mortes_cacto"] + e["mortes_ptera"] == 0
        assert e["obstaculos"] == [0, 0, 0]
        assert jogo.dinoArray == []
    # pista real: quem morre antes do teto fica com o score da morte
    monkeypatch.undo()
    random.seed(4)
    ((score_morte, _),) = jogo.roda_geracao([_rede_fixa(pula=False)], janela=False)
    frames_morte = jogo.estatisticas["frames"]
    assert jogo.estatisticas["mortes_cacto"] == 1 and frames_morte > 50
    monkeypatch.setattr(DinoGame, "LIMITE_FRAMES", frames_morte + 50)
    random.seed(4)
    assert jogo.roda_geracao([_rede_fixa(pula=False)], janela=False)[0][0] == score_morte
    assert (jogo.estatisticas["frames"], jogo.estatisticas["mortes_cacto"]) == (frames_morte, 1)
    # e o teto antes da morte encerra a partida com o dino vivo
    monkeypatch.setattr(DinoGame, "LIMITE_FRAMES", frames_morte - 10)
    random.seed(4)
    assert jogo.roda_geracao([_rede_fixa(pula=False)], janela=False)[0][0] == (frames_morte - 10) // 7
    assert (jogo.estatisticas["frames"], jogo.estatisticas["mortes_cacto"]) == (frames_morte - 10, 0)
