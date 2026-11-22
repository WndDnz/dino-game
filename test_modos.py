"""Testes da spec headless-training-and-watch. Rodam sem janela: python -m pytest test_modos.py -v"""

import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import numpy as np  # noqa: E402
import pygame  # noqa: E402
import pytest  # noqa: E402

import DinoGame  # noqa: E402
import RedeNeural  # noqa: E402

CFG = (5, 8, 4, 2)


@pytest.fixture
def jogo():
    """Tela dummy, sem som, e grupos de sprites vazios."""
    pygame.init()  # um teste anterior pode ter encerrado o pygame
    pygame.mixer.quit()
    j = DinoGame.DinoGame()
    DinoGame.Cactus.containers = pygame.sprite.Group()
    DinoGame.Ptera.containers = pygame.sprite.Group()
    DinoGame.Cloud.containers = pygame.sprite.Group()
    return j


def _mesma_mascara(sprite):
    esperada = pygame.mask.from_surface(sprite.image)
    return (
        sprite.mask.get_size() == esperada.get_size()
        and sprite.mask.count() == esperada.count()
        and sprite.mask.overlap_area(esperada, (0, 0)) == esperada.count()
    )


def test_mascara_em_cache_igual_a_da_imagem(jogo):
    dino = DinoGame.Dino(44, 47)
    assert _mesma_mascara(dino)  # recem-criado
    for _ in range(12):  # em pe, correndo: a imagem alterna
        dino.update()
        assert _mesma_mascara(dino)
    dino.isDucking = True
    for _ in range(12):  # abaixado: outra folha de sprites
        dino.update()
        assert _mesma_mascara(dino)
    assert dino.mask.get_size() == (59, 47)
    dino.isDucking, dino.isDead = False, True
    dino.update()
    assert _mesma_mascara(dino)
    for _ in range(5):  # cacto: uma de 3 imagens, sorteada
        assert _mesma_mascara(DinoGame.Cactus(4, 40, 40))
    ptera = DinoGame.Ptera(4, 46, 40)
    for _ in range(25):  # ptera: bate asas a cada 10 frames
        ptera.update()
        assert _mesma_mascara(ptera)


def test_sprites_carregados_uma_vez(jogo, monkeypatch):
    carregadas = []
    load = pygame.image.load

    def conta(nome, *args):
        carregadas.append(nome)
        return load(nome, *args)

    monkeypatch.setattr(pygame.image, "load", conta)
    dinos = [DinoGame.Dino(44, 47) for _ in range(50)]
    assert len(carregadas) <= 2  # dino.png e dino_ducking.png, uma vez cada
    assert len({id(d.rect) for d in dinos}) == 50  # cada dino com o seu proprio rect


def test_lote_igual_ao_individual():
    np.random.seed(3)
    redes = [RedeNeural.RedeNeural(CFG) for _ in range(50)]
    entradas = np.random.uniform(-1, 1, (50, 5, 1))  # uma entrada diferente por rede
    W, B = RedeNeural.RedeNeural.empilha(redes)
    lote = RedeNeural.RedeNeural.feed_forward_lote(W, B, entradas)
    assert lote.shape == (50, 2, 1)
    for rede, entrada, saida in zip(redes, entradas, lote):
        assert np.allclose(saida, rede.feedForward(entrada), rtol=0, atol=1e-12)
    # so as redes ainda vivas: indices 3, 17 e 40
    vivos = [3, 17, 40]
    parte = RedeNeural.RedeNeural.feed_forward_lote(
        [w[vivos] for w in W], [b[vivos] for b in B], entradas[vivos]
    )
    for i, saida in zip(vivos, parte):
        assert np.allclose(saida, redes[i].feedForward(entradas[i]), rtol=0, atol=1e-12)
