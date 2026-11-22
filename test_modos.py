"""Testes da spec headless-training-and-watch. Rodam sem janela: python -m pytest test_modos.py -v"""

import inspect
import os
import pickle
import random
import shutil
import subprocess
import sys
import time

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import numpy as np  # noqa: E402
import pygame  # noqa: E402
import pytest  # noqa: E402

import autodino  # noqa: E402
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
    # os quatro itens do HUD, cada um no seu lugar e na sua cor
    VERMELHO, AZUL = (255, 0, 0), (0, 0, 255)
    fonte = pygame.freetype.SysFont("Input", 12)
    vivos = fonte.get_rect("Alive: 5/5")
    vivos.topright = tela.topright
    vivos.move_ip(-2, 2)
    melhor = fonte.get_rect("Best fitness (prev gen): 123")
    melhor.topright = vivos.bottomright
    melhor.move_ip(0, 2)
    sensores = pygame.Rect(2, 2, 250, vivos.height)
    pontos = pygame.Rect(2, sensores.bottom + 2, 120, vivos.height)
    assert vivos.bottom <= melhor.top and sensores.bottom <= pontos.top  # areas separadas
    assert VERMELHO in _cores(jogo.screen, vivos)
    assert VERMELHO in _cores(jogo.screen, melhor)
    assert AZUL in _cores(jogo.screen, sensores)
    assert AZUL in _cores(jogo.screen, pontos)
    # e o texto de cada um
    textos = []
    sysfont = pygame.freetype.SysFont

    class _Fonte:
        def __init__(self, *args):
            self.fonte = sysfont(*args)

        def get_rect(self, texto):
            return self.fonte.get_rect(texto)

        def render_to(self, tela, pos, texto, cor):
            textos.append(texto)
            return self.fonte.render_to(tela, pos, texto, cor)

    monkeypatch.setattr(pygame.freetype, "SysFont", _Fonte)
    with pytest.raises(_Fim):
        jogo.roda_geracao(_redes(5), janela=True)
    ultimo_frame = textos[-4:]
    assert ultimo_frame[0] == "Alive: 5/5"
    assert ultimo_frame[1].startswith("Senses: l: ") and " nl: " in ultimo_frame[1] and " s: " in ultimo_frame[1]
    assert ultimo_frame[2] == "Best fitness (prev gen): 123"
    assert ultimo_frame[3] == "Current Score: 4"  # 28 frames completos // 7
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


def _mesma_rede(a, b):
    return all(np.array_equal(x, y) for x, y in zip(a.pesos + a.bias, b.pesos + b.bias))


def test_carrega_rede_devolve_a_rede_salva(tmp_path):
    rede = RedeNeural.RedeNeural(CFG)
    caminho = str(tmp_path / "rede.din")
    RedeNeural.RedeNeural.save_object(rede, caminho)
    carregada = DinoGame.carrega_rede(caminho)
    assert isinstance(carregada, RedeNeural.RedeNeural)
    assert _mesma_rede(carregada, rede)


def test_carrega_rede_arquivo_inexistente_levanta(tmp_path):
    with pytest.raises(FileNotFoundError):
        DinoGame.carrega_rede(str(tmp_path / "nao_existe.din"))


def test_carrega_rede_arquivo_invalido_levanta(tmp_path):
    outra_topologia = str(tmp_path / "pequena.din")
    RedeNeural.RedeNeural.save_object(RedeNeural.RedeNeural((5, 4, 2)), outra_topologia)
    outro_objeto = str(tmp_path / "lista.din")
    RedeNeural.RedeNeural.save_object([1, 2, 3], outro_objeto)
    nao_pickle = tmp_path / "texto.din"
    nao_pickle.write_text("isto nao e uma rede")
    vazio = tmp_path / "vazio.din"
    vazio.write_bytes(b"")
    for caminho in (outra_topologia, outro_objeto, str(nao_pickle), str(vazio)):
        with pytest.raises(ValueError):
            DinoGame.carrega_rede(caminho)


def _rede_fixa(pula):
    """Rede (5, 8, 4, 2) de pesos zero: a saida so depende do bias da ultima camada."""
    rede = RedeNeural.RedeNeural(CFG)
    for a in rede.pesos + rede.bias:
        a[:] = 0.0
    rede.bias[-1][:] = [[10.0 if pula else -10.0], [-10.0]]  # [pular, abaixar]
    return rede


