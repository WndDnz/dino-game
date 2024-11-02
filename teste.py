#!/usr/bin/python3

import AGMLP
import numpy as np
from RedeNeural import RedeNeural

correction = np.zeros((9, 1))
correction[:2] = [[1], [1]]
print(correction)