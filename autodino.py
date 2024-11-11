#!/usr/bin/python3

import DinoGame

game = DinoGame.DinoGame()
game.start(nIndividuals=500, nGenerations=30, train=True)