def _novo_jogo():
    pygame.init()
    pygame.mixer.quit()
    j = DinoGame.DinoGame()
    j.clock = _Relogio()
    return j


CHAO = int(0.98 * DinoGame.DinoGame.height)


def test_assistir_rede_controla_o_dino_a_60_fps(jogo, monkeypatch):
    jogo.clock = _Relogio()
    _grava_pista(monkeypatch, 30)
    with pytest.raises(_Fim):
        jogo.gameplay(rede=_rede_fixa(pula=True))  # nenhuma tecla e enviada
    assert isinstance(jogo.playerDino, DinoGame.Dino)
    assert jogo.playerDino.isJumping and jogo.playerDino.rect.bottom < CHAO
    assert jogo.dinoArray == []  # um unico dino: o do jogador
    assert len(jogo.clock.fps) == 29 and set(jogo.clock.fps) == {60}

    jogo.clock = _Relogio()
    with pytest.raises(_Fim):
        jogo.gameplay(rede=_rede_fixa(pula=False))
    assert not jogo.playerDino.isJumping and jogo.playerDino.rect.bottom == CHAO

    # a rede manda, nao o teclado: ESPACO nao faz pular o dino da rede que nunca pula
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    with pytest.raises(_Fim):
        jogo.gameplay(rede=_rede_fixa(pula=False))
    assert not jogo.playerDino.isJumping and jogo.playerDino.rect.bottom == CHAO


def test_assistir_mostra_pontuacao(jogo, monkeypatch):
    jogo.clock = _Relogio()
    placares = set()
    update = pygame.display.update
    area = DinoGame.Scoreboard().rect

    def fotografa(*args):
        placares.add(pygame.image.tostring(jogo.screen.subsurface(area), "RGB"))
        update(*args)

    monkeypatch.setattr(pygame.display, "update", fotografa)
    _grava_pista(monkeypatch, 100)
    with pytest.raises(_Fim):
        jogo.gameplay(rede=_rede_fixa(pula=False))
    score = jogo.playerDino.score
    assert score == 14  # 1 ponto a cada 7 frames, 99 frames completos
    assert len(placares) == 15  # o placar mostrou cada valor de 0 a 14
    esperado = DinoGame.Scoreboard()
    esperado.update(score)
    na_tela = pygame.image.tostring(jogo.screen.subsurface(esperado.rect), "RGB")
    assert na_tela == pygame.image.tostring(esperado.image, "RGB")


def test_assistir_usa_regras_do_jogo_manual(jogo, monkeypatch):
    esperado = _pista_sozinha(monkeypatch, 21, 1500)
    assert len(esperado) > 10 and any(tipo == "Ptera" for _, tipo, _, _ in esperado)
    assert max(sum(1 for f, t, _, _ in esperado if t == "Cactus" and f0 <= f < f0 + 100) for f0, _, _, _ in esperado) >= 2
    log = _grava_pista(monkeypatch, 1500)
    _sem_colisao(monkeypatch)
    jogo.clock = _Relogio()
    random.seed(21)
    with pytest.raises(_Fim):
        jogo.gameplay(rede=_rede_fixa(pula=True))
    assert log == esperado


def _ate_o_fim_de_jogo(jogo, monkeypatch, na_tela_de_fim):
    """Roda gameplay com a rede que nunca pula; `na_tela_de_fim(n)` e chamada a cada frame da tela de fim."""
    passos = []
    passo = DinoGame.Pista.passo
    fim_de_jogo = DinoGame.DinoGame.disp_gameOver_msg
    chamadas = []

    def conta_passo(self):
        passos.append(self)
        passo(self)

    def tela_de_fim(self, *args):
        fim_de_jogo(self, *args)
        chamadas.append((len(passos), self.playerDino.score))
        na_tela_de_fim(len(chamadas))

    monkeypatch.setattr(DinoGame.Pista, "passo", conta_passo)
    monkeypatch.setattr(DinoGame.DinoGame, "disp_gameOver_msg", tela_de_fim)
    return passos, chamadas


