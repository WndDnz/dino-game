"""Testes da spec headless-training-and-watch. Rodam sem janela: python -m pytest test_modos.py -v"""

import os
import random

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


def _percorre(semente, frames):
    """Roda uma Pista. Devolve (pista, novos), com novos = [(frame, obstaculo, outros na tela)].

    Cada obstaculo novo ganha `.distancias`: da borda esquerda dele a borda direita de cada
    outro, medidas no frame da criacao. Cada frame entra em `pista.historico` como
    (cactos na tela, velocidade, contador).
    """
    random.seed(semente)
    pista = DinoGame.Pista()
    pista.historico = []
    novos, antes = [], set()
    for _ in range(frames):
        frame = pista.counter
        pista.passo()
        agora = set(pista.cacti) | set(pista.pteras)
        for o in agora - antes:
            outros = [x for x in agora if x is not o]
            o.distancias = [o.rect.left - x.rect.right for x in outros]
            novos.append((frame, o, outros))
        antes = agora
        pista.historico.append((len(pista.cacti), pista.gamespeed, pista.counter))
    return pista, novos


def test_obstaculo_novo_a_160_px(jogo):
    cactos = pteras = cacto_com_ptera_na_tela = 0
    for semente in range(20):
        pista, novos = _percorre(semente, 5000)
        for frame, o, outros in novos:
            assert all(d >= 160 for d in o.distancias), (semente, frame, o.distancias)
            if isinstance(o, DinoGame.Ptera):
                pteras += 1
            else:
                cactos += 1
                cacto_com_ptera_na_tela += any(isinstance(x, DinoGame.Ptera) for x in outros)
    # o teste so vale se as situacoes de risco aconteceram
    assert cactos > 500 and pteras > 20 and cacto_com_ptera_na_tela > 5


def test_pista_regras_do_jogo_manual(jogo):
    for semente in range(20):
        pista, novos = _percorre(semente, 5000)
        assert max(n for n, _, _ in pista.historico) == 2  # ate 2 cactos, nunca 3
        for cactos, velocidade, contador in pista.historico:
            assert velocidade == 4 + contador // 700  # 4 no inicio, +1 a cada 700 frames
        for frame, o, _ in novos:
            if isinstance(o, DinoGame.Ptera):
                assert frame > 700
                assert o.rect.size == (46, 40)
            else:
                assert o.rect.size == (40, 40)


def _cacto(esquerda):
    c = DinoGame.Cactus(4, 40, 40)
    c.rect.left = esquerda
    return c


def _l(dino, cactos):
    return DinoGame.sensores(dino, DinoGame.cacto_a_frente(dino, cactos), None, 4)[0][0]


def test_sensor_mede_cacto_mais_proximo_a_frente(jogo):
    dino = DinoGame.Dino(44, 47)
    assert (dino.rect.left, dino.rect.right) == (40, 84)
    passado, perto, longe = _cacto(-10), _cacto(284), _cacto(484)  # perto: 200 px a frente
    assert passado.rect.right < dino.rect.left
    for cactos in ([passado, perto, longe], [longe, perto, passado], [perto, longe, passado]):
        assert _l(dino, cactos) == pytest.approx(200 / 600)
    assert _l(dino, [longe, passado]) == pytest.approx(400 / 600)
    # passando por baixo do dino (ainda nao saiu por tras) continua sendo o medido
    embaixo = _cacto(60)
    assert _l(dino, [embaixo, perto]) == pytest.approx((60 - 84) / 600)


def test_sensor_vale_1_quando_cactos_passaram(jogo):
    dino = DinoGame.Dino(44, 47)
    assert _l(dino, [_cacto(-30), _cacto(-5)]) == 1.0  # bordas direitas em 10 e 35, antes de 40
    assert _l(dino, []) == 1.0
    no_limite = _cacto(0)  # borda direita em 40, igual a borda esquerda do dino: ainda nao passou
    assert no_limite.rect.right == dino.rect.left
    assert _l(dino, [no_limite]) == pytest.approx((0 - 84) / 600)
    assert _l(dino, [_cacto(-1)]) == 1.0  # um pixel depois, passou


class _Fim(Exception):
    pass


class _Relogio:
    """No lugar de pygame.time.Clock: nao espera, so anota o FPS pedido."""

    def __init__(self):
        self.fps = []

    def tick(self, fps=0):
        self.fps.append(fps)


def _grava_pista(monkeypatch, frames):
    """Espiona Pista.passo: devolve o log [(frame, tipo, x, y)] dos obstaculos criados e
    levanta _Fim quando a pista chega a `frames` frames."""
    log, vistos = [], set()
    passo = DinoGame.Pista.passo

    def espia(self):
        frame = self.counter
        passo(self)
        for o in (*self.cacti, *self.pteras):
            if o not in vistos:
                vistos.add(o)
                log.append((frame, type(o).__name__, o.rect.x, o.rect.y))
        if self.counter >= frames:
            raise _Fim

    monkeypatch.setattr(DinoGame.Pista, "passo", espia)
    return log


def _pista_sozinha(monkeypatch, semente, frames):
    log = _grava_pista(monkeypatch, frames)
    random.seed(semente)
    pista = DinoGame.Pista()
    with pytest.raises(_Fim):
        while True:
            pista.passo()
    return list(log)


def _sem_colisao(monkeypatch):
    monkeypatch.setattr(pygame.sprite, "collide_mask", lambda a, b: None)


def test_jogo_manual_usa_a_pista(jogo, monkeypatch):
    esperado = _pista_sozinha(monkeypatch, 11, 1500)
    assert len(esperado) > 10 and any(tipo == "Ptera" for _, tipo, _, _ in esperado)
    log = _grava_pista(monkeypatch, 1500)
    _sem_colisao(monkeypatch)
    jogo.clock = _Relogio()
    random.seed(11)
    with pytest.raises(_Fim):
        jogo.gameplay()
    assert log == esperado
