"""Testes da spec fixed-test-tracks. Rodam sem janela: python -m pytest test_pistas.py -v"""

import csv
import json
import os
import random
import shutil

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["MPLBACKEND"] = "Agg"

import numpy as np  # noqa: E402
import pygame  # noqa: E402
import pytest  # noqa: E402

import autodino  # noqa: E402
import DinoGame  # noqa: E402
import graficos  # noqa: E402
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


# ---- T4: pistas de teste -----------------------------------------------------

TESTE = list(range(900001, 900021))
CABECALHO = (
    "geracao,melhor,media,mediana,desvio,pior,frames,obstaculos_melhor,"
    "obstaculos_media,mortes_cacto,mortes_ptera,diversidade,teste"
)


class _Fim(Exception):
    pass


def test_melhor_corre_nas_pistas_de_teste(jogo, monkeypatch, tmp_path, capsys):
    assert list(DinoGame.SEMENTES_TESTE) == TESTE
    chamadas = []
    avalia = DinoGame.DinoGame.avalia

    def espia(self, redes, sementes, janela=True):
        resultado = avalia(self, redes, sementes, janela)
        chamadas.append((list(redes), list(sementes), janela, resultado))
        return resultado

    monkeypatch.setattr(DinoGame.DinoGame, "avalia", espia)
    jogo.train(8, 3, semente_base=7, saida=str(tmp_path), janela=False, pistas=2)
    assert len(chamadas) == 6  # por geracao: a populacao no treino, depois uma rede no teste
    for treino, teste in zip(chamadas[0::2], chamadas[1::2]):
        assert len(treino[0]) == 8 and treino[1] == [8, 9]
        campea = max(treino[3], key=lambda par: par[0])[1]
        assert teste[0] == [campea]  # so a rede de maior fitness da geracao
        assert teste[1] == TESTE
        assert teste[2] is False  # as pistas de teste rodam sem desenho


def test_coluna_teste_e_a_media(jogo, monkeypatch, tmp_path, capsys):
    # scores de teste fixados: 1, 2, ..., 20 -> media 10.5
    roda = DinoGame.DinoGame.roda_geracao
    sozinha = []

    def roda_com_teste_fixo(self, redes, janela=True):
        if len(redes) > 1:
            return roda(self, redes, janela)
        sozinha.append(1)
        self.estatisticas = {"frames": 1, "obstaculos": [0], "mortes_cacto": 1, "mortes_ptera": 0}
        return [(len(sozinha), redes[0])]

    monkeypatch.setattr(DinoGame.DinoGame, "roda_geracao", roda_com_teste_fixo)
    (tmp_path / "fixo").mkdir()
    jogo.train(6, 1, semente_base=7, saida=str(tmp_path / "fixo"), janela=False, pistas=2)
    assert float(_linhas(tmp_path / "fixo")[0]["teste"]) == 10.5
    # pista real: a media dos scores da rede salva, rodada em cada pista de teste
    monkeypatch.undo()
    (tmp_path / "real").mkdir()
    jogo.train(40, 1, semente_base=7, saida=str(tmp_path / "real"), janela=False, pistas=2)
    campea = DinoGame.carrega_rede(str(tmp_path / "real" / "bestDino.din"))
    scores = []
    for semente in TESTE:
        random.seed(semente)
        scores.append(jogo.roda_geracao([campea], janela=False)[0][0])
    assert len(set(scores)) > 1  # pistas diferentes, scores diferentes
    assert float(_linhas(tmp_path / "real")[0]["teste"]) == pytest.approx(sum(scores) / 20)


def test_cabecalho_com_teste(jogo, tmp_path, capsys):
    jogo.train(4, 1, semente_base=1, saida=str(tmp_path), janela=False, pistas=1)
    assert (tmp_path / "fitness.csv").read_text().splitlines()[0] == CABECALHO