def test_assistir_colisao_mostra_fim_de_jogo(jogo, monkeypatch):
    jogo.clock = _Relogio()

    def para_no_quinto(n):
        if n == 5:
            raise _Fim

    passos, chamadas = _ate_o_fim_de_jogo(jogo, monkeypatch, para_no_quinto)
    random.seed(1)
    with pytest.raises(_Fim):
        jogo.gameplay(rede=_rede_fixa(pula=False))
    assert jogo.playerDino.isDead
    assert 100 < chamadas[0][0] < 200  # morreu no primeiro cacto, que chega perto do frame 139
    # a partida parou: nem a pista nem a pontuacao andam durante a tela de fim
    assert len({p for p, _ in chamadas}) == 1 and len({s for _, s in chamadas}) == 1
    fim = pygame.Rect(0, 0, 190, 11)
    fim.centerx, fim.centery = 300, int(150 * 0.35)
    assert _cores(jogo.screen, fim) != {DinoGame.BG_COLOR}  # o letreiro de fim de jogo esta na tela


@pytest.mark.parametrize("tecla", [pygame.K_SPACE, pygame.K_RETURN])
def test_assistir_espaco_reinicia_com_a_mesma_rede(jogo, monkeypatch, tecla):
    jogo.clock = _Relogio()
    rede = _rede_fixa(pula=False)
    consultas = []
    feed = rede.feedForward
    rede.feedForward = lambda a: consultas.append(len(pistas)) or feed(a)
    pistas, dinos = [], []
    pista_init = DinoGame.Pista.__init__

    def nova_pista(self):
        pistas.append(self)
        dinos.append(jogo.playerDino)
        pista_init(self)

    monkeypatch.setattr(DinoGame.Pista, "__init__", nova_pista)

    def aperta_e_depois_para(n):
        if len(pistas) == 1 and n == 3:
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=tecla))
        if len(pistas) == 2:
            raise _Fim  # a segunda partida tambem chegou ao fim de jogo

    _ate_o_fim_de_jogo(jogo, monkeypatch, aperta_e_depois_para)
    with pytest.raises(_Fim):
        jogo.gameplay(rede=rede)
    assert len(pistas) == 2 and dinos[0] is not dinos[1]  # outra partida, outro dino
    assert consultas.count(1) > 100 and consultas.count(2) > 100  # a mesma rede decidiu nas duas


def test_assistir_esc_encerra_com_codigo_0(monkeypatch):
    sair = [
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
        pygame.event.Event(pygame.QUIT),
    ]
    passo = DinoGame.Pista.passo
    for evento in sair:  # durante a partida
        jogo = _novo_jogo()

        def no_frame_10(self):
            if self.counter == 10:
                pygame.event.post(evento)
            passo(self)

        monkeypatch.setattr(DinoGame.Pista, "passo", no_frame_10)
        with pytest.raises(SystemExit) as saida:
            jogo.gameplay(rede=_rede_fixa(pula=False))
        assert saida.value.code in (None, 0)
        assert not jogo.playerDino.isDead
    monkeypatch.setattr(DinoGame.Pista, "passo", passo)
    for evento in sair:  # na tela de fim de jogo
        jogo = _novo_jogo()
        _ate_o_fim_de_jogo(jogo, monkeypatch, lambda n: n == 2 and pygame.event.post(evento))
        with pytest.raises(SystemExit) as saida:
            jogo.gameplay(rede=_rede_fixa(pula=False))
        assert saida.value.code in (None, 0)
        assert jogo.playerDino.isDead
        monkeypatch.undo()


def _estado_no_primeiro_cacto(jogo, monkeypatch, semente, antes):
    """Duas partidas seguidas (reinicio por ESPACO): estado do random quando nasce o 1o cacto de cada uma."""
    estados = []
    cacto_init = DinoGame.Cactus.__init__
    pistas = []
    pista_init = DinoGame.Pista.__init__

    def nova_pista(self):
        pistas.append(self)
        pista_init(self)

    def espia(self, *args, **kwargs):
        if len(estados) < len(pistas):
            estados.append(random.getstate())
        cacto_init(self, *args, **kwargs)

    def reinicia_uma_vez(n):
        if len(pistas) == 1 and n == 1:
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        if len(pistas) == 2:
            raise _Fim

    monkeypatch.setattr(DinoGame.Pista, "__init__", nova_pista)
    monkeypatch.setattr(DinoGame.Cactus, "__init__", espia)
    _ate_o_fim_de_jogo(jogo, monkeypatch, reinicia_uma_vez)
    random.seed(antes)
    with pytest.raises(_Fim):
        jogo.gameplay(rede=_rede_fixa(pula=False), semente=semente)
    monkeypatch.undo()
    return estados


