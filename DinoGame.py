#!/usr/bin/python3

import os
import pickle
import pygame
import pygame.freetype
import random
import numpy as np
import RedeNeural
import AGMLP
import math
import concurrent.futures
import functools

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BG_COLOR = (235, 235, 235)

pygame.mixer.pre_init(44100, -16, 2, 2048)  # fix audio delay
pygame.init()


class DinoGame:
    scr_size = (width, height) = (600, 150)
    accel = 1
    FPS = 60
    gravity = 0.65
    high_score = 0
    checkPoint_sound = pygame.mixer.Sound("sprites/checkPoint.wav")
    jump_sound = pygame.mixer.Sound("sprites/jump.wav")
    die_sound = pygame.mixer.Sound("sprites/die.wav")

    def __init__(self):
        self.screen = pygame.display.set_mode(self.scr_size)
        folha.cache_clear()  # sprites são convertidos para a tela atual
        self.clock = pygame.time.Clock()
        self.dinoArray = []
        self.playerDino = None
        pygame.display.set_caption("T-Rex Rush")

    @staticmethod
    def load_image(
        # self,
        name,
        sizex=-1,
        sizey=-1,
        colorkey=None,
    ):
        fullname = os.path.join("sprites", name)
        image = pygame.image.load(fullname)
        image = image.convert()
        if colorkey is not None:
            if colorkey == -1:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)

        if sizex != -1 or sizey != -1:
            image = pygame.transform.scale(image, (sizex, sizey))

        return (image, image.get_rect())

    @staticmethod
    def load_sprite_sheet(
        # self,
        sheetname,
        nx,
        ny,
        scalex=-1,
        scaley=-1,
        colorkey=None,
    ):
        fullname = os.path.join("sprites", sheetname)
        sheet = pygame.image.load(fullname)
        sheet = sheet.convert()

        sheet_rect = sheet.get_rect()

        sprites = []

        sizex = sheet_rect.width / nx
        sizey = sheet_rect.height / ny

        for i in range(0, ny):
            for j in range(0, nx):
                rect = pygame.Rect((j * sizex, i * sizey, sizex, sizey))
                image = pygame.Surface(rect.size)
                image = image.convert()
                image.blit(sheet, (0, 0), rect)

                if colorkey is not None:
                    if colorkey == -1:
                        colorkey = image.get_at((0, 0))
                    image.set_colorkey(colorkey, pygame.RLEACCEL)

                if scalex != -1 or scaley != -1:
                    image = pygame.transform.scale(image, (scalex, scaley))

                sprites.append(image)

        sprite_rect = sprites[0].get_rect()

        return sprites, sprite_rect

    def disp_gameOver_msg(self, retbutton_image, gameover_image):
        retbutton_rect = retbutton_image.get_rect()
        retbutton_rect.centerx = self.width / 2
        retbutton_rect.top = self.height * 0.52

        gameover_rect = gameover_image.get_rect()
        gameover_rect.centerx = self.width / 2
        gameover_rect.centery = self.height * 0.35

        self.screen.blit(retbutton_image, retbutton_rect)
        self.screen.blit(gameover_image, gameover_rect)

    @staticmethod
    def extractDigits(number):
        if number > -1:
            digits = []
            i = 0
            while number // 10 != 0:
                digits.append(number % 10)
                number = number // 10

            digits.append(number % 10)
            for i in range(len(digits), 5):
                digits.append(0)
            digits.reverse()
            return digits

    def introscreen(self):
        temp_dino = Dino(44, 47)
        temp_dino.isBlinking = True
        gameStart = False

        callout, callout_rect = self.load_image("call_out.png", 196, 45, -1)
        callout_rect.left = self.width * 0.05
        callout_rect.top = self.height * 0.4

        temp_ground, temp_ground_rect = self.load_sprite_sheet(
            "ground.png", 15, 1, -1, -1, -1
        )
        temp_ground_rect.left = self.width / 20
        temp_ground_rect.bottom = self.height

        logo, logo_rect = self.load_image("logo.png", 240, 40, -1)
        logo_rect.centerx = self.width * 0.6
        logo_rect.centery = self.height * 0.6
        while not gameStart:
            if pygame.display.get_surface() is None:
                print("Couldn't load display surface")
                return True
            else:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return True
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                            temp_dino.isJumping = True
                            temp_dino.isBlinking = False
                            temp_dino.movement[1] = -1 * temp_dino.jumpSpeed

            temp_dino.update()

            if pygame.display.get_surface() is not None:
                self.screen.fill(BG_COLOR)
                self.screen.blit(temp_ground[0], temp_ground_rect)
                if temp_dino.isBlinking:
                    self.screen.blit(logo, logo_rect)
                    self.screen.blit(callout, callout_rect)
                temp_dino.draw(self.screen)

                pygame.display.update()

            self.clock.tick(self.FPS)
            if temp_dino.isJumping is False and temp_dino.isBlinking is False:
                gameStart = True

    def gameplay(self):
        DinoGame.FPS = 60
        startMenu = False
        gameOver = False
        gameQuit = False
        self.playerDino = Dino(44, 47)
        pista = Pista()
        scb = Scoreboard()
        highsc = Scoreboard(self.width * 0.78)

        retbutton_image, retbutton_rect = self.load_image(
            "replay_button.png", 35, 31, -1
        )
        gameover_image, gameover_rect = self.load_image("game_over.png", 190, 11, -1)

        temp_images, temp_rect = self.load_sprite_sheet(
            "numbers.png", 12, 1, 11, int(11 * 6 / 5), -1
        )
        HI_image = pygame.Surface((22, int(11 * 6 / 5)))
        HI_rect = HI_image.get_rect()
        HI_image.fill(BG_COLOR)
        HI_image.blit(temp_images[10], temp_rect)
        temp_rect.left += temp_rect.width
        HI_image.blit(temp_images[11], temp_rect)
        HI_rect.top = self.height * 0.1
        HI_rect.left = self.width * 0.73

        while not gameQuit:
            while startMenu:
                pass
            while not gameOver:
                if pygame.display.get_surface() is None:
                    print("Couldn't load display surface")
                    gameQuit = True
                    gameOver = True
                else:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            gameQuit = True
                            gameOver = True

                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_SPACE:
                                if self.playerDino.rect.bottom == int(
                                    
                                    0.98 * self.height
                                
                                ):
                                    self.playerDino.isJumping = True
                                    if pygame.mixer.get_init() is not None:
                                        DinoGame.jump_sound.play()
                                    self.playerDino.movement[1] = (
                                        -1 * self.playerDino.jumpSpeed
                                    )
                                    self.playerDino.movement[1] = (
                                        -1 * self.playerDino.jumpSpeed
                                    )

                            if event.key == pygame.K_DOWN:
                                if not (
                                    
                                    self.playerDino.isJumping and self.playerDino.isDead
                                
                                ):
                                    self.playerDino.isDucking = True

                            if event.key == pygame.K_q:
                                gameQuit = True
                                gameOver = True

                        if event.type == pygame.KEYUP:
                            if event.key == pygame.K_DOWN:
                                self.playerDino.isDucking = False
                for obstaculo in (*pista.cacti, *pista.pteras):
                    if pygame.sprite.collide_mask(self.playerDino, obstaculo):
                        self.playerDino.isDead = True
                        if pygame.mixer.get_init() is not None:
                            DinoGame.die_sound.play()

                pista.passo()
                self.playerDino.update()
                scb.update(self.playerDino.score)
                highsc.update(self.high_score)

                if pygame.display.get_surface() is not None:
                    self.screen.fill(BG_COLOR)
                    pista.desenha(self.screen)
                    scb.draw(self.screen)
                    if self.high_score != 0:
                        highsc.draw(self.screen)
                        self.screen.blit(HI_image, HI_rect)
                    self.playerDino.draw(self.screen)

                    pygame.display.update()
                self.clock.tick(self.FPS)

                if self.playerDino.isDead:
                    gameOver = True
                    if self.playerDino.score > DinoGame.high_score:
                        DinoGame.high_score = self.playerDino.score

            if gameQuit:
                break

            while gameOver:
                if pygame.display.get_surface() is None:
                    print("Couldn't load display surface")
                    gameQuit = True
                    gameOver = False
                else:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            gameQuit = True
                            gameOver = False
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                gameQuit = True
                                gameOver = False
                            if (
                                event.key == pygame.K_RETURN
                                or event.key == pygame.K_SPACE
                            ):
                                gameOver = False
                                self.gameplay()
 
                highsc.update(DinoGame.high_score)
                if pygame.display.get_surface() is not None:
                    self.disp_gameOver_msg(retbutton_image, gameover_image)
                    if DinoGame.high_score != 0:
                        highsc.draw(self.screen)
                        self.screen.blit(HI_image, HI_rect)
                    pygame.display.update()
                self.clock.tick(self.FPS)

        pygame.quit()
        quit()

    def roda_geracao(self, redes, janela=True):
        """
        Simula uma geração na Pista até todos os dinos morrerem e devolve a lista
        [(score, rede)]. Com `janela`, trata eventos, desenha os dinos e o HUD e
        limita o FPS; devolve None se o usuário fechou. Sem `janela`, só simula.
        """
        self.dinoArray.clear()
        for rede in redes:
            dino = Dino(44, 47)
            dino.brain = rede
            self.dinoArray.append(dino)
        indice = {id(d): i for i, d in enumerate(self.dinoArray)}
        W, B = RedeNeural.RedeNeural.empilha(redes)
        ranked = []
        pista = Pista()
        ft_font = pygame.freetype.SysFont("Input", 12) if janela else None
        cac = pte = None
        senses = (0, 0, 0, 0, 0)

        while self.dinoArray:
            if janela and not self._eventos_treino():
                return None

            for obstaculo in (*pista.cacti, *pista.pteras):
                remove_colididos(self.dinoArray, obstaculo, ranked)

            if self.dinoArray:
                # todos os dinos têm a mesma borda esquerda: o cacto à frente é um só
                cac = cacto_a_frente(self.dinoArray[0], pista.cacti)
                pte = min(pista.pteras, key=lambda p: p.rect.left, default=None)
                entradas = np.stack(
                    [sensores(d, cac, pte, pista.gamespeed) for d in self.dinoArray]
                )
                vivos = [indice[id(d)] for d in self.dinoArray]
                acoes = RedeNeural.RedeNeural.feed_forward_lote(
                    [w[vivos] for w in W], [b[vivos] for b in B], entradas
                )
                for dino, acao in zip(self.dinoArray, acoes):
                    dino.agir(acao)
                senses = entradas[-1].ravel()

            pista.passo()
            for dino in self.dinoArray:
                dino.update()

            if janela:
                self._desenha_treino(pista, ft_font, len(redes), senses, cac or pte)
                self.clock.tick(self.FPS)
        return ranked

    def _eventos_treino(self):
        """Eventos do treino com janela. Devolve False se o usuário pediu para sair."""
        if pygame.display.get_surface() is None:
            print("Couldn't load display surface")
            return False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return False
                if event.key == pygame.K_RIGHT:
                    DinoGame.accel += 1
                    DinoGame.FPS *= DinoGame.accel
                if event.key == pygame.K_LEFT:
                    DinoGame.accel -= 1
                    DinoGame.FPS *= DinoGame.accel
        return True

    def _desenha_treino(self, pista, ft_font, nIndividuals, senses, ha_obstaculo):
        """Pista, dinos vivos e HUD: vivos, melhor da geração anterior, sensores e pontuação."""
        l, nl, na, ds, s = senses
        tela = self.screen.get_rect()

        alive = f"Alive: {len(self.dinoArray)}/{nIndividuals}"
        alive_rect = ft_font.get_rect(alive)
        alive_rect.topright = tela.topright
        alive_rect.move_ip(-2, 2)

        best = f"Best fitness (prev gen): {DinoGame.train.currentBest}"
        best_rect = ft_font.get_rect(best)
        best_rect.topright = alive_rect.bottomright
        best_rect.move_ip(0, 2)

        sens = f"Senses: l: {l:.2f} nl: {nl:.2f} na: {na:.2f} d: {ds:.2f} s: {s}"
        sens_rect = ft_font.get_rect(sens)
        sens_rect.topleft = tela.topleft
        sens_rect.move_ip(2, 2)

        scr = f"Current Score: {pista.counter // 7}"
        scr_rect = ft_font.get_rect(scr)
        scr_rect.topleft = sens_rect.bottomleft
        scr_rect.move_ip(0, 2)

        self.screen.fill(BG_COLOR)
        pista.desenha(self.screen)
        for d in self.dinoArray:
            d.draw(self.screen)
        ft_font.render_to(self.screen, alive_rect.topleft, alive, (255, 0, 0))
        if ha_obstaculo:
            ft_font.render_to(self.screen, sens_rect.topleft, sens, (0, 0, 255))
        if DinoGame.train.currentBest is not None:
            ft_font.render_to(self.screen, best_rect.topleft, best, (255, 0, 0))
        ft_font.render_to(self.screen, scr_rect.topleft, scr, (0, 0, 255))
        pygame.display.update()

    def train(
        self,
        nIndividuals=20,
        nGenerations=100,
        semente_base=0,
        saida=".",
        janela=True,
    ):
        """
        Treina `nIndividuals` redes por `nGenerations` gerações. Com `janela`, mostra
        o treino e, ao fim, a tela de fim de treino. Sem `janela`, imprime uma linha
        por geração e retorna depois da última.
        """
        DinoGame.train.currentGeneration = 1
        DinoGame.train.currentBest = None
        DinoGame.train.recorde = None
        np.random.seed(semente_base)  # população inicial, crossover e mutação
        if os.path.exists(os.path.join(saida, "fitness.csv")):
            os.remove(os.path.join(saida, "fitness.csv"))
        ag = AGMLP.RNA_AG(
            (5, 8, 4, 2),
            None,
            0.1,
            nIndividuals,
            nGenerations,
            taxaMutacao=0.05,
            elite=0.1,
        )
        redes = ag.iniciaPopulacao()

        for geracao in range(1, nGenerations + 1):
            DinoGame.train.currentGeneration = geracao
            # pista reproduzível: mesma semente, mesma sequência de obstáculos
            random.seed(semente_base + geracao)
            if janela:
                print(f"Starting generation {geracao}.")
            ranked = self.roda_geracao(redes, janela)
            if ranked is None:  # o usuário fechou a janela
                pygame.quit()
                quit()
            DinoGame.train.recorde = registra_geracao(
                ranked, geracao, DinoGame.train.recorde, saida
            )
            melhor = max(score for score, _ in ranked)
            DinoGame.train.currentBest = melhor
            if not janela:
                media = sum(score for score, _ in ranked) / len(ranked)
                print(f"Geração {geracao}: melhor={melhor} media={media}")
            if geracao < nGenerations:
                redes = ag.proximaGeracao(ranked)

        if not janela:
            return
        if self._fim_do_treino():
            return self.train(nIndividuals, nGenerations, semente_base, saida, janela)
        pygame.quit()
        quit()

    def _fim_do_treino(self):
        """Tela de fim do treino com janela. Devolve True se o usuário pediu outro treino."""
        retbutton_image, _ = self.load_image("replay_button.png", 35, 31, -1)
        gameover_image, _ = self.load_image("game_over.png", 190, 11, -1)
        while True:
            if pygame.display.get_surface() is None:
                print("Couldn't load display surface")
                return False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return True
            self.disp_gameOver_msg(retbutton_image, gameover_image)
            pygame.display.update()
            self.clock.tick(self.FPS)

    def start(self, nIndividuals=None, nGenerations=None, train=False, auto=False):
        isGameQuit = self.introscreen()
        if not isGameQuit:
            if train and nIndividuals is not None:
                print("Starting training.")
                DinoGame.train.currentGeneration = 1
                DinoGame.train.currentBest = None
                self.train(nIndividuals=nIndividuals, nGenerations=nGenerations)
            elif auto:
                self.gameplay()
            else:
                self.gameplay()


