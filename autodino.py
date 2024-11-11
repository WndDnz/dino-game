#!/usr/bin/python3

import DinoGame

game = DinoGame.DinoGame()
game.start(nIndividuals=1000, nGenerations=30, train=True)
