"""Testes da spec ga-training-fixes. Rodam sem janela: python -m pytest test_ga.py -v"""

import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame  # noqa: E402

import AGMLP  # noqa: E402
import DinoGame  # noqa: E402
import RedeNeural  # noqa: E402


def test_importa_sem_janela():
    DinoGame.DinoGame()
    assert pygame.display.get_driver() == "dummy"
    assert AGMLP.RNA_AG and RedeNeural.RedeNeural
