import numpy as np

def ensure_list(x, allow_none=False):
    # Ensure inputs are lists, np.arrays are converted to lists
    if isinstance(x, list):
        return x
    if x is None:
        if allow_none:
            return None
        else:
            raise TypeError("Input must be a list or numpy array, not None")
    if isinstance(x, (str, bytes, bytearray)):
        return [x]
    if isinstance(x, np.ndarray):
        if x.ndim == 0:
            return [x.tolist()]
        else:
            return x.tolist()
    else:
        raise TypeError("Input must be a list or numpy array")
