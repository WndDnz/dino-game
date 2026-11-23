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


# ---- T2: avaliacao em varias pistas ------------------------------------------


def _pista_a_pista(jogo, redes, sementes):
    """Roda cada pista em separado: [({id da rede: score}, estatisticas)] por semente."""
    saida = []
    for semente in sementes:
        random.seed(semente)
        ranked = jogo.roda_geracao(redes, janela=False)
        saida.append(({id(r): s for s, r in ranked}, jogo.estatisticas, ranked))
    return saida


def _roda_falsa(monkeypatch, scores, obstaculos=None):
    """roda_geracao de mentira: na chamada k, a rede i faz scores[i][k]. A ordem de `ranked`
    muda a cada chamada, como numa pista real (quem morre primeiro vem primeiro)."""
    chamadas = []

    def roda(self, redes, janela=True):
        k = len(chamadas)
        chamadas.append(k)
        ordem = list(range(len(redes)))
        ordem = ordem[k % len(redes):] + ordem[: k % len(redes)]
        self.estatisticas = {
            "frames": 100 + k,
            "obstaculos": [obstaculos[i][k] if obstaculos else 0 for i in ordem],
            "mortes_cacto": len(redes),
            "mortes_ptera": 0,
        }
        return [(scores[i][k], redes[i]) for i in ordem]

    monkeypatch.setattr(DinoGame.DinoGame, "roda_geracao", roda)
    return chamadas


def test_populacao_corre_em_cada_pista_de_treino(jogo, monkeypatch):
    vistos = []
    roda = DinoGame.DinoGame.roda_geracao

    def espia(self, redes, janela=True):
        vistos.append(([id(r) for r in redes], random.getstate()))
        return roda(self, redes, janela)

    monkeypatch.setattr(DinoGame.DinoGame, "roda_geracao", espia)
    redes = _redes(4, 1)
    random.seed(123)
    jogo.avalia(redes, (8, 9, 10), janela=False)
    assert len(vistos) == 3
    for (ids, estado), semente in zip(vistos, (8, 9, 10)):
        assert ids == [id(r) for r in redes]  # a populacao inteira, em cada pista
        random.seed(semente)
        assert estado == random.getstate()


def test_fitness_e_a_media_das_pistas(jogo, monkeypatch):
    a, b = _redes(2, 1)
    _roda_falsa(monkeypatch, [(10, 20, 60), (30, 30, 30)])
    assert jogo.avalia([a, b], (1, 2, 3), janela=False) == [(30.0, a), (30.0, b)]
    _roda_falsa(monkeypatch, [(10, 20, 61), (30, 30, 30)])
    fit = jogo.avalia([a, b], (1, 2, 3), janela=False)
    assert fit[0][0] == pytest.approx(91 / 3) and fit[0][1] is a and fit[1] == (30.0, b)
    # pista real: a media dos scores de cada pista rodada em separado
    monkeypatch.undo()
    redes = _redes(150, 2)
    separado = _pista_a_pista(jogo, redes, (8, 9, 10))
    fit = jogo.avalia(redes, (8, 9, 10), janela=False)
    assert [r for _, r in fit] == redes  # na ordem da populacao
    for f, rede in fit:
        assert f == pytest.approx(sum(scores[id(rede)] for scores, _, _ in separado) / 3)
    assert len({f for f, _ in fit}) > 3  # a comparacao nao e trivial: fitness variados


def test_frames_e_mortes_somam_as_pistas(jogo):
    redes = _redes(150, 3)
    separado = [e for _, e, _ in _pista_a_pista(jogo, redes, (8, 9, 10))]
    jogo.avalia(redes, (8, 9, 10), janela=False)
    for chave in ("frames", "mortes_cacto", "mortes_ptera"):
        assert jogo.estatisticas[chave] == sum(e[chave] for e in separado), chave
    assert jogo.estatisticas["mortes_cacto"] + jogo.estatisticas["mortes_ptera"] == 450
    assert len({e["frames"] for e in separado}) >= 2  # pistas diferentes, valores diferentes