def test_selecao_ignora_o_teste(jogo, monkeypatch, tmp_path, capsys):
    def treina(nome):
        (tmp_path / nome).mkdir()
        jogo.train(12, 4, semente_base=7, saida=str(tmp_path / nome), janela=False, pistas=2)
        return _linhas(tmp_path / nome), (tmp_path / nome / "bestDino.din").read_bytes()

    normal, rede_normal = treina("normal")
    # outro teste: scores diferentes e o `random` deixado em outro estado
    avalia = DinoGame.DinoGame.avalia

    def outro_teste(self, redes, sementes, janela=True):
        if list(sementes) != TESTE:
            return avalia(self, redes, sementes, janela)
        random.seed(len(redes) * 31337)
        random.random()
        return [(999.0, redes[0])]

    monkeypatch.setattr(DinoGame.DinoGame, "avalia", outro_teste)
    trocado, rede_trocada = treina("trocado")
    assert [l["teste"] for l in trocado] == ["999.0"] * 4 != [l["teste"] for l in normal]
    for a, b in zip(normal, trocado):
        assert {k: v for k, v in a.items() if k != "teste"} == {k: v for k, v in b.items() if k != "teste"}
    assert rede_normal == rede_trocada
    assert len({l["media"] for l in normal}) > 1  # as geracoes diferem: a selecao agiu


def test_pistas_de_teste_independem_das_opcoes(jogo, monkeypatch, tmp_path, capsys):
    esperado = [_estado_apos_seed(s) for s in TESTE]
    for semente, pistas in ((3, 1), (11, 3)):
        partidas = _espia_pistas(monkeypatch)
        saida = tmp_path / f"s{semente}"
        saida.mkdir()
        jogo.train(4, 2, semente_base=semente, saida=str(saida), janela=False, pistas=pistas)
        teste = [estado for _, n, _, estado in partidas if n == 1]
        assert teste == esperado * 2  # as mesmas 20 pistas, nas duas geracoes
        monkeypatch.undo()


def test_resumo_traz_teste_do_melhor(jogo, monkeypatch, tmp_path, capsys):
    # recorde na geracao 2; a geracao 3 tem teste maior, mas fitness menor
    _avalia_falsa(monkeypatch, [[50, 10, 10, 10], [10, 70, 10, 10], [60, 10, 10, 10]], teste=[11.0, 22.5, 33.0])
    jogo.train(4, 3, semente_base=1, saida=str(tmp_path), janela=False)
    resumo = _json(tmp_path / "resumo.json")
    assert (resumo["geracao_do_melhor"], resumo["teste_do_melhor"]) == (2, 22.5)
    assert [float(l["teste"]) for l in _linhas(tmp_path)] == [11.0, 22.5, 33.0]


def test_linha_impressa_com_teste(jogo, monkeypatch, tmp_path, capsys):
    (tmp_path / "real").mkdir()
    jogo.train(6, 2, semente_base=7, saida=str(tmp_path / "real"), janela=False, pistas=2)
    impressas = [l for l in capsys.readouterr().out.splitlines() if l.startswith("Geração")]
    linhas = _linhas(tmp_path / "real")
    assert len(linhas) == 2
    assert impressas == [
        f"Geração {l['geracao']}: melhor={l['melhor']} media={l['media']} teste={l['teste']}" for l in linhas
    ]
    _avalia_falsa(monkeypatch, [[10.5, 20.0, 60.0, 30.0]], teste=[42.5])
    jogo.train(4, 1, semente_base=1, saida=str(tmp_path), janela=False)
    impressas = [l for l in capsys.readouterr().out.splitlines() if l.startswith("Geração")]
    assert impressas == ["Geração 1: melhor=60.0 media=30.125 teste=42.5"]


def test_csv_igual_com_e_sem_janela_com_pistas(jogo, monkeypatch, tmp_path, capsys):
    def fim(*args):
        raise _Fim

    monkeypatch.setattr(DinoGame.DinoGame, "disp_gameOver_msg", fim)
    (tmp_path / "com").mkdir()
    (tmp_path / "sem").mkdir()
    with pytest.raises(_Fim):
        jogo.train(10, 3, semente_base=6, saida=str(tmp_path / "com"), pistas=2)
    jogo.train(10, 3, semente_base=6, saida=str(tmp_path / "sem"), janela=False, pistas=2)
    com = (tmp_path / "com" / "fitness.csv").read_text()
    assert com == (tmp_path / "sem" / "fitness.csv").read_text()
    linhas = _linhas(tmp_path / "com")
    assert len(linhas) == 3 and list(linhas[0]) == CABECALHO.split(",")
    for l in linhas:
        assert all(v != "" for v in l.values())
        assert float(l["teste"]) > 0
        assert int(l["mortes_cacto"]) + int(l["mortes_ptera"]) == 20  # 10 dinos x 2 pistas


# ---- T5: opcao --pistas ------------------------------------------------------

