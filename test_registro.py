"""Testes da spec training-record-and-plots. Rodam sem janela: python -m pytest test_registro.py -v"""

import os
import random

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["MPLBACKEND"] = "Agg"

import numpy as np  # noqa: E402
import pygame  # noqa: E402
import pytest  # noqa: E402

import AGMLP  # noqa: E402
import DinoGame  # noqa: E402
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


def _espia_passos(monkeypatch):
    """Grava, depois de cada passo da pista, os ids dos obstaculos com a borda direita antes de x=40
    (a borda esquerda dos dinos). Devolve a lista de conjuntos, uma por passo."""
    passos = []
    passo = DinoGame.Pista.passo

    def espia(self):
        passo(self)
        passos.append({id(o) for o in (*self.cacti, *self.pteras) if o.rect.right < 40})

    monkeypatch.setattr(DinoGame.Pista, "passo", espia)
    return passos


def _so_ptera_colide(monkeypatch):
    colide = pygame.sprite.collide_mask
    monkeypatch.setattr(
        pygame.sprite, "collide_mask", lambda a, b: colide(a, b) if isinstance(b, DinoGame.Ptera) else None
    )


def test_frames_da_geracao(jogo, monkeypatch):
    passos = _espia_passos(monkeypatch)
    random.seed(3)
    np.random.seed(3)
    jogo.roda_geracao([RedeNeural.RedeNeural(CFG) for _ in range(10)], janela=False)
    assert jogo.estatisticas["frames"] == len(passos) > 100


def test_obstaculos_vencidos_por_dino(jogo, monkeypatch):
    assert DinoGame.Dino(44, 47).rect.left == 40
    # redes iguais que nunca pulam e so morrem em ptera: atravessam os cactos e vencem cada um
    _so_ptera_colide(monkeypatch)
    passos = _espia_passos(monkeypatch)
    random.seed(5)
    ranked = jogo.roda_geracao([_rede_fixa(pula=False) for _ in range(4)], janela=False)
    vencidos = len(set().union(*passos))  # obstaculos que passaram enquanto havia dino vivo
    assert vencidos >= 3
    assert len(ranked) == 4
    assert jogo.estatisticas["obstaculos"] == [vencidos] * 4
    # com colisao normal, redes que nunca pulam morrem no primeiro cacto: 0 obstaculos
    monkeypatch.undo()
    random.seed(5)
    jogo.roda_geracao([_rede_fixa(pula=False) for _ in range(4)], janela=False)
    assert jogo.estatisticas["obstaculos"] == [0, 0, 0, 0]


def test_mortes_por_tipo_de_obstaculo(jogo, monkeypatch):
    random.seed(7)
    jogo.roda_geracao([_rede_fixa(pula=False) for _ in range(6)], janela=False)
    assert (jogo.estatisticas["mortes_cacto"], jogo.estatisticas["mortes_ptera"]) == (6, 0)
    _so_ptera_colide(monkeypatch)
    random.seed(7)
    jogo.roda_geracao([_rede_fixa(pula=False) for _ in range(6)], janela=False)
    assert (jogo.estatisticas["mortes_cacto"], jogo.estatisticas["mortes_ptera"]) == (0, 6)
    monkeypatch.undo()
    random.seed(8)
    np.random.seed(8)
    jogo.roda_geracao([RedeNeural.RedeNeural(CFG) for _ in range(40)], janela=False)
    e = jogo.estatisticas
    assert e["mortes_cacto"] + e["mortes_ptera"] == 40
    assert len(e["obstaculos"]) == 40


CABECALHO = (
    "geracao,melhor,media,mediana,desvio,pior,frames,obstaculos_melhor,"
    "obstaculos_media,mortes_cacto,mortes_ptera,diversidade"
)


def _linhas(pasta):
    import csv

    with open(pasta / "fitness.csv", newline="") as f:
        return list(csv.DictReader(f))


def test_cabecalho_do_fitness_csv(tmp_path):
    DinoGame.registra_geracao([(10, RedeNeural.RedeNeural(CFG))], 1, None, str(tmp_path))
    assert (tmp_path / "fitness.csv").read_text().splitlines()[0] == CABECALHO


def test_mediana_desvio_e_pior(tmp_path):
    redes = [RedeNeural.RedeNeural(CFG) for _ in range(4)]
    estat = {"frames": 321, "obstaculos": [4, 0, 2], "mortes_cacto": 2, "mortes_ptera": 1}
    DinoGame.registra_geracao([(10, redes[0]), (60, redes[1]), (20, redes[2])], 1, None, str(tmp_path), estat)
    estat2 = {"frames": 99, "obstaculos": [1, 3, 5, 7], "mortes_cacto": 0, "mortes_ptera": 4}
    DinoGame.registra_geracao([(5, r) for r in redes[:2]] + [(15, redes[2]), (40, redes[3])], 2, 60, str(tmp_path), estat2)
    l1, l2 = _linhas(tmp_path)
    assert (l1["melhor"], l1["pior"]) == ("60", "10")
    assert float(l1["media"]) == pytest.approx(30.0)
    assert float(l1["mediana"]) == 20.0
    assert float(l1["desvio"]) == pytest.approx(21.602468994692867)  # populacional: divisor 3, nao 2
    assert (l1["frames"], l1["obstaculos_melhor"], l1["mortes_cacto"], l1["mortes_ptera"]) == ("321", "4", "2", "1")
    assert float(l1["obstaculos_media"]) == pytest.approx(2.0)
    assert float(l2["mediana"]) == 10.0  # par: media dos dois do meio, 5 e 15
    assert l2["pior"] == "5" and float(l2["desvio"]) == pytest.approx(np.std([5, 5, 15, 40]))
    assert (l2["frames"], l2["obstaculos_melhor"], l2["mortes_ptera"]) == ("99", "7", "4")
    assert float(l2["obstaculos_media"]) == pytest.approx(4.0)


def test_diversidade_no_csv(tmp_path):
    np.random.seed(2)
    redes = [RedeNeural.RedeNeural(CFG) for _ in range(5)]
    DinoGame.registra_geracao([(i, r) for i, r in enumerate(redes)], 1, None, str(tmp_path))
    assert float(_linhas(tmp_path)[0]["diversidade"]) == pytest.approx(AGMLP.diversidade(redes))
    copias = [redes[0]] * 3
    DinoGame.registra_geracao([(1, r) for r in copias], 2, 4, str(tmp_path))
    assert float(_linhas(tmp_path)[1]["diversidade"]) == pytest.approx(0.0, abs=1e-12)  # ruido de ponto flutuante do std
