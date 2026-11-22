"""Testes da spec ga-training-fixes. Rodam sem janela: python -m pytest test_ga.py -v"""

import os
import random

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


def _ag(n=50, elite=0.1):
    return AGMLP.RNA_AG(CFG, None, 0.1, n, 1, taxaMutacao=0.05, elite=elite)


def _copia(rede):
    return [a.copy() for a in rede.bias + rede.pesos]


def test_mutacao_taxa_1_altera_todos():
    rede = RedeNeural.RedeNeural(CFG)
    antes = _copia(rede)
    _ag().aplicaMutacao(rede, 1.0)
    for a, d in zip(antes, rede.bias + rede.pesos):
        assert np.all(a != d)


def test_mutacao_taxa_0_nao_altera():
    rede = RedeNeural.RedeNeural(CFG)
    antes = _copia(rede)
    _ag().aplicaMutacao(rede, 0.0)
    for a, d in zip(antes, rede.bias + rede.pesos):
        assert np.array_equal(a, d)


def test_mutacao_delta_normal_0_05():
    np.random.seed(1)
    ag, deltas = _ag(), []
    for _ in range(20):  # 20 redes x 94 genes = 1880 genes
        rede = RedeNeural.RedeNeural(CFG)
        antes = _copia(rede)
        ag.aplicaMutacao(rede, 1.0)
        deltas += [(d - a).ravel() for a, d in zip(antes, rede.bias + rede.pesos)]
    deltas = np.concatenate(deltas)
    assert deltas.size >= 1000
    assert -0.1 < deltas.mean() < 0.1
    assert 0.4 < deltas.std() < 0.6
    assert (deltas > 0).any() and (deltas < 0).any()
    # forma de normal com desvio 0.5: ~68.3% dos deltas dentro de 1 desvio, ~50% de cada sinal
    assert 0.63 < np.mean(np.abs(deltas) < 0.5) < 0.73
    assert 0.45 < np.mean(deltas > 0) < 0.55


def test_torneio_de_3():
    random.seed(2)
    ranqueada = [(i, i) for i in range(99, -1, -1)]  # (indice, score), 100 scores distintos
    vencedores = _ag().selecao(ranqueada, 5000)
    assert len(vencedores) == 5000
    # maximo de 3 sorteados entre 100: posicao media esperada 0.75 da escala
    assert 0.72 < np.mean(vencedores) / 99 < 0.78


def test_torneio_populacao_menor_que_3():
    ranqueada = [(1, 9.0), (0, 2.0)]
    assert _ag().selecao(ranqueada, 50) == [1] * 50


def _geracao(n=50):
    """n pares (score, rede) com scores distintos; a rede de indice i tem score i."""
    return [(float(i), RedeNeural.RedeNeural(CFG)) for i in range(n)]


def _iguais(a, b):
    return all(np.array_equal(x, y) for x, y in zip(a.bias + a.pesos, b.bias + b.pesos))


def test_proxima_geracao_devolve_n(capsys):
    nova = _ag(50).proximaGeracao(_geracao(50))
    assert len(nova) == 50
    assert all(isinstance(r, RedeNeural.RedeNeural) for r in nova)


def test_elite_identica(capsys):
    ag = _ag(50, elite=0.1)
    ag.taxaMutacao = 1.0  # qualquer mutacao que vaze para a elite aparece
    atual = _geracao(50)
    nova = ag.proximaGeracao(atual)
    melhores = [rede for _, rede in atual[-5:]]  # scores 45..49
    for melhor in melhores:
        copias = [r for r in nova if _iguais(r, melhor)]
        assert len(copias) == 1
        assert copias[0] is not melhor


def test_entrada_inalterada(capsys):
    ag = _ag(50, elite=0.1)
    ag.taxaMutacao = 1.0
    atual = _geracao(50)
    antes = [_copia(rede) for _, rede in atual]
    ag.proximaGeracao(atual)
    for a, (_, rede) in zip(antes, atual):
        assert all(np.array_equal(x, y) for x, y in zip(a, rede.bias + rede.pesos))


def test_sem_elite_gera_n_filhos(capsys):
    ag = _ag(50, elite=0.01)
    assert ag.tamElite == 0
    atual = _geracao(50)
    nova = ag.proximaGeracao(atual)
    assert len(nova) == 50
    assert not any(r is rede for r in nova for _, rede in atual)