REPO = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def pasta(tmp_path, monkeypatch):
    """Diretorio de trabalho temporario com os sprites."""
    shutil.copytree(os.path.join(REPO, "sprites"), tmp_path / "sprites")
    monkeypatch.chdir(tmp_path)
    pygame.init()
    pygame.mixer.quit()
    return tmp_path


def test_opcao_pistas(pasta, monkeypatch, capsys):
    chamadas = []

    def train(self, nIndividuals=20, nGenerations=100, semente_base=0, saida=".", janela=True, pistas=None):
        chamadas.append((janela, pistas))

    monkeypatch.setattr(DinoGame.DinoGame, "train", train)
    monkeypatch.setattr(DinoGame.DinoGame, "introscreen", lambda self: False)
    assert autodino.main(["--sem-janela", "--pistas", "3"]) == 0
    assert autodino.main(["--pistas", "3"]) == 0
    assert autodino.main(["--sem-janela", "--pistas", "1"]) == 0
    assert chamadas == [(False, 3), (True, 3), (False, 1)]
    # treino de verdade: com a opcao, N pistas; sem ela, 5
    monkeypatch.undo()
    monkeypatch.chdir(pasta)
    partidas = _espia_pistas(monkeypatch)
    base = ["--sem-janela", "--individuos", "4", "--geracoes", "1", "--semente", "7"]
    assert autodino.main(base + ["--saida", "tres", "--pistas", "3"]) == 0
    assert _json(pasta / "tres" / "config.json")["pistas"] == 3
    assert [estado for _, n, _, estado in partidas if n == 4] == [_estado_apos_seed(s) for s in (8, 9, 10)]
    partidas.clear()
    assert autodino.main(base + ["--saida", "padrao"]) == 0
    assert _json(pasta / "padrao" / "config.json")["pistas"] == 5
    assert [estado for _, n, _, estado in partidas if n == 4] == [_estado_apos_seed(s) for s in range(8, 13)]


def test_pistas_invalido_codigo_2(pasta, monkeypatch, capsys):
    treinou = []
    monkeypatch.setattr(DinoGame.DinoGame, "train", lambda self, *a, **k: treinou.append(1))
    for valor in ("0", "-1", "2.5", "duas"):
        with pytest.raises(SystemExit) as saida:
            autodino.main(["--sem-janela", "--pistas", valor])
        assert saida.value.code == 2, valor
    assert treinou == [] and not (pasta / "treinos").exists()


# ---- T6 e T7: graficos -------------------------------------------------------

CABECALHO_12 = CABECALHO.rsplit(",", 1)[0]
FITNESS = [
    # geracao,melhor,media,mediana,desvio,pior,frames,obst_melhor,obst_media,mortes_cacto,mortes_ptera,diversidade,teste
    (1, 50.0, 20.0, 18.0, 6.0, 5.0, 300, 2.0, 0.5, 9, 1, 3.9, 31.5),
    (2, 90.0, 35.0, 30.0, 12.0, 8.0, 520, 4.0, 1.25, 6, 4, 3.5, 77.25),
    (3, 140.0, 60.0, 55.0, 20.0, 11.0, 900, 7.0, 2.75, 3, 7, 2.8, 64.0),
]


def _fitness(pasta, linhas=FITNESS, colunas=13):
    """Grava um fitness.csv com as primeiras `colunas` colunas de `linhas`."""
    pasta.mkdir(parents=True, exist_ok=True)
    cabecalho = ",".join(CABECALHO.split(",")[:colunas])
    corpo = [",".join(map(str, l[:colunas])) for l in linhas]
    (pasta / "fitness.csv").write_text("\n".join([cabecalho, *corpo]) + "\n")
    return pasta


def _figuras(monkeypatch):
    """Guarda cada figura salva por graficos.py: {nome do arquivo: figura}."""
    import matplotlib.figure

    salvas = {}
    savefig = matplotlib.figure.Figure.savefig

    def guarda(self, caminho, *a, **k):
        salvas[os.path.basename(str(caminho))] = self
        return savefig(self, caminho, *a, **k)

    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", guarda)
    return salvas


def _curvas(fig):
    """{rotulo: (x, y)} das linhas do primeiro eixo."""
    return {l.get_label(): (list(l.get_xdata()), list(l.get_ydata())) for l in fig.axes[0].get_lines()}


