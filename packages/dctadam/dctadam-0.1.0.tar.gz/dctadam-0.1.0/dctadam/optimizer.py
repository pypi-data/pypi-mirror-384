import torch
from torch.optim.optimizer import Optimizer
from .utils import block_process
 
class DCTAdam(Optimizer):
    """
    DCTAdam — модификация Adam, выполняющая обновления в DCT-домене.
    """

    def __init__(self, params, lr=1e-3, betas=(0.9, 0.999), eps=1e-8,
                 weight_decay=0.0, alpha=0.0, block_size=4096):
        defaults = dict(lr=lr, betas=betas, eps=eps,
                        weight_decay=weight_decay, alpha=alpha,
                        block_size=block_size)
        super().__init__(params, defaults)

    @torch.no_grad()
    def step(self, closure=None):
        loss = None
        if closure is not None:
            loss = closure()

        for group in self.param_groups:
            lr = group['lr']
            beta1, beta2 = group['betas']
            eps = group['eps']
            wd = group['weight_decay']
            alpha = group['alpha']
            block_size = group['block_size']

            for p in group['params']:
                if p.grad is None:
                    continue
                grad = p.grad.data
                if grad.is_sparse:
                    raise RuntimeError("DCTAdam does not support sparse gradients")

                state = self.state[p]
                if len(state) == 0:
                    state['step'] = 0
                    N = p.data.numel()
                    state['m_hat'] = torch.zeros(N, device=p.device, dtype=p.dtype)
                    state['v_hat'] = torch.zeros(N, device=p.device, dtype=p.dtype)
                    if alpha != 0.0:
                        k = torch.arange(N, device=p.device, dtype=p.dtype)
                        state['w'] = 1.0 / (1.0 + alpha * k)
                    else:
                        state['w'] = torch.ones(N, device=p.device, dtype=p.dtype)

                m_hat = state['m_hat']
                v_hat = state['v_hat']
                w = state['w']

                state['step'] += 1

                g_flat = grad.contiguous().view(-1)
                g_hat = block_process(g_flat, block_size, forward=True)

                m_hat.mul_(beta1).add_(g_hat, alpha=(1 - beta1))
                v_hat.mul_(beta2).addcmul_(g_hat, g_hat, value=(1 - beta2))

                bias_correction1 = 1 - beta1 ** state['step']
                bias_correction2 = 1 - beta2 ** state['step']

                m_hat_corr = m_hat / bias_correction1
                v_hat_corr = v_hat / bias_correction2

                u_hat = m_hat_corr / (v_hat_corr.sqrt().add(eps))
                u_hat = u_hat * w

                delta_flat = block_process(u_hat, block_size, forward=False)
                delta = delta_flat.view_as(grad)

                if wd != 0:
                    p.data.add_(p.data, alpha=-wd * lr)
                p.data.add_(delta, alpha=-lr)

        return loss