def test_obstaculos_media_por_pista(jogo, monkeypatch):
    redes = _redes(3, 1)
    _roda_falsa(monkeypatch, [(1, 1, 1)] * 3, obstaculos=[(0, 0, 0), (2, 4, 9), (1, 1, 2)])
    jogo.avalia(redes, (1, 2, 3), janela=False)
    assert jogo.estatisticas["obstaculos"] == [0.0, 5.0, pytest.approx(4 / 3)]
    # pista real
    monkeypatch.undo()
    redes = _redes(30, 4)
    separado = _pista_a_pista(jogo, redes, (8, 9))
    jogo.avalia(redes, (8, 9), janela=False)
    for i, rede in enumerate(redes):
        por_pista = [e["obstaculos"][[id(r) for _, r in ranked].index(id(rede))] for _, e, ranked in separado]
        assert jogo.estatisticas["obstaculos"][i] == pytest.approx(sum(por_pista) / 2)
    assert max(jogo.estatisticas["obstaculos"]) > 0


def test_empate_no_melhor_e_reproduzivel(jogo):
    import copy

    a = _redes(40, 5)
    random.seed(8)
    melhor = max(jogo.roda_geracao(a, janela=False), key=lambda par: par[0])[1]
    redes = [_rede_fixa(pula=False), melhor, copy.deepcopy(melhor)]
    for _ in range(2):
        fit = jogo.avalia(redes, (8, 9), janela=False)
        assert fit[1][0] == fit[2][0] > fit[0][0]  # empate no maior fitness
        assert max(fit, key=lambda par: par[0])[1] is redes[1]  # sempre o de menor indice


# ---- T3: treino com pistas fixas ---------------------------------------------


def _linhas(pasta):
    with open(pasta / "fitness.csv", newline="") as f:
        return list(csv.DictReader(f))


def _json(caminho):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def _estado_apos_seed(semente):
    random.seed(semente)
    return random.getstate()


def _espia_pistas(monkeypatch):
    """Estado do random no comeco de cada partida: (geracao, n de redes, janela, estado)."""
    partidas = []
    roda = DinoGame.DinoGame.roda_geracao

    def espia(self, redes, janela=True):
        partidas.append((DinoGame.DinoGame.train.currentGeneration, len(redes), janela, random.getstate()))
        return roda(self, redes, janela)

    monkeypatch.setattr(DinoGame.DinoGame, "roda_geracao", espia)
    return partidas


def _avalia_falsa(monkeypatch, fitness, teste=None):
    """avalia de mentira: na geracao g, o individuo i tem fitness[g-1][i]; a rede que corre
    sozinha nas pistas de teste faz teste[g-1]. Devolve {geracao: populacao avaliada}."""
    populacoes = {}

    def avalia(self, redes, sementes, janela=True):
        g = DinoGame.DinoGame.train.currentGeneration
        self.estatisticas = {
            "frames": 7, "obstaculos": [0.0] * len(redes), "mortes_cacto": len(redes), "mortes_ptera": 0,
        }
        if list(sementes) == list(DinoGame.SEMENTES_TESTE):
            return [(teste[g - 1] if teste else 0.0, redes[0])]
        populacoes[g] = list(redes)
        return list(zip(fitness[g - 1], redes))

    monkeypatch.setattr(DinoGame.DinoGame, "avalia", avalia)
    return populacoes


def test_mesmas_pistas_em_todas_as_geracoes(jogo, monkeypatch, tmp_path, capsys):
    partidas = _espia_pistas(monkeypatch)
    jogo.train(6, 3, semente_base=7, saida=str(tmp_path), janela=False, pistas=2)
    treino = [(g, estado) for g, n, _, estado in partidas if n == 6]  # a populacao inteira
    assert [g for g, _ in treino] == [1, 1, 2, 2, 3, 3]
    assert [estado for _, estado in treino] == [_estado_apos_seed(8), _estado_apos_seed(9)] * 3