def test_aptidao_com_curva_de_teste(tmp_path, monkeypatch):
    salvas = _figuras(monkeypatch)
    pasta = _fitness(tmp_path / "t")
    assert graficos.main([str(pasta)]) == 0
    assert (pasta / "aptidao.png").stat().st_size > 0
    curvas = _curvas(salvas["aptidao.png"])
    assert set(curvas) == {"melhor", "mediana", "média", "pior", "teste"}
    assert curvas["teste"] == ([1.0, 2.0, 3.0], [31.5, 77.25, 64.0])
    assert curvas["melhor"] == ([1.0, 2.0, 3.0], [50.0, 90.0, 140.0])  # as outras curvas continuam
    legenda = [t.get_text() for t in salvas["aptidao.png"].axes[0].get_legend().get_texts()]
    assert "teste" in legenda


def test_aptidao_sem_coluna_teste(tmp_path, monkeypatch, capsys):
    salvas = _figuras(monkeypatch)
    pasta = _fitness(tmp_path / "antigo", colunas=12)
    assert (pasta / "fitness.csv").read_text().splitlines()[0] == CABECALHO_12
    assert graficos.main([str(pasta)]) == 0
    assert (pasta / "aptidao.png").stat().st_size > 0
    assert set(_curvas(salvas["aptidao.png"])) == {"melhor", "mediana", "média", "pior"}
    assert capsys.readouterr().out == ""  # nenhum aviso
    assert sorted(p.name for p in pasta.glob("*.png")) == sorted(graficos.GRAFICOS)  # nada pulado


def _compara(tmp_path, monkeypatch, colunas_do_segundo):
    salvas = _figuras(monkeypatch)
    monkeypatch.chdir(tmp_path)
    outro = [(g, m, med * 2, *meio, teste + 100) for g, m, med, *meio, teste in FITNESS]
    a = _fitness(tmp_path / "treinos" / "20261123-090000_s1")
    b = _fitness(tmp_path / "treinos" / "20261123-100000_s2", linhas=outro, colunas=colunas_do_segundo)
    assert graficos.main([str(a), str(b)]) == 0
    assert (tmp_path / "comparacao.png").stat().st_size > 0
    return salvas["comparacao.png"]


def test_comparacao_usa_teste(tmp_path, monkeypatch):
    fig = _compara(tmp_path, monkeypatch, colunas_do_segundo=13)
    assert _curvas(fig) == {
        "20261123-090000_s1": ([1.0, 2.0, 3.0], [31.5, 77.25, 64.0]),
        "20261123-100000_s2": ([1.0, 2.0, 3.0], [131.5, 177.25, 164.0]),
    }
    assert fig.axes[0].get_ylabel() == "score de teste"


def test_comparacao_sem_teste_usa_media(tmp_path, monkeypatch):
    fig = _compara(tmp_path, monkeypatch, colunas_do_segundo=12)
    assert _curvas(fig) == {
        "20261123-090000_s1": ([1.0, 2.0, 3.0], [20.0, 35.0, 60.0]),
        "20261123-100000_s2": ([1.0, 2.0, 3.0], [40.0, 70.0, 120.0]),
    }
    assert fig.axes[0].get_ylabel() == "média"


# ---- achados do Verifier -----------------------------------------------------


def test_obstaculos_contados_sem_depender_de_id(jogo, monkeypatch):
    # achado 1: um obstaculo que sai da pista e liberado, e o seguinte pode nascer com o
    # mesmo id(); a contagem de vencidos nao pode se confundir com isso
    criados = []  # conta os nascimentos sem guardar o objeto, para o id poder ser reutilizado
    for classe in (DinoGame.Cactus, DinoGame.Ptera):
        def espia(self, *a, _init=classe.__init__, **k):
            criados.append(1)
            _init(self, *a, **k)

        monkeypatch.setattr(classe, "__init__", espia)
    monkeypatch.setattr(pygame.sprite, "collide_mask", lambda a, b: None)  # ninguem morre
    monkeypatch.setattr(DinoGame, "LIMITE_FRAMES", 6000)
    na_pista = []
    passo = DinoGame.Pista.passo

    def espia_passo(self):
        passo(self)
        na_pista[:] = [sum(o.rect.right >= 40 for o in (*self.cacti, *self.pteras))]

    monkeypatch.setattr(DinoGame.Pista, "passo", espia_passo)
    for semente in (8, 9):
        criados.clear()
        random.seed(semente)
        jogo.roda_geracao([_rede_fixa(pula=False) for _ in range(3)], janela=False)
        vencidos = len(criados) - na_pista[0]  # todos os que nasceram, menos os que ainda nao passaram
        assert vencidos > 40
        assert jogo.estatisticas["obstaculos"] == [vencidos] * 3
