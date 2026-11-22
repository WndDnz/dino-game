"""Testes da spec ga-training-fixes. Rodam sem janela: python -m pytest test_ga.py -v"""

import os
import pickle
import random

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import numpy as np  # noqa: E402
import pygame  # noqa: E402
import pytest  # noqa: E402

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


def test_elite_proporcional_ao_n_recebido(capsys):
    ag = _ag(50, elite=0.1)  # AG montado para 50, mas recebe 30 pares: elite = int(30 * 0.1) = 3
    ag.taxaMutacao = 1.0
    atual = _geracao(30)
    nova = ag.proximaGeracao(atual)
    assert len(nova) == 30
    intactas = [rede for _, rede in atual if any(_iguais(r, rede) for r in nova)]
    assert len(intactas) == 3
    assert all(a is b for a, b in zip(intactas, [rede for _, rede in atual[-3:]]))


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
    assert int(50 * 0.01) == 0
    ag.taxaMutacao = 1.0  # todo filho sai diferente dos pais; uma copia de elite sairia igual
    atual = _geracao(50)
    nova = ag.proximaGeracao(atual)
    assert len(nova) == 50
    assert not any(_iguais(r, rede) for r in nova for _, rede in atual)


@pytest.fixture
def jogo():
    """Tela dummy e grupos de sprites, como train() monta."""
    pygame.init()  # um teste de treino pode ter encerrado o pygame
    pygame.mixer.quit()  # sem som nos testes
    j = DinoGame.DinoGame()
    DinoGame.Cactus.containers = pygame.sprite.Group()
    DinoGame.Ptera.containers = pygame.sprite.Group()
    return j


def _cena():
    """Dino com a borda direita em x=84, cacto de 384 a 424, ptera a partir de 444 com base em y=90."""
    dino = DinoGame.Dino(44, 47)
    dino.rect.right = 84
    cac = DinoGame.Cactus(4, 40, 40)
    cac.rect.left = 384
    pte = DinoGame.Ptera(4, 40, 40)
    pte.rect.left, pte.rect.bottom = 444, 90
    return dino, cac, pte


def test_sensores_normalizados(jogo):
    dino, cac, pte = _cena()
    assert cac.rect.right == 424
    s = DinoGame.sensores(dino, cac, pte, 8)
    assert s.shape == (5, 1)
    assert s.ravel() == pytest.approx(
        [(384 - 84) / 600, (444 - 84) / 600, 90 / 150, (424 - 444) / 600, 8 / 20]
    )


def test_sensor_sem_cacto(jogo):
    dino, _, pte = _cena()
    assert DinoGame.sensores(dino, None, pte, 4)[0][0] == 1.0


def test_sensor_sem_ptera(jogo):
    dino, cac, _ = _cena()
    s = DinoGame.sensores(dino, cac, None, 4).ravel()
    assert (s[1], s[2], s[3]) == (1.0, 0.0, 0.0)


def test_sensores_do_proprio_dino(jogo):
    dino, cac, pte = _cena()
    outro = DinoGame.Dino(44, 47)
    outro.rect.right = 99  # 15 px mais a frente, como um dino abaixado
    l1 = DinoGame.sensores(dino, cac, pte, 4)[0][0]
    l2 = DinoGame.sensores(outro, cac, pte, 4)[0][0]
    assert l1 == pytest.approx(300 / 600)
    assert l2 == pytest.approx(285 / 600)


def test_limiar_05(jogo):
    pula = DinoGame.Dino(44, 47)
    pula.agir(np.array([[0.51], [0.49]]))
    assert pula.isJumping is True and pula.isDucking is False
    abaixa = DinoGame.Dino(44, 47)
    abaixa.agir(np.array([[0.49], [0.51]]))
    assert abaixa.isJumping is False and abaixa.isDucking is True


def test_pulo_sem_mixer(jogo):
    pygame.mixer.quit()
    assert pygame.mixer.get_init() is None
    dino = DinoGame.Dino(44, 47)
    assert dino.rect.bottom == int(0.98 * DinoGame.DinoGame.height)  # no chao
    dino.agir(np.array([[0.9], [0.1]]))
    assert dino.movement[1] == -dino.jumpSpeed


def test_colisoes_mesmo_frame(jogo):
    dinos = [DinoGame.Dino(44, 47) for _ in range(10)]
    for i, d in enumerate(dinos):
        d.score, d.brain = i, RedeNeural.RedeNeural(CFG)
    redes = [d.brain for d in dinos]
    cac = DinoGame.Cactus(4, 40, 40)
    cac.rect.left = dinos[0].rect.left  # cacto em cima dos 10 dinos
    no_ar = DinoGame.Dino(44, 47)  # este pulou: nao colide e deve continuar vivo
    no_ar.rect.bottom, no_ar.brain = 20, RedeNeural.RedeNeural(CFG)
    vivos, ranked = dinos + [no_ar], []
    DinoGame.remove_colididos(vivos, cac, ranked)
    assert vivos == [no_ar]
    assert len(ranked) == 10
    assert [score for score, _ in ranked] == list(range(10))
    assert all(sum(r is rede for _, r in ranked) == 1 for rede in redes)


