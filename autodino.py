#!/usr/bin/python3

import DinoGame
import traceback

try:
    game = DinoGame.DinoGame()
    game.start(nIndividuals=350, nGenerations=30, train=True)
except Exception as e:
    traceback.print_exception(e)
    wait_for_it = input("Press enter to close the terminal window")
