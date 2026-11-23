"""Testes da spec training-record-and-plots. Rodam sem janela: python -m pytest test_registro.py -v"""

import os

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