def _salva(tmp_path):
    with open(tmp_path / "bestDino.din", "rb") as f:
        return pickle.load(f)


def test_csv_linha_por_geracao(tmp_path):
    g1 = [(10, RedeNeural.RedeNeural(CFG)), (30, RedeNeural.RedeNeural(CFG))]
    g2 = [(50, RedeNeural.RedeNeural(CFG)), (20, RedeNeural.RedeNeural(CFG))]
    recorde = DinoGame.registra_geracao(g1, 1, None, str(tmp_path))
    DinoGame.registra_geracao(g2, 2, recorde, str(tmp_path))
    linhas = (tmp_path / "fitness.csv").read_text().splitlines()
    assert linhas[0] == "geracao,melhor,media"
    assert [linha.split(",") for linha in linhas[1:]] == [["1", "30", "20.0"], ["2", "50", "35.0"]]


def test_salva_melhor_de_todos(tmp_path):
    melhor, pior = RedeNeural.RedeNeural(CFG), RedeNeural.RedeNeural(CFG)
    recorde = DinoGame.registra_geracao([(10, pior), (30, melhor)], 1, None, str(tmp_path))
    assert recorde == 30
    assert _iguais(_salva(tmp_path), melhor)
    # geracao seguinte pior: recorde e arquivo ficam como estavam
    outra = RedeNeural.RedeNeural(CFG)
    assert DinoGame.registra_geracao([(25, outra)], 2, recorde, str(tmp_path)) == 30
    assert _iguais(_salva(tmp_path), melhor)
    # empate nao e recorde
    assert DinoGame.registra_geracao([(30, outra)], 3, recorde, str(tmp_path)) == 30
    assert _iguais(_salva(tmp_path), melhor)
    # novo recorde regrava
    assert DinoGame.registra_geracao([(31, outra)], 4, recorde, str(tmp_path)) == 31
    assert _iguais(_salva(tmp_path), outra)


class _FimDoTreino(Exception):
    pass


def _treina(jogo, monkeypatch, saida, geracoes, semente_base=0):
    """Roda train() sem janela e sem limite de FPS ate a tela de fim de treino."""
    def fim(*args):
        raise _FimDoTreino

    monkeypatch.setattr(DinoGame.DinoGame, "FPS", 0)
    monkeypatch.setattr(DinoGame.DinoGame, "disp_gameOver_msg", fim)
    np.random.seed(0)
    with pytest.raises(_FimDoTreino):
        jogo.train(nIndividuals=10, nGenerations=geracoes, semente_base=semente_base, saida=str(saida))


def test_semente_por_geracao(jogo, monkeypatch, tmp_path, capsys):
    estados = []  # (geracao, estado do random quando nasce o primeiro obstaculo)
    cacto_init = DinoGame.Cactus.__init__

    def espia(self, *args, **kwargs):
        g = DinoGame.DinoGame.train.currentGeneration
        if g not in [e[0] for e in estados]:
            estados.append((g, random.getstate()))
        cacto_init(self, *args, **kwargs)

    monkeypatch.setattr(DinoGame.Cactus, "__init__", espia)
    csvs = []
    for nome in ("a", "b"):
        (tmp_path / nome).mkdir()
        _treina(jogo, monkeypatch, tmp_path / nome, geracoes=2, semente_base=7)
        csvs.append((tmp_path / nome / "fitness.csv").read_text())
    # o primeiro obstaculo da geracao g nasce com o random recem-semeado em semente_base + g
    assert [g for g, _ in estados[:2]] == [1, 2]
    for g, estado in estados[:2]:
        random.seed(7 + g)
        assert estado == random.getstate()
    # mesma semente, mesmo treino
    assert len(csvs[0].splitlines()) == 3
    assert csvs[0] == csvs[1]


def test_treino_interrompido_mantem_melhor(jogo, monkeypatch, tmp_path, capsys):
    registra = DinoGame.registra_geracao
    geracoes = []

    def registra_e_fecha_a_janela(ranked, *args):
        geracoes.append(list(ranked))
        recorde = registra(ranked, *args)
        pygame.event.post(pygame.event.Event(pygame.QUIT))  # usuario fecha apos a 1a geracao
        return recorde

    monkeypatch.setattr(DinoGame, "registra_geracao", registra_e_fecha_a_janela)
    monkeypatch.setattr(DinoGame.DinoGame, "FPS", 0)
    np.random.seed(0)
    with pytest.raises(SystemExit):
        jogo.train(nIndividuals=10, nGenerations=3, saida=str(tmp_path))
    assert len(geracoes) == 1
    melhor = max(geracoes[0], key=lambda par: par[0])[1]
    assert _iguais(_salva(tmp_path), melhor)
    assert len((tmp_path / "fitness.csv").read_text().splitlines()) == 2