@functools.lru_cache(maxsize=None)
def folha(sheetname, nx, ny, scalex, scaley):
    """Folha de sprites carregada uma vez por tela: (imagens, máscaras de colisão)."""
    imagens, _ = DinoGame.load_sprite_sheet(sheetname, nx, ny, scalex, scaley, -1)
    return imagens, [pygame.mask.from_surface(imagem) for imagem in imagens]


class Pista:
    """
    Obstáculos, nuvens, chão, velocidade e contador de frames. É a mesma pista para
    o jogo manual, o treino e o modo assistir (AD-007): até 2 cactos na tela, ptera
    depois de 700 frames, velocidade +1 a cada 700 frames, e todo obstáculo novo
    nasce a pelo menos DIST_MIN px dos que já estão na tela.
    """

    DIST_MIN = 160

    def __init__(self):
        self.gamespeed = 4
        self.counter = 0
        self.ground = Ground(-1 * self.gamespeed)
        self.cacti = pygame.sprite.Group()
        self.pteras = pygame.sprite.Group()
        self.clouds = pygame.sprite.Group()
        self.last_obstacle = pygame.sprite.Group()
        Cactus.containers = self.cacti
        Ptera.containers = self.pteras
        Cloud.containers = self.clouds

    def _cabe(self, largura):
        """Um obstáculo de `largura` px nasce em width + largura: cabe se fica longe de todos."""
        esquerda = DinoGame.width + largura
        return all(
            esquerda - o.rect.right >= self.DIST_MIN
            for o in (*self.cacti, *self.pteras)
        )

    def passo(self):
        """Um frame: cria obstáculos e nuvens, move tudo e acelera a cada 700 frames."""
        for o in (*self.cacti, *self.pteras):
            o.movement[0] = -1 * self.gamespeed

        if len(self.cacti) < 2:
            if len(self.cacti) == 0:
                # sem a checagem, o cacto nascia em cima de um ptera recém-criado
                if self._cabe(40):
                    self.last_obstacle.empty()
                    self.last_obstacle.add(Cactus(self.gamespeed, 40, 40))
            else:
                for last in self.last_obstacle:
                    if (
                        last.rect.right < DinoGame.width * 0.7
                        and random.randrange(0, 50) == 10
                        and self._cabe(40)
                    ):
                        self.last_obstacle.empty()
                        self.last_obstacle.add(Cactus(self.gamespeed, 40, 40))

        if (
            len(self.pteras) == 0
            and random.randrange(0, 200) == 10
            and self.counter > 700
        ):
            for last in self.last_obstacle:
                if last.rect.right < DinoGame.width * 0.8 and self._cabe(46):
                    self.last_obstacle.empty()
                    self.last_obstacle.add(Ptera(self.gamespeed, 46, 40))

        if len(self.clouds) < 5 and random.randrange(0, 300) == 10:
            Cloud(
                DinoGame.width,
                random.randrange(DinoGame.height // 5, DinoGame.height // 2),
            )

        self.cacti.update()
        self.pteras.update()
        self.clouds.update()
        self.ground.update()

        if self.counter % 700 == 699:
            self.ground.speed -= 1
            self.gamespeed += 1
        self.counter += 1

    def desenha(self, screen):
        self.ground.draw(screen)
        self.clouds.draw(screen)
        self.cacti.draw(screen)
        self.pteras.draw(screen)


def carrega_rede(caminho):
    """
    A RedeNeural salva em `caminho`. FileNotFoundError se o arquivo não existe;
    ValueError se não for uma rede de topologia (5, 8, 4, 2).
    O arquivo é pickle: abrir um arquivo de terceiros executa código.
    """
    with open(caminho, "rb") as f:
        try:
            rede = pickle.load(f)
        except Exception as erro:  # pickle levanta tipos variados para arquivo corrompido
            raise ValueError(caminho) from erro
    if not isinstance(rede, RedeNeural.RedeNeural) or tuple(rede.tamanhos) != (5, 8, 4, 2):
        raise ValueError(caminho)
    return rede


def cacto_a_frente(dino, cacti):
    """O cacto mais próximo que ainda não passou pelo dino, ou None (AD-007)."""
    a_frente = [c for c in cacti if c.rect.right >= dino.rect.left]
    return min(a_frente, key=lambda c: c.rect.left, default=None)


def sensores(dino, cac, pte, gamespeed):
    """
    Entrada (5,1) da rede, normalizada (AD-005): distância ao cacto, distância ao
    ptera, altura do ptera, distância cacto->ptera e velocidade. Distâncias medidas
    a partir do próprio dino; sem obstáculo, a distância vale 1.0 (borda da tela).
    """
    w, h = DinoGame.width, DinoGame.height
    l = (cac.rect.left - dino.rect.right) / w if cac is not None else 1.0
    nl = (pte.rect.left - dino.rect.right) / w if pte is not None else 1.0
    na = pte.rect.bottom / h if pte is not None else 0.0
    if cac is not None and pte is not None:
        ds = (cac.rect.right - pte.rect.left) / w
    else:
        ds = 0.0
    return np.array([[l], [nl], [na], [ds], [gamespeed / 20]])


def remove_colididos(dinos, obstaculo, ranked):
    """
    Tira de `dinos` todos os que colidem com `obstaculo` e registra (score, rede)
    de cada um em `ranked`. Itera sobre uma cópia: remover durante a iteração
    pulava o dino seguinte.
    """
    for d in dinos[:]:
        if pygame.sprite.collide_mask(d, obstaculo):
            d.isDead = True
            ranked.append((d.score, d.brain))
            dinos.remove(d)
            if pygame.mixer.get_init() is not None:
                DinoGame.die_sound.play()


def registra_geracao(ranked, geracao, melhor_score, saida="."):
    """
    Acrescenta `geracao,melhor,media` a fitness.csv e salva a melhor rede da geração
    em bestDino.din quando ela supera `melhor_score` (None = ainda não há recorde).
    Devolve o recorde atualizado.
    """
    score, rede = max(ranked, key=lambda par: par[0])
    media = sum(s for s, _ in ranked) / len(ranked)
    caminho = os.path.join(saida, "fitness.csv")
    novo = not os.path.exists(caminho)
    with open(caminho, "a") as f:
        if novo:
            f.write("geracao,melhor,media\n")
        f.write(f"{geracao},{score},{media}\n")
    if melhor_score is None or score > melhor_score:
        RedeNeural.RedeNeural.save_object(rede, os.path.join(saida, "bestDino.din"))
        return score
    return melhor_score


class Dino:
    def __init__(self, sizex=-1, sizey=-1):
        self.images, self.masks = folha("dino.png", 5, 1, sizex, sizey)
        self.images1, self.masks1 = folha("dino_ducking.png", 2, 1, 59, sizey)
        self.rect = self.images[0].get_rect()
        self.rect1 = self.images1[0].get_rect()
        self.rect.bottom = int(0.98 * DinoGame.height)
        self.rect.left = DinoGame.width / 15
        self.image = self.images[0]
        self.mask = self.masks[0]  # usada por pygame.sprite.collide_mask
        self.index = 0
        self.counter = 0
        self.score = 0
        self.isJumping = False
        self.isDead = False
        self.isDucking = False
        self.isBlinking = False
        self.movement = [0, 0]
        self.jumpSpeed = 11.5
        self.brain = None

        self.stand_pos_width = self.rect.width
        self.duck_pos_width = self.rect1.width

    def getAction(self, senses):
        if isinstance(senses, np.ndarray):
            if senses.shape == (5, 1):
                return self.brain.feedForward(senses)
        else:
            return None

    def agir(self, action):
        """Aplica a saída (2,1) da rede, [pular, abaixar]: dispara acima de 0.5."""
        self.isDucking = bool(action[1][0] > 0.5)
        if action[0][0] > 0.5 and not self.isJumping:
            self.isJumping = True
            self.movement[1] = -1 * self.jumpSpeed
            if pygame.mixer.get_init() is not None:
                DinoGame.jump_sound.play()

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def checkbounds(self):
        if self.rect.bottom > int(0.98 * DinoGame.height):
            self.rect.bottom = int(0.98 * DinoGame.height)
            self.isJumping = False

    def update(self):

        if self.isJumping:
            self.movement[1] = self.movement[1] + DinoGame.gravity

        if self.isJumping:
            self.index = 0
        elif self.isBlinking:
            if self.index == 0:
                if self.counter % 400 == 399:
                    self.index = (self.index + 1) % 2
            else:
                if self.counter % 20 == 19:
                    self.index = (self.index + 1) % 2
        elif self.isDucking:
            if self.counter % 5 == 0:
                self.index = (self.index + 1) % 2
        else:
            if self.counter % 5 == 0:
                self.index = (self.index + 1) % 2 + 2

        if self.isDead:
            self.index = 4

        if not self.isDucking:
            self.image = self.images[self.index]
            self.mask = self.masks[self.index]
            self.rect.width = self.stand_pos_width
        else:
            self.image = self.images1[(self.index) % 2]
            self.mask = self.masks1[(self.index) % 2]
            self.rect.width = self.duck_pos_width

        self.rect = self.rect.move(self.movement)
        self.checkbounds()

        if not self.isDead and self.counter % 7 == 6 and not self.isBlinking:
            self.score += 1
            if self.score % 100 == 0 and self.score != 0:
                if pygame.mixer.get_init() is not None:
                    DinoGame.checkPoint_sound.play()

        self.counter = self.counter + 1


class Cactus(pygame.sprite.Sprite):
    def __init__(self, speed=5, sizex=-1, sizey=-1):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.images, self.masks = folha("cacti-small.png", 3, 1, sizex, sizey)
        self.rect = self.images[0].get_rect()
        self.rect.bottom = int(0.98 * DinoGame.height)
        self.rect.left = DinoGame.width + self.rect.width
        i = random.randrange(0, 3)
        self.image = self.images[i]
        self.mask = self.masks[i]
        self.movement = [-1 * speed, 0]

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self):
        self.rect = self.rect.move(self.movement)

        if self.rect.right < 0:
            self.kill()


