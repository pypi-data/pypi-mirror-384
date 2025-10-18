import numpy as np

float_eps = float(10 * np.finfo(np.float32).eps)
NumberType = float | int | np.number