def _estado_apos_seed(semente):
    random.seed(semente)
    return random.getstate()


def test_assistir_semente_por_partida(jogo, monkeypatch):
    jogo.clock = _Relogio()
    com = _estado_no_primeiro_cacto(jogo, monkeypatch, semente=5, antes=99)
    assert com == [_estado_apos_seed(5), _estado_apos_seed(5)]  # as duas partidas na mesma pista
    jogo = _novo_jogo()
    sem = _estado_no_primeiro_cacto(jogo, monkeypatch, semente=None, antes=99)
    assert sem[0] == _estado_apos_seed(99)  # sem semente, o jogo nao mexe no random
    assert sem[1] not in (_estado_apos_seed(99), _estado_apos_seed(5))  # e a 2a partida e outra pista


def test_tres_modos_mesma_pista(jogo, monkeypatch, tmp_path):
    S, FRAMES = 31, 1500
    _sem_colisao(monkeypatch)
    jogo.clock = _Relogio()

    def roda(f):
        log = _grava_pista(monkeypatch, FRAMES)
        with pytest.raises(_Fim):
            f()
        return list(log)

    def manual():
        random.seed(S)
        jogo.gameplay()

    manual_log = roda(manual)
    assistir_log = roda(lambda: jogo.gameplay(rede=_rede_fixa(pula=True), semente=S))
    # no treino a geracao g usa a semente semente_base + g: base S - 1 da S na geracao 1
    treino_log = roda(lambda: jogo.train(3, 1, semente_base=S - 1, saida=str(tmp_path), janela=False))
    assert len(manual_log) > 10 and any(tipo == "Ptera" for _, tipo, _, _ in manual_log)
    assert manual_log == assistir_log == treino_log


REPO = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def pasta(tmp_path, monkeypatch):
    """Diretorio de trabalho temporario com os sprites: os modos gravam fitness.csv e bestDino.din em '.'."""
    shutil.copytree(os.path.join(REPO, "sprites"), tmp_path / "sprites")
    monkeypatch.chdir(tmp_path)
    pygame.init()
    pygame.mixer.quit()
    return tmp_path


