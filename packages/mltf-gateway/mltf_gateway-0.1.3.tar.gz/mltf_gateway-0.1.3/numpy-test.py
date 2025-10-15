#!/usr/bin/env python3

import numpy as np

x = np.ones(1, dtype=np.float64)
y = np.full(1, complex(0 + 2j), dtype=np.complex128)
z = x > y
print(z)
