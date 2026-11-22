"""Testes da spec ga-training-fixes. Rodam sem janela: python -m pytest test_ga.py -v"""

import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import numpy as np  # noqa: E402
import pygame  # noqa: E402

import AGMLP  # noqa: E402
import DinoGame  # noqa: E402
import RedeNeural  # noqa: E402


def test_importa_sem_janela():
    DinoGame.DinoGame()
    assert pygame.display.get_driver() == "dummy"
    assert AGMLP.RNA_AG and RedeNeural.RedeNeural


CFG = (5, 8, 4, 2)


def _genes(redes, attr):
    return np.concatenate([a.ravel() for r in redes for a in getattr(r, attr)])


def test_init_normal_0_1():
    np.random.seed(0)
    redes = [RedeNeural.RedeNeural(CFG) for _ in range(350)]
    pesos, bias = _genes(redes, "pesos"), _genes(redes, "bias")
    assert -0.05 < pesos.mean() < 0.05
    assert 0.95 < pesos.std() < 1.05
    assert -0.1 < bias.mean() < 0.1
    assert 0.9 < bias.std() < 1.1
