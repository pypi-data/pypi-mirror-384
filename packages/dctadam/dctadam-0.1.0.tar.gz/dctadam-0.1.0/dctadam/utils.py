import torch
from scipy.fftpack import dct, idct

def block_process(x, block_size, forward=True):
    """
    Разбивает вектор x на блоки и применяет DCT/IDCT к каждому блоку.
    forward=True -> DCT, forward=False -> IDCT
    """
    N = x.shape[0]
    pad = (block_size - (N % block_size)) % block_size
    if pad > 0:
        x = torch.cat([x, torch.zeros(pad, dtype=x.dtype, device=x.device)], dim=0)

    x_np = x.cpu().numpy().reshape(-1, block_size)
    if forward:
        y_np = dct(x_np, type=2, norm='ortho', axis=-1)
    else:
        y_np = idct(x_np, type=2, norm='ortho', axis=-1)

    y = torch.from_numpy(y_np.reshape(-1)).to(x)
    if pad > 0:
        y = y[:-pad]
    return y