class Ptera(pygame.sprite.Sprite):
    def __init__(self, speed=5, sizex=-1, sizey=-1):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.images, self.masks = folha("ptera.png", 2, 1, sizex, sizey)
        self.rect = self.images[0].get_rect()
        self.ptera_height = [
            DinoGame.height * 0.82,
            DinoGame.height * 0.75,
            DinoGame.height * 0.60,
        ]
        self.rect.centery = self.ptera_height[random.randrange(0, 3)]
        self.rect.left = DinoGame.width + self.rect.width
        self.image = self.images[0]
        self.mask = self.masks[0]
        self.movement = [-1 * speed, 0]
        self.index = 0
        self.counter = 0

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self):
        if self.counter % 10 == 0:
            self.index = (self.index + 1) % 2
        self.image = self.images[self.index]
        self.mask = self.masks[self.index]
        self.rect = self.rect.move(self.movement)
        self.counter = self.counter + 1
        if self.rect.right < 0:
            self.kill()


class Ground:
    def __init__(self, speed=-5):
        self.image, self.rect = DinoGame.load_image("ground.png", -1, -1, -1)
        self.image1, self.rect1 = DinoGame.load_image("ground.png", -1, -1, -1)
        self.rect.bottom = DinoGame.height
        self.rect1.bottom = DinoGame.height
        self.rect1.left = self.rect.right
        self.speed = speed

    def draw(self, screen=None):
        if screen is not None:
            screen.blit(self.image, self.rect)
            screen.blit(self.image1, self.rect1)

    def update(self):
        self.rect.left += self.speed
        self.rect1.left += self.speed

        if self.rect.right < 0:
            self.rect.left = self.rect1.right

        if self.rect1.right < 0:
            self.rect1.left = self.rect.right


