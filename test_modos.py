"""Testes da spec headless-training-and-watch. Rodam sem janela: python -m pytest test_modos.py -v"""

import inspect
import os
import pickle
import random
import time

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


def _redes(n, semente=0):
    np.random.seed(semente)
    return [RedeNeural.RedeNeural(CFG) for _ in range(n)]


def test_roda_geracao_devolve_um_par_por_dino(jogo):
    redes = _redes(10)
    random.seed(1)
    ranked = jogo.roda_geracao(redes, janela=False)
    assert len(ranked) == 10
    assert all(sum(r is rede for _, r in ranked) == 1 for rede in redes)
    assert all(isinstance(score, int) and score > 0 for score, _ in ranked)
    assert jogo.dinoArray == []


def _cores(tela, area):
    return {tuple(tela.get_at((x, y)))[:3] for x in range(area.left, area.right) for y in range(area.top, area.bottom)}


def test_treino_com_janela_desenha_dinos_e_hud(jogo, monkeypatch):
    DinoGame.DinoGame.train.currentBest = 123
    SENTINELA = (1, 2, 3)
    # sem janela: a tela nao e tocada
    _grava_pista(monkeypatch, 30)
    jogo.screen.fill(SENTINELA)
    with pytest.raises(_Fim):
        jogo.roda_geracao(_redes(5), janela=False)
    assert _cores(jogo.screen, jogo.screen.get_rect()) == {SENTINELA}
    # com janela: fundo, dino no lugar dele e HUD em vermelho e azul
    jogo.clock = _Relogio()
    jogo.screen.fill(SENTINELA)
    with pytest.raises(_Fim):
        jogo.roda_geracao(_redes(5), janela=True)
    tela = jogo.screen.get_rect()
    todas = _cores(jogo.screen, tela)
    assert SENTINELA not in todas and DinoGame.BG_COLOR in todas
    no_chao = [d for d in jogo.dinoArray if not d.isJumping and not d.isDucking]
    assert no_chao, "ao menos um dino em pe no chao para conferir o desenho"
    assert _cores(jogo.screen, no_chao[0].rect.clip(tela)) != {DinoGame.BG_COLOR}
    hud = pygame.Rect(0, 0, tela.width, 34)  # as duas linhas de texto de cada lado
    assert (255, 0, 0) in _cores(jogo.screen, hud)  # vivos e melhor da geracao anterior
    assert (0, 0, 255) in _cores(jogo.screen, hud)  # sensores e pontuacao
    assert len(jogo.clock.fps) == 29  # um limite de FPS por frame completo; o 30o foi interrompido no meio


def _ms_por_frame(jogo, monkeypatch, janela, frames=120):
    """Mediana do tempo entre passos da pista com 350 dinos vivos (o 1o cacto so chega no frame ~139)."""
    instantes = []
    passo = DinoGame.Pista.passo

    def espia(self):
        instantes.append(time.perf_counter())
        passo(self)
        if self.counter >= frames:
            assert len(jogo.dinoArray) == 350
            raise _Fim

    monkeypatch.setattr(DinoGame.Pista, "passo", espia)
    random.seed(0)
    with pytest.raises(_Fim):
        jogo.roda_geracao(_redes(350), janela=janela)
    monkeypatch.setattr(DinoGame.Pista, "passo", passo)
    return float(np.median(np.diff(instantes))) * 1000


def test_sem_janela_metade_do_tempo(jogo, monkeypatch):
    jogo.clock = _Relogio()
    DinoGame.DinoGame.train.currentBest = 123
    com = np.median([_ms_por_frame(jogo, monkeypatch, True) for _ in range(3)])
    sem = np.median([_ms_por_frame(jogo, monkeypatch, False) for _ in range(3)])
    print(f"com janela {com:.2f} ms/frame, sem janela {sem:.2f} ms/frame, razao {com / sem:.1f}")
    assert sem <= com / 2


def _treina(jogo, monkeypatch, saida, janela, geracoes=3, n=10, semente=4):
    """train() ate o fim. Com janela, o fim e a tela de fim de treino."""
    def fim(*args):
        raise _Fim

    monkeypatch.setattr(DinoGame.DinoGame, "disp_gameOver_msg", fim)
    jogo.clock = _Relogio()
    saida.mkdir()
    if janela:
        with pytest.raises(_Fim):
            jogo.train(nIndividuals=n, nGenerations=geracoes, semente_base=semente, saida=str(saida))
    else:
        assert jogo.train(n, geracoes, semente_base=semente, saida=str(saida), janela=False) is None
    return (saida / "fitness.csv").read_text()


def test_mesmo_csv_com_e_sem_janela(jogo, monkeypatch, tmp_path, capsys):
    com = _treina(jogo, monkeypatch, tmp_path / "com", janela=True)
    sem = _treina(jogo, monkeypatch, tmp_path / "sem", janela=False)
    assert len(com.splitlines()) == 4  # cabecalho + 3 geracoes
    assert sem == com
    outra = _treina(jogo, monkeypatch, tmp_path / "outra", janela=False, semente=5)
    assert outra != com  # a comparacao nao e trivial: outra semente, outro treino


def test_imprime_linha_por_geracao(jogo, monkeypatch, tmp_path, capsys):
    csv = _treina(jogo, monkeypatch, tmp_path / "t", janela=False, geracoes=2)
    linhas = [l for l in capsys.readouterr().out.splitlines() if l.startswith("Geração")]
    esperadas = []
    for dados in csv.splitlines()[1:]:
        g, melhor, media = dados.split(",")
        esperadas.append(f"Geração {g}: melhor={melhor} media={media}")
    assert len(esperadas) == 2
    assert linhas == esperadas


def test_pilha_nao_cresce_entre_geracoes(jogo, monkeypatch, tmp_path, capsys):
    profundidade = {}
    cacto_init = DinoGame.Cactus.__init__

    def espia(self, *args, **kwargs):
        g = DinoGame.DinoGame.train.currentGeneration
        profundidade.setdefault(g, len(inspect.stack()))  # no primeiro obstaculo de cada geracao
        cacto_init(self, *args, **kwargs)

    monkeypatch.setattr(DinoGame.Cactus, "__init__", espia)
    _treina(jogo, monkeypatch, tmp_path / "t", janela=True, geracoes=3)
    assert sorted(profundidade) == [1, 2, 3]
    assert profundidade[1] == profundidade[2] == profundidade[3]


def test_sem_janela_interrompido_mantem_melhor(jogo, monkeypatch, tmp_path, capsys):
    registra = DinoGame.registra_geracao
    geracoes = []

    def anota(ranked, *args):
        geracoes.append(list(ranked))
        return registra(ranked, *args)

    passo = DinoGame.Pista.passo

    def ctrl_c_na_geracao_2(self):
        if DinoGame.DinoGame.train.currentGeneration == 2 and self.counter == 20:
            raise KeyboardInterrupt
        passo(self)

    monkeypatch.setattr(DinoGame, "registra_geracao", anota)
    monkeypatch.setattr(DinoGame.Pista, "passo", ctrl_c_na_geracao_2)
    with pytest.raises(KeyboardInterrupt):
        jogo.train(10, 3, semente_base=4, saida=str(tmp_path), janela=False)
    assert len(geracoes) == 1
    melhor = max(geracoes[0], key=lambda par: par[0])[1]
    with open(tmp_path / "bestDino.din", "rb") as f:
        salva = pickle.load(f)
    assert all(np.array_equal(a, b) for a, b in zip(salva.pesos + salva.bias, melhor.pesos + melhor.bias))