def test_estatisticas_sobre_o_fitness(jogo, monkeypatch, tmp_path, capsys):
    import statistics

    fitness = [10.5, 20.0, 60.0, 30.0]
    _avalia_falsa(monkeypatch, [fitness])
    jogo.train(4, 1, semente_base=1, saida=str(tmp_path), janela=False)
    (linha,) = _linhas(tmp_path)
    assert float(linha["melhor"]) == 60.0
    assert float(linha["media"]) == 30.125
    assert float(linha["mediana"]) == 25.0
    assert float(linha["pior"]) == 10.5
    assert float(linha["desvio"]) == pytest.approx(statistics.pstdev(fitness))


def test_recorde_pelo_fitness(jogo, monkeypatch, tmp_path, capsys):
    # maior fitness por geracao: 50, 50 (empata, outra rede), 40 (menor), 70.5 (recorde)
    fitness = [[50, 10, 10, 10], [10, 50, 10, 10], [40, 10, 10, 10], [10, 10, 70.5, 10]]
    populacoes = _avalia_falsa(monkeypatch, fitness)
    gravadas = []
    salva = RedeNeural.RedeNeural.save_object

    def espia(rede, caminho):
        gravadas.append((DinoGame.DinoGame.train.currentGeneration, rede, os.path.basename(caminho)))
        return salva(rede, caminho)

    monkeypatch.setattr(RedeNeural.RedeNeural, "save_object", staticmethod(espia))
    jogo.train(4, 4, semente_base=1, saida=str(tmp_path), janela=False)
    assert [(g, nome) for g, _, nome in gravadas] == [(1, "bestDino.din"), (4, "bestDino.din")]
    assert gravadas[0][1] is populacoes[1][0] and gravadas[1][1] is populacoes[4][2]
    no_disco = DinoGame.carrega_rede(str(tmp_path / "bestDino.din"))
    for a, b in zip(no_disco.pesos + no_disco.bias, populacoes[4][2].pesos + populacoes[4][2].bias):
        assert np.array_equal(a, b)
    assert _json(tmp_path / "resumo.json")["melhor_score"] == 70.5


def test_config_traz_pistas(jogo, tmp_path, capsys):
    jogo.train(4, 1, semente_base=1, saida=str(tmp_path), janela=False, pistas=3)
    config = _json(tmp_path / "config.json")
    assert (config["pistas"], config["pistas_teste"], config["limite_frames"]) == (3, 20, 14000)


def test_uma_pista_so(jogo, monkeypatch, tmp_path, capsys):
    partidas = _espia_pistas(monkeypatch)
    jogo.train(6, 3, semente_base=7, saida=str(tmp_path), janela=False, pistas=1)
    treino = [(g, estado) for g, n, _, estado in partidas if n == 6]
    assert [g for g, _ in treino] == [1, 2, 3]
    assert [estado for _, estado in treino] == [_estado_apos_seed(8)] * 3


def test_janela_fechada_nao_registra_geracao(jogo, monkeypatch, tmp_path, capsys):
    partidas = _espia_pistas(monkeypatch)

    def eventos(self):
        com_janela = [p for p in partidas if p[2]]
        return len(com_janela) < 4  # fecha na 2a pista da geracao 2 (2 pistas por geracao)

    monkeypatch.setattr(DinoGame.DinoGame, "_eventos_treino", eventos)
    with pytest.raises(SystemExit):
        jogo.train(6, 3, semente_base=7, saida=str(tmp_path), pistas=2)
    assert [(g, n) for g, n, janela, _ in partidas if janela] == [(1, 6), (1, 6), (2, 6), (2, 6)]
    assert [l["geracao"] for l in _linhas(tmp_path)] == ["1"]
    assert not (tmp_path / "resumo.json").exists()
