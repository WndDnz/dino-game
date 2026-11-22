#!/usr/bin/python3

import AGMLP
import numpy as np
from RedeNeural import RedeNeural
import matplotlib.pyplot as plt

x = np.linspace(-10, 10, 10000)
y = 1.0 / (1.0 + np.exp(-x))

plt.plot(x, y)
plt.show()