def _processo(pasta, codigo_ou_script, *args):
    """Processo Python novo, sem SDL_VIDEODRIVER no ambiente, na pasta temporaria."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("SDL_")}
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, *codigo_ou_script, *args],
        cwd=pasta, env=env, stdin=subprocess.DEVNULL, capture_output=True, encoding="utf-8", timeout=120,
    )


def test_sem_janela_usa_driver_dummy(pasta):
    codigo = (
        f"import sys; sys.path.insert(0, {REPO!r}); import autodino; "
        "rc = autodino.main(['--sem-janela', '--individuos', '3', '--geracoes', '1']); "
        "import pygame; print('DRIVER=' + pygame.display.get_driver()); sys.exit(rc)"
    )
    p = _processo(pasta, ["-c", codigo])
    assert p.returncode == 0, p.stderr
    assert "DRIVER=dummy" in p.stdout


def test_sem_janela_termina_com_codigo_0(pasta):
    p = _processo(pasta, [os.path.join(REPO, "autodino.py")], "--sem-janela", "--individuos", "10", "--geracoes", "2")
    assert p.returncode == 0, p.stderr  # terminou sozinho: stdin fechado, nenhuma tecla
    linhas = [l for l in p.stdout.splitlines() if l.startswith("Geração")]
    assert [l.split(":")[0] for l in linhas] == ["Geração 1", "Geração 2"]
    csv = (pasta / "fitness.csv").read_text().splitlines()
    assert csv[0] == "geracao,melhor,media" and len(csv) == 3
    assert (pasta / "bestDino.din").exists()


def _espia_treino(monkeypatch):
    """Troca train por um registrador: devolve a lista das chamadas (argumentos nomeados)."""
    chamadas = []

    def train(self, nIndividuals=20, nGenerations=100, semente_base=0, saida=".", janela=True):
        chamadas.append(dict(n=nIndividuals, g=nGenerations, semente=semente_base, janela=janela))

    monkeypatch.setattr(DinoGame.DinoGame, "train", train)
    return chamadas


def test_opcoes_de_treino_sao_usadas(pasta, monkeypatch, capsys):
    # treino de verdade com as opcoes: 7 dinos, 2 geracoes, semente 9
    tamanhos, estados = [], []
    registra = DinoGame.registra_geracao
    cacto_init = DinoGame.Cactus.__init__

    def anota(ranked, *args):
        tamanhos.append(len(ranked))
        return registra(ranked, *args)

    def espia(self, *args, **kwargs):
        if len(estados) == len(tamanhos):  # primeiro cacto da geracao
            estados.append(random.getstate())
        cacto_init(self, *args, **kwargs)

    monkeypatch.setattr(DinoGame, "registra_geracao", anota)
    monkeypatch.setattr(DinoGame.Cactus, "__init__", espia)
    assert autodino.main(["--sem-janela", "--individuos", "7", "--geracoes", "2", "--semente", "9"]) == 0
    assert tamanhos == [7, 7]
    assert estados == [_estado_apos_seed(9 + 1), _estado_apos_seed(9 + 2)]
    monkeypatch.undo()
    # sem as opcoes: 350, 30 e 0, nos dois modos de treino
    monkeypatch.chdir(pasta)
    chamadas = _espia_treino(monkeypatch)
    monkeypatch.setattr(DinoGame.DinoGame, "introscreen", lambda self: False)
    assert autodino.main(["--sem-janela"]) == 0
    assert autodino.main([]) == 0
    assert chamadas == [dict(n=350, g=30, semente=0, janela=False), dict(n=350, g=30, semente=0, janela=True)]
    chamadas.clear()
    assert autodino.main(["--individuos", "12", "--geracoes", "4", "--semente", "3"]) == 0
    assert chamadas == [dict(n=12, g=4, semente=3, janela=True)]


def _espia_assistir(monkeypatch):
    partidas = []
    monkeypatch.setattr(
        DinoGame.DinoGame, "gameplay", lambda self, rede=None, semente=None: partidas.append((rede, semente))
    )
    return partidas


def test_assistir_carrega_o_arquivo_indicado(pasta, monkeypatch):
    padrao, outra = _redes(2, semente=8)
    RedeNeural.RedeNeural.save_object(padrao, "bestDino.din")
    RedeNeural.RedeNeural.save_object(outra, "outro.din")
    partidas = _espia_assistir(monkeypatch)
    assert autodino.main(["--assistir", "outro.din"]) == 0
    assert autodino.main(["--assistir"]) == 0
    assert autodino.main(["--assistir", "outro.din", "--semente", "5"]) == 0
    assert _mesma_rede(partidas[0][0], outra) and not _mesma_rede(partidas[0][0], padrao)
    assert _mesma_rede(partidas[1][0], padrao)
    assert [semente for _, semente in partidas] == [None, None, 5]


def _sem_janela_criada(monkeypatch):
    janelas = []
    set_mode = pygame.display.set_mode
    monkeypatch.setattr(pygame.display, "set_mode", lambda *a, **k: janelas.append(a) or set_mode(*a, **k))
    return janelas


def test_assistir_arquivo_inexistente(pasta, monkeypatch, capsys):
    janelas, partidas = _sem_janela_criada(monkeypatch), _espia_assistir(monkeypatch)
    assert autodino.main(["--assistir", "nao_existe.din"]) == 1
    assert capsys.readouterr().out.splitlines() == ["Arquivo não encontrado: nao_existe.din"]
    assert autodino.main(["--assistir"]) == 1  # o padrao bestDino.din tambem nao existe aqui
    assert capsys.readouterr().out.splitlines() == ["Arquivo não encontrado: bestDino.din"]
    assert janelas == [] and partidas == []


def test_assistir_arquivo_invalido(pasta, monkeypatch, capsys):
    janelas, partidas = _sem_janela_criada(monkeypatch), _espia_assistir(monkeypatch)
    RedeNeural.RedeNeural.save_object(RedeNeural.RedeNeural((5, 4, 2)), "pequena.din")
    (pasta / "texto.din").write_text("isto nao e uma rede")
    for caminho in ("pequena.din", "texto.din"):
        assert autodino.main(["--assistir", caminho]) == 1
        assert capsys.readouterr().out.splitlines() == [f"Arquivo inválido: {caminho}"]
    assert janelas == [] and partidas == []


def test_sem_opcoes_treina_350_por_30_com_janela(pasta, monkeypatch):
    ordem = []
    chamadas = _espia_treino(monkeypatch)
    intro = DinoGame.DinoGame.introscreen

    def tela_inicial(self):
        # a tela inicial de verdade, com o usuario apertando ESPACO
        ordem.append("tela inicial")
        self.clock = _Relogio()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        fechou = intro(self)
        ordem.append("treino liberado" if not fechou else "fechou")
        return fechou

    monkeypatch.setattr(DinoGame.DinoGame, "introscreen", tela_inicial)
    assert autodino.main([]) == 0
    assert ordem == ["tela inicial", "treino liberado"]
    assert chamadas == [dict(n=350, g=30, semente=0, janela=True)]
    # se o usuario fecha a janela na tela inicial, nao ha treino
    chamadas.clear()
    monkeypatch.setattr(DinoGame.DinoGame, "introscreen", lambda self: True)
    assert autodino.main([]) == 0
    assert chamadas == []


@pytest.mark.parametrize("opcao", ["--individuos", "--geracoes"])
@pytest.mark.parametrize("valor", ["0", "-1"])
def test_individuos_ou_geracoes_menor_que_1(pasta, monkeypatch, capsys, opcao, valor):
    chamadas = _espia_treino(monkeypatch)
    for modo in ([], ["--sem-janela"]):
        with pytest.raises(SystemExit) as saida:
            autodino.main([*modo, opcao, valor])
        assert saida.value.code == 2
        assert "usage:" in capsys.readouterr().err
    assert chamadas == []


def test_sem_janela_com_assistir_e_erro(pasta, monkeypatch, capsys):
    chamadas, partidas = _espia_treino(monkeypatch), _espia_assistir(monkeypatch)
    for argv in (["--sem-janela", "--assistir"], ["--assistir", "bestDino.din", "--sem-janela"]):
        with pytest.raises(SystemExit) as saida:
            autodino.main(argv)
        assert saida.value.code == 2
        assert "usage:" in capsys.readouterr().err
    assert chamadas == [] and partidas == []


@pytest.mark.parametrize("evento", ["pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)", "pygame.event.Event(pygame.QUIT)"])
def test_assistir_processo_sai_com_codigo_0(pasta, evento):
    RedeNeural.RedeNeural.save_object(_rede_fixa(pula=False), "rede.din")
    codigo = (
        "import os, sys; os.environ['SDL_VIDEODRIVER'] = 'dummy'; os.environ['SDL_AUDIODRIVER'] = 'dummy'; "
        f"sys.path.insert(0, {REPO!r}); import pygame, autodino, DinoGame; "
        "passo = DinoGame.Pista.passo; "
        f"DinoGame.Pista.passo = lambda self: (self.counter == 10 and pygame.event.post({evento}), passo(self))[1]; "
        "sys.exit(autodino.main(['--assistir', 'rede.din']))"
    )
    p = _processo(pasta, ["-c", codigo])
    assert p.returncode == 0, p.stderr
    assert "Traceback" not in p.stderr


@pytest.mark.parametrize("valor", ["-1", "-4", "4294967296"])
def test_semente_fora_da_faixa_e_erro_de_uso(pasta, monkeypatch, capsys, valor):
    chamadas, partidas = _espia_treino(monkeypatch), _espia_assistir(monkeypatch)
    RedeNeural.RedeNeural.save_object(_rede_fixa(pula=False), "bestDino.din")
    for modo in ([], ["--sem-janela"], ["--assistir"]):
        with pytest.raises(SystemExit) as saida:
            autodino.main([*modo, "--semente", valor])
        assert saida.value.code == 2
        assert "usage:" in capsys.readouterr().err
    assert chamadas == [] and partidas == []
    # os limites da faixa sao aceitos
    monkeypatch.setattr(DinoGame.DinoGame, "introscreen", lambda self: False)
    assert autodino.main(["--semente", "0"]) == 0 and autodino.main(["--semente", "4294967295"]) == 0
    assert [c["semente"] for c in chamadas] == [0, 4294967295]
