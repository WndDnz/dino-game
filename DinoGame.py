#!/usr/bin/python3

import os
import pygame
import pygame.freetype
import random
import numpy as np
import RedeNeural
import AGMLP
import math

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BG_COLOR = (235, 235, 235)

pygame.mixer.pre_init(44100, -16, 2, 2048)  # fix audio delay
pygame.init()


class DinoGame():
    scr_size = (width, height) = (600, 150)
    accel = 1
    FPS = 60
    gravity = 0.6
    high_score = 0
    checkPoint_sound = pygame.mixer.Sound('sprites/checkPoint.wav')
    jump_sound = pygame.mixer.Sound('sprites/jump.wav')
    die_sound = pygame.mixer.Sound('sprites/die.wav')

    def __init__(self):
        self.screen = pygame.display.set_mode(self.scr_size)
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
        fullname = os.path.join('sprites', name)
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
        fullname = os.path.join('sprites', sheetname)
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
            while(number // 10 != 0):
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

        callout, callout_rect = self.load_image('call_out.png', 196, 45, -1)
        callout_rect.left = self.width * 0.05
        callout_rect.top = self.height * 0.4

        temp_ground, temp_ground_rect = self.load_sprite_sheet('ground.png', 15, 1, -1, -1, -1)
        temp_ground_rect.left = self.width / 20
        temp_ground_rect.bottom = self.height

        logo, logo_rect = self.load_image('logo.png', 240, 40, -1)
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
        gamespeed = 4
        startMenu = False
        gameOver = False
        gameQuit = False
        self.playerDino = Dino(44, 47)
        new_ground = Ground(-1 * gamespeed)
        scb = Scoreboard()
        highsc = Scoreboard(self.width * 0.78)
        counter = 0

        cacti = pygame.sprite.Group()
        pteras = pygame.sprite.Group()
        clouds = pygame.sprite.Group()
        last_obstacle = pygame.sprite.Group()

        Cactus.containers = cacti
        Ptera.containers = pteras
        Cloud.containers = clouds

        retbutton_image, retbutton_rect = self.load_image('replay_button.png', 35, 31, -1)
        gameover_image, gameover_rect = self.load_image('game_over.png', 190, 11, -1)

        temp_images, temp_rect = self.load_sprite_sheet('numbers.png', 12, 1, 11, int(11 * 6 / 5), -1)
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
                                if self.playerDino.rect.bottom == int(0.98 * self.height):
                                    self.playerDino.isJumping = True
                                    if pygame.mixer.get_init() is not None:
                                        DinoGame.jump_sound.play()
                                    self.playerDino.movement[1] = -1 * self.playerDino.jumpSpeed

                            if event.key == pygame.K_DOWN:
                                if not (self.playerDino.isJumping and self.playerDino.isDead):
                                    self.playerDino.isDucking = True

                            if event.key == pygame.K_q:
                                gameQuit = True
                                gameOver = True

                        if event.type == pygame.KEYUP:
                            if event.key == pygame.K_DOWN:
                                self.playerDino.isDucking = False
                for c in cacti:
                    c.movement[0] = -1 * gamespeed
                    if pygame.sprite.collide_mask(self.playerDino, c):
                        self.playerDino.isDead = True
                        if pygame.mixer.get_init() is not None:
                            DinoGame.die_sound.play()

                for p in pteras:
                    p.movement[0] = -1 * gamespeed
                    if pygame.sprite.collide_mask(self.playerDino, p):
                        self.playerDino.isDead = True
                        if pygame.mixer.get_init() is not None:
                            DinoGame.die_sound.play()

                if len(cacti) < 2:
                    if len(cacti) == 0:
                        last_obstacle.empty()
                        last_obstacle.add(Cactus(gamespeed, 40, 40))
                    else:
                        for last in last_obstacle:
                            if last.rect.right < self.width * 0.7 and random.randrange(0, 50) == 10:
                                last_obstacle.empty()
                                last_obstacle.add(Cactus(gamespeed, 40, 40))

                if len(pteras) == 0 and random.randrange(0, 200) == 10 and counter > 700:
                    for last in last_obstacle:
                        if last.rect.right < self.width * 0.8:
                            last_obstacle.empty()
                            last_obstacle.add(Ptera(gamespeed, 46, 40))

                if len(clouds) < 5 and random.randrange(0, 300) == 10:
                    Cloud(self.width, random.randrange(self.height / 5, self.height / 2))

                self.playerDino.update()
                cacti.update()
                pteras.update()
                clouds.update()
                new_ground.update()
                scb.update(self.playerDino.score)
                highsc.update(self.high_score)

                if pygame.display.get_surface() is not None:
                    self.screen.fill(BG_COLOR)
                    new_ground.draw(self.screen)
                    clouds.draw(self.screen)
                    scb.draw(self.screen)
                    if self.high_score != 0:
                        highsc.draw(self.screen)
                        self.screen.blit(HI_image, HI_rect)
                    cacti.draw(self.screen)
                    pteras.draw(self.screen)
                    self.playerDino.draw(self.screen)

                    pygame.display.update()
                self.clock.tick(self.FPS)

                if self.playerDino.isDead:
                    gameOver = True
                    if self.playerDino.score > DinoGame.high_score:
                        DinoGame.high_score = self.playerDino.score

                if counter % 700 == 699:
                    new_ground.speed -= 1
                    gamespeed += 1

                counter = (counter + 1)

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

                            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
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

    def train(self, nIndividuals=20, nGenerations=100, population=None):
        # DinoGame.FPS *= 3
        gamespeed = 4
        startMenu = False
        gameOver = False
        gameQuit = False
        l = a = nl = na = s = 0
        self.dinoArray.clear()
        for i in range(nIndividuals):
            self.dinoArray.append(Dino(44, 47))
        ag = AGMLP.RNA_AG((4, 8, 4, 2), None, 0.1, nIndividuals, nGenerations, elite=0.05)
        if population is None:
            brains = ag.iniciaPopulacao()
        else:
            brains = population
        for dino, brain in zip(self.dinoArray, brains):
            dino.brain = brain
        rankedBrains = []

        new_ground = Ground(-1 * gamespeed)
        counter = 0

        ft_font = pygame.freetype.SysFont('Input', 12)

        cacti = pygame.sprite.Group()
        pteras = pygame.sprite.Group()
        clouds = pygame.sprite.Group()
        last_obstacle = pygame.sprite.Group()

        Cactus.containers = cacti
        Ptera.containers = pteras
        Cloud.containers = clouds

        retbutton_image, retbutton_rect = self.load_image('replay_button.png', 35, 31, -1)
        gameover_image, gameover_rect = self.load_image('game_over.png', 190, 11, -1)

        temp_images, temp_rect = self.load_sprite_sheet('numbers.png', 12, 1, 11, int(11 * 6 / 5), -1)

        print(f"Starting generation {DinoGame.train.currentGeneration}.")

        while not gameQuit:
            while startMenu:
                pass
            while not gameOver and not gameQuit:
                if pygame.display.get_surface() is None:
                    print("Couldn't load display surface")
                    gameQuit = True
                    gameOver = True
                else:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            gameQuit = True
                            gameOver = False
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                gameQuit = True
                                gameOver = False
                            if event.key == pygame.K_q:
                                gameQuit = True
                                gameOver = True
                            if event.key == pygame.K_RIGHT:
                                DinoGame.accel += 1
                                DinoGame.FPS *= DinoGame.accel
                            if event.key == pygame.K_LEFT:
                                DinoGame.accel -= 1
                                DinoGame.FPS *= DinoGame.accel

                cac = None
                pte = None
                for c in cacti:
                    c.movement[0] = -1 * gamespeed
                    for d in self.dinoArray:
                        if pygame.sprite.collide_mask(d, c):
                            d.isDead = True
                            # print("I'm dead... My score: ", d.score)
                            rankedBrains.append((d.score, d.brain))
                            self.dinoArray.remove(d)
                            if pygame.mixer.get_init() is not None:
                                DinoGame.die_sound.play()

                    if cac is None:
                        cac = c
                    else:
                        if c.rect.left >= 65:
                            cac = c

                for p in pteras:
                    p.movement[0] = -1 * gamespeed
                    for d in self.dinoArray:
                        if pygame.sprite.collide_mask(d, p):
                            d.isDead = True
                            # print("I'm dead... My score: ", d.score)
                            rankedBrains.append((d.score, d.brain))
                            self.dinoArray.remove(d)
                            if pygame.mixer.get_init() is not None:
                                DinoGame.die_sound.play()
                    if pte is None:
                        pte = p
                    else:
                        if p.rect.left < pte.rect.left:
                            pte = p

                if cac is not None or pte is not None:
                    l = (cac.rect.left - dino.rect.right) if cac is not None else 0
                    # if cac is not None:
                    #     l = (cac.rect.left - dino.rect.right)
                    # else:
                    #     l = 632
                    
                    # if pte is not None:
                    nl = (pte.rect.left - dino.rect.right) if pte is not None else 0
                    na = pte.rect.bottom if pte is not None else 0
                    # else:
                    #     nl = 632
                    #     na =  110
                    s = gamespeed
                    for dino in self.dinoArray:
                        activation = dino.getAction(np.array([[l], [nl], [na], [s]]))
                        # print(f"Activation: {activation}")
                        if activation[1][0] > 0.99:
                            dino.isDucking = True
                        else:
                            dino.isDucking = False

                        if activation[0][0] > 0.99:
                            if not dino.isJumping:
                                dino.isJumping = True
                                if pygame.mixer.get_init() is not None:
                                    DinoGame.jump_sound.play()
                                    dino.movement[1] = -1 * dino.jumpSpeed

                if len(cacti) < 1:
                    if len(cacti) == 0:
                        nearest = None
                        last_obstacle.empty()
                        last_obstacle.add(Cactus(gamespeed, 40, 40))
                    else:
                        for last in last_obstacle:
                            if last.rect.right < self.width * 0.7 and random.randrange(0, 50) == 10:
                                last_obstacle.empty()
                                last_obstacle.add(Cactus(gamespeed, 40, 40))

                if len(pteras) == 0 and random.randrange(0, 200) == 10 and counter > 600:
                    for last in last_obstacle:
                        if last.rect.right < self.width * 0.8:
                            last_obstacle.empty()
                            p = Ptera(gamespeed, 56, 40)
                            if len(cacti) == 0:
                                for c in cacti:
                                    if not pygame.sprite.collide_mask(p, c):
                                        last_obstacle.add(p)
                            else:
                                last_obstacle.add(p)

                if len(clouds) < 5 and random.randrange(0, 300) == 10:
                    Cloud(self.width, random.randrange(self.height // 5, self.height // 2))

                for d in self.dinoArray:
                    d.update()

                cacti.update()
                pteras.update()
                clouds.update()
                new_ground.update()

                alive = f'Alive: {len(self.dinoArray)}/{nIndividuals}'
                alive_rect = ft_font.get_rect(alive)
                alive_rect.topright = self.screen.get_rect().topright
                alive_rect.move_ip(-2, 2)

                best = f'Best fitness (prev gen): {DinoGame.train.currentBest}'
                best_rect = ft_font.get_rect(best)
                best_rect.topright = alive_rect.bottomright
                best_rect.move_ip(0, 2)

                sens = f'Senses: l: {l} nl: {nl} na: {na} s: {s}'
                sens_rect = ft_font.get_rect(sens)
                sens_rect.topleft = self.screen.get_rect().topleft
                sens_rect.move_ip(2, 2)

                if pygame.display.get_surface() is not None:
                    self.screen.fill(BG_COLOR)
                    new_ground.draw(self.screen)
                    clouds.draw(self.screen)
                    cacti.draw(self.screen)
                    pteras.draw(self.screen)
                    for d in self.dinoArray:
                        d.draw(self.screen)
                    ft_font.render_to(self.screen, alive_rect.topleft, alive, (255, 0, 0))
                    if cac is not None or pte is not None:
                        ft_font.render_to(self.screen, sens_rect.topleft, sens, (0, 0, 255))
                    if DinoGame.train.currentBest is not None:
                        ft_font.render_to(self.screen, best_rect.topleft, best, (255, 0, 0))
                    pygame.display.update()
                # if len(self.dinoArray) > 0 and counter % 3 == 0:
                #     print(f"Activation: {self.dinoArray[0].getAction(np.array([[l], [nl], [na], [s]]))}")
                self.clock.tick(self.FPS)

                if not self.dinoArray:
                    DinoGame.train.currentGeneration += 1
                    rank = ag.ranquearIndividuos(rankedBrains)
                    if DinoGame.train.currentGeneration > nGenerations:
                        RedeNeural.RedeNeural.save_object(rankedBrains[rank[0][0]][1], 'bestDino.din')
                        gameOver = True
                    else:
                        DinoGame.train.currentBest = rank[0][1]
                        newPopulation = ag.proximaGeracao(rankedBrains)
                        self.train(nIndividuals=nIndividuals, nGenerations=nGenerations, population=newPopulation)

                if counter % 700 == 699:
                    new_ground.speed -= 1
                    gamespeed += 1

                counter = (counter + 1)

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

                            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                                gameOver = False
                                # TODO Check if want to run again, save population
                                DinoGame.train.currentGeneration = 1
                                self.train(nIndividuals=nIndividuals, nGenerations=nGenerations)

                if pygame.display.get_surface() is not None:
                    self.disp_gameOver_msg(retbutton_image, gameover_image)
                    pygame.display.update()
                self.clock.tick(self.FPS)

        pygame.quit()
        quit()

    def start(self, nIndividuals=None, nGenerations=None, train=False, auto=False):
        isGameQuit = self.introscreen()
        if not isGameQuit:
            if train and nIndividuals is not None:
                print('Starting training.')
                DinoGame.train.currentGeneration = 1
                DinoGame.train.currentBest = None
                self.train(nIndividuals=nIndividuals, nGenerations=nGenerations)
            elif auto:
                self.gameplay()
            else:
                self.gameplay()


class Dino():
    def __init__(self, sizex=-1, sizey=-1):
        self.images, self.rect = DinoGame.load_sprite_sheet('dino.png', 5, 1, sizex, sizey, -1)
        self.images1, self.rect1 = DinoGame.load_sprite_sheet('dino_ducking.png', 2, 1, 59, sizey, -1)
        self.rect.bottom = int(0.98 * DinoGame.height)
        self.rect.left = DinoGame.width / 15
        self.image = self.images[0]
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
            if senses.shape == (4, 1):
                return self.brain.feedForward(senses)
        else:
            return None

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
            self.rect.width = self.stand_pos_width
        else:
            self.image = self.images1[(self.index) % 2]
            self.rect.width = self.duck_pos_width

        self.rect = self.rect.move(self.movement)
        self.checkbounds()

        if not self.isDead and self.counter % 7 == 6 and not self.isBlinking:
            self.score += 1
            if self.score % 100 == 0 and self.score != 0:
                if pygame.mixer.get_init() is not None:
                    DinoGame.checkPoint_sound.play()

        self.counter = (self.counter + 1)


class Cactus(pygame.sprite.Sprite):
    def __init__(self, speed=5, sizex=-1, sizey=-1):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.images, self.rect = DinoGame.load_sprite_sheet('cacti-small.png', 3, 1, sizex, sizey, -1)
        self.rect.bottom = int(0.98 * DinoGame.height)
        self.rect.left = DinoGame.width + self.rect.width
        self.image = self.images[random.randrange(0, 3)]
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
        self.images, self.rect = DinoGame.load_sprite_sheet('ptera.png', 2, 1, sizex, sizey, -1)
        self.ptera_height = [DinoGame.height * 0.82, DinoGame.height * 0.75, DinoGame.height * 0.60]
        self.rect.centery = self.ptera_height[random.randrange(0, 3)]
        self.rect.left = DinoGame.width + self.rect.width
        self.image = self.images[0]
        self.movement = [-1 * speed, 0]
        self.index = 0
        self.counter = 0

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self):
        if self.counter % 10 == 0:
            self.index = (self.index + 1) % 2
        self.image = self.images[self.index]
        self.rect = self.rect.move(self.movement)
        self.counter = (self.counter + 1)
        if self.rect.right < 0:
            self.kill()


class Ground():
    def __init__(self, speed=-5):
        self.image, self.rect = DinoGame.load_image('ground.png', -1, -1, -1)
        self.image1, self.rect1 = DinoGame.load_image('ground.png', -1, -1, -1)
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
        self.image, self.rect = DinoGame.load_image('cloud.png', int(90 * 30 / 42), 30, -1)
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


class Scoreboard():
    def __init__(self, x=-1, y=-1):
        self.score = 0
        self.tempimages, self.temprect = DinoGame.load_sprite_sheet('numbers.png', 12, 1, 11, int(11 * 6 / 5), -1)
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