class Cloud(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image, self.rect = DinoGame.load_image(
            "cloud.png", int(90 * 30 / 42), 30, -1
        )
        self.speed = 1
        self.rect.left = x
        self.rect.top = y
        self.movement = [-1 * self.speed, 0]

    def draw(self, screen=None):
        if screen is not None:
            screen.blit(self.image, self.rect)

    def update(self):
        self.rect = self.rect.move(self.movement)
        if self.rect.right < 0:
            self.kill()


class Scoreboard:
    def __init__(self, x=-1, y=-1):
        self.score = 0
        self.tempimages, self.temprect = DinoGame.load_sprite_sheet(
            "numbers.png", 12, 1, 11, int(11 * 6 / 5), -1
        )
        self.image = pygame.Surface((55, int(11 * 6 / 5)))
        self.rect = self.image.get_rect()
        if x == -1:
            self.rect.left = DinoGame.width * 0.89
        else:
            self.rect.left = x
        if y == -1:
            self.rect.top = DinoGame.height * 0.1
        else:
            self.rect.top = y

    def draw(self, screen=None):
        if screen is not None:
            screen.blit(self.image, self.rect)

    def update(self, score):
        score_digits = DinoGame.extractDigits(score)
        self.image.fill(BG_COLOR)
        for s in score_digits:
            self.image.blit(self.tempimages[s], self.temprect)
            self.temprect.left += self.temprect.width
        self.temprect.left = 0
