from collections.abc import Callable

import numpy as np
from numpy.typing import ArrayLike

Array = np.typing.NDArray[np.float64]
Weights = list[Array]
ActivationFunction = Callable[[ArrayLike], Array]
