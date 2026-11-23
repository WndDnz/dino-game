"""Testes da spec training-record-and-plots. Rodam sem janela: python -m pytest test_registro.py -v"""

import os
import random

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["MPLBACKEND"] = "Agg"

import numpy as np  # noqa: E402
import pytest  # noqa: E402

import AGMLP  # noqa: E402
import RedeNeural  # noqa: E402

CFG = (5, 8, 4, 2)


def _rede(valor_por_gene):
    """Rede (5, 8, 4, 2) com todos os genes iguais a `valor_por_gene` (ou definidos por funcao do indice)."""
    rede = RedeNeural.RedeNeural(CFG)
    i = 0
    for a in rede.pesos + rede.bias:
        for idx in np.ndindex(a.shape):
            a[idx] = valor_por_gene(i) if callable(valor_por_gene) else valor_por_gene
            i += 1
    return rede


def test_diversidade_media_do_desvio_por_gene():
    iguais = [_rede(0.3) for _ in range(5)]
    assert AGMLP.diversidade(iguais) == 0.0
    # dois individuos que diferem de 2.0 em todo gene: desvio populacional 1.0 em cada um
    assert AGMLP.diversidade([_rede(0.0), _rede(2.0)]) == pytest.approx(1.0)
    # 3 redes: gene i vale i, 2i e 3i -> desvio de cada gene e i * std([1, 2, 3])
    redes = [_rede(lambda i, k=k: k * i) for k in (1, 2, 3)]
    n_genes = sum(a.size for a in redes[0].pesos + redes[0].bias)
    assert n_genes == 94
    esperado = np.mean([i * np.std([1, 2, 3]) for i in range(n_genes)])
    assert AGMLP.diversidade(redes) == pytest.approx(esperado)


def _ag():
    return AGMLP.RNA_AG(CFG, None, 0.1, 50, 1, taxaMutacao=0.05, elite=0.1)


def test_hiperparametros_do_ag_sao_as_constantes(monkeypatch):
    assert (AGMLP.SIGMA_MUTACAO, AGMLP.TORNEIO, AGMLP.ALPHA_BLX) == (0.5, 3, 0.1)
    ag = _ag()
    ranqueada = [(i, i) for i in range(99, -1, -1)]
    # TORNEIO = 1: cada "torneio" e um sorteio simples, sem preferencia pelo melhor
    monkeypatch.setattr(AGMLP, "TORNEIO", 1)
    random.seed(0)
    assert 0.47 < np.mean(ag.selecao(ranqueada, 5000)) / 99 < 0.53
    # SIGMA_MUTACAO = 2.0: o desvio dos deltas acompanha
    monkeypatch.setattr(AGMLP, "SIGMA_MUTACAO", 2.0)
    np.random.seed(0)
    deltas = []
    for _ in range(20):
        rede = RedeNeural.RedeNeural(CFG)
        antes = [a.copy() for a in rede.pesos + rede.bias]
        ag.aplicaMutacao(rede, 1.0)
        deltas += [(d - a).ravel() for a, d in zip(antes, rede.pesos + rede.bias)]
    assert 1.8 < np.concatenate(deltas).std() < 2.2
    # ALPHA_BLX = 0: o filho fica entre os pais em todo gene
    monkeypatch.setattr(AGMLP, "ALPHA_BLX", 0.0)
    for _ in range(50):
        p1, p2 = RedeNeural.RedeNeural(CFG), RedeNeural.RedeNeural(CFG)
        f = ag.acasala(p1, p2)
        for a, b, c in zip(p1.pesos + p1.bias, p2.pesos + p2.bias, f.pesos + f.bias):
            assert np.all(c >= np.minimum(a, b) - 1e-12) and np.all(c <= np.maximum(a, b) + 1e-12)
