"""Testes da spec training-record-and-plots. Rodam sem janela: python -m pytest test_registro.py -v"""

import datetime
import json
import os
import random
import re
import shutil
import subprocess

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["MPLBACKEND"] = "Agg"

import numpy as np  # noqa: E402
import pygame  # noqa: E402
import pytest  # noqa: E402

import AGMLP  # noqa: E402
import autodino  # noqa: E402
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


def test_versao_do_codigo_vem_do_git():
    repo = os.path.dirname(os.path.abspath(DinoGame.__file__))
    esperado = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=repo, capture_output=True, text=True
    ).stdout.strip()
    sujo = bool(subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True).stdout.strip())
    assert len(esperado) >= 7
    assert DinoGame.versao_do_codigo() == (esperado, sujo)


def test_versao_sem_git(monkeypatch):
    def sem_git(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr(subprocess, "run", sem_git)
    assert DinoGame.versao_do_codigo() == (None, False)

    def git_falha(*args, **kwargs):
        return subprocess.CompletedProcess(args, 128, stdout="", stderr="fatal: not a git repository")

    monkeypatch.setattr(subprocess, "run", git_falha)
    assert DinoGame.versao_do_codigo() == (None, False)


class _Fim(Exception):
    pass


def _json(caminho):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def test_config_json_antes_da_primeira_geracao(jogo, monkeypatch, tmp_path, capsys):
    vistos = []
    roda = DinoGame.DinoGame.roda_geracao

    def espia(self, redes, janela=True):
        if not vistos:
            arquivo = tmp_path / "config.json"
            vistos.append(_json(arquivo) if arquivo.exists() else None)
        return roda(self, redes, janela)

    monkeypatch.setattr(DinoGame.DinoGame, "roda_geracao", espia)
    jogo.train(10, 2, semente_base=4, saida=str(tmp_path), janela=False)
    config = vistos[0]
    assert config is not None, "config.json nao existia quando a primeira geracao comecou"
    commit, sujo = DinoGame.versao_do_codigo()
    inicio = config.pop("inicio")
    assert config == {
        "individuos": 10, "geracoes": 2, "semente": 4, "janela": False, "topologia": [5, 8, 4, 2],
        "taxa_mutacao": 0.05, "sigma_mutacao": 0.5, "elite": 0.1, "torneio": 3, "alpha_blx": 0.1,
        "commit": commit, "alteracoes_locais": sujo,
    }
    assert datetime.datetime.fromisoformat(inicio).year >= 2026


def test_resumo_json_no_fim(jogo, tmp_path, capsys):
    jogo.train(10, 3, semente_base=4, saida=str(tmp_path), janela=False)
    resumo = _json(tmp_path / "resumo.json")
    linhas = _linhas(tmp_path)
    melhor = max(linhas, key=lambda l: int(l["melhor"]))  # max devolve o primeiro em caso de empate
    assert set(resumo) == {"geracoes_concluidas", "melhor_score", "geracao_do_melhor", "frames_total", "segundos_total"}
    assert resumo["geracoes_concluidas"] == 3 == len(linhas)
    assert resumo["melhor_score"] == int(melhor["melhor"])
    assert resumo["geracao_do_melhor"] == int(melhor["geracao"])
    assert resumo["frames_total"] == sum(int(l["frames"]) for l in linhas)
    assert isinstance(resumo["segundos_total"], float) and resumo["segundos_total"] > 0


def test_treino_interrompido_sem_resumo(jogo, monkeypatch, tmp_path, capsys):
    passo = DinoGame.Pista.passo

    def ctrl_c_na_geracao_2(self):
        if DinoGame.DinoGame.train.currentGeneration == 2 and self.counter == 20:
            raise KeyboardInterrupt
        passo(self)

    monkeypatch.setattr(DinoGame.Pista, "passo", ctrl_c_na_geracao_2)
    with pytest.raises(KeyboardInterrupt):
        jogo.train(10, 3, semente_base=4, saida=str(tmp_path), janela=False)
    assert sorted(os.listdir(tmp_path)) == ["bestDino.din", "config.json", "fitness.csv"]
    assert len(_linhas(tmp_path)) == 1


def test_csv_completo_igual_com_e_sem_janela(jogo, monkeypatch, tmp_path, capsys):
    def fim(*args):
        raise _Fim

    monkeypatch.setattr(DinoGame.DinoGame, "disp_gameOver_msg", fim)
    (tmp_path / "com").mkdir()
    (tmp_path / "sem").mkdir()
    with pytest.raises(_Fim):
        jogo.train(10, 3, semente_base=6, saida=str(tmp_path / "com"))
    jogo.train(10, 3, semente_base=6, saida=str(tmp_path / "sem"), janela=False)
    com = (tmp_path / "com" / "fitness.csv").read_text()
    assert com == (tmp_path / "sem" / "fitness.csv").read_text()
    linhas = _linhas(tmp_path / "com")
    assert len(linhas) == 3 and list(linhas[0]) == CABECALHO.split(",")
    for l in linhas:
        assert int(l["mortes_cacto"]) + int(l["mortes_ptera"]) == 10
        assert float(l["pior"]) <= float(l["mediana"]) <= float(l["melhor"])
        assert int(l["frames"]) > 0


REPO = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def pasta(tmp_path, monkeypatch):
    """Diretorio de trabalho temporario com os sprites."""
    shutil.copytree(os.path.join(REPO, "sprites"), tmp_path / "sprites")
    monkeypatch.chdir(tmp_path)
    pygame.init()
    pygame.mixer.quit()
    return tmp_path


def _treinos(pasta):
    raiz = pasta / "treinos"
    return sorted(p.name for p in raiz.iterdir()) if raiz.exists() else []


def test_treino_cria_pasta_com_data_e_semente(pasta, capsys):
    antes = datetime.datetime.now().replace(microsecond=0)
    assert autodino.main(["--sem-janela", "--individuos", "5", "--geracoes", "2", "--semente", "7"]) == 0
    depois = datetime.datetime.now()
    (nome,) = _treinos(pasta)
    assert re.fullmatch(r"\d{8}-\d{6}_s7", nome)
    criada = datetime.datetime.strptime(nome[:15], "%Y%m%d-%H%M%S")
    assert antes <= criada <= depois
    assert sorted(os.listdir(pasta / "treinos" / nome)) == ["bestDino.din", "config.json", "fitness.csv", "resumo.json"]
    assert not (pasta / "fitness.csv").exists() and not (pasta / "bestDino.din").exists()


def test_saida_escolhida(pasta, capsys):
    assert autodino.main(["--sem-janela", "--individuos", "5", "--geracoes", "1", "--saida", "meu_treino"]) == 0
    assert sorted(os.listdir(pasta / "meu_treino")) == ["bestDino.din", "config.json", "fitness.csv", "resumo.json"]
    assert not (pasta / "treinos").exists()
    # pasta vazia que ja existe e aceita
    (pasta / "vazia").mkdir()
    assert autodino.main(["--sem-janela", "--individuos", "5", "--geracoes", "1", "--saida", "vazia"]) == 0
    assert (pasta / "vazia" / "fitness.csv").exists()


def test_pasta_com_treino_e_recusada(pasta, monkeypatch, capsys):
    (pasta / "antigo").mkdir()
    (pasta / "antigo" / "fitness.csv").write_text("conteudo anterior")
    treinos = []
    monkeypatch.setattr(DinoGame.DinoGame, "train", lambda self, *a, **k: treinos.append(a))
    monkeypatch.setattr(DinoGame.DinoGame, "introscreen", lambda self: False)
    for modo in (["--sem-janela"], []):
        assert autodino.main([*modo, "--saida", "antigo"]) == 1
        assert capsys.readouterr().out.splitlines() == ["Pasta já tem um treino: antigo"]
    assert treinos == []
    assert (pasta / "antigo" / "fitness.csv").read_text() == "conteudo anterior"


def test_mesmo_segundo_ganha_sufixo(pasta, monkeypatch, capsys):
    monkeypatch.setattr(autodino.time, "strftime", lambda formato, *a: "20261123-101500")
    monkeypatch.setattr(DinoGame.DinoGame, "train", lambda self, *a, **k: None)
    for _ in range(3):
        assert autodino.main(["--sem-janela", "--semente", "4"]) == 0
    assert _treinos(pasta) == ["20261123-101500_s4", "20261123-101500_s4-2", "20261123-101500_s4-3"]
