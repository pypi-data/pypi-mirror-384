import torch
from einops import rearrange
from retention._utils import dummify, InnerBlock_DT, OuterBlock_DT, InnerBlock_TD, OuterBlock_TD

def reference_expand(K, deg):
    """ Reference implementation of key expansion
    args:
        K: [b, n, h, c d]
        deg: int
    returns:
        phi_K: [b, n, h, c, D]
    """
    assert deg == 2
    b, n, h, c, d = K.shape
    K_outer = rearrange(K, 'b n h c (x o) -> b n h c x o', o=OuterBlock_DT)
    K_inner = rearrange(K, 'b n h c (y i) -> b n h c y i', i=InnerBlock_DT)
    phi_K_unmasked = torch.einsum('bnhcxo,bnhcyi->bnhcxyoi', K_outer, K_inner).to(K.dtype)
    _, _, _, _, x, y, o, i = phi_K_unmasked.shape
    phi_K_shape = (b, n, h, c, int((InnerBlock_DT // OuterBlock_DT + x) * y // 2), o, i)
    phi_K = torch.empty(phi_K_shape, device=K.device, dtype=K.dtype)
    idx = 0
    for y_idx in range(y):
        for x_idx in range(x):
            if (x_idx * OuterBlock_DT) < (y_idx + 1) * InnerBlock_DT:
                multiplier = 1 if (x_idx + 1) * OuterBlock_DT > y_idx * InnerBlock_DT else 2
                phi_K[:, :, :, :, idx, :, :] = multiplier * phi_K_unmasked[:, :, :, :, x_idx, y_idx, :, :]
                idx += 1
    phi_K = rearrange(phi_K, 'b n h c k o i -> b n h c (k o i)') # [b, n, h, c, D]
    return phi_K.to(K.dtype)

class SymmetricPowerUpdateStateReference(torch.autograd.Function):
    @staticmethod
    def forward(ctx, K, V, deg):
        """Reference implementation of the chunk state forward pass
        args:

            K, V: [b, n, c, h, d]
        returns:
            S: [b, n, h, D, d]
            N: [b, n, h, D]
        """
        b, n, c, h, d = K.shape
        K, V = K.transpose(2, 3), V.transpose(2, 3)  # [b, n, h, c, d]

        phi_K = reference_expand(K, deg)
        phi_K_T = phi_K.transpose(-1, -2) # [b, n, h, D, c]
        N = torch.sum(phi_K_T.to(torch.float32), dim=-1)  # [b, n, h, D]
        S = torch.matmul(phi_K_T, V)  # [b, n, h, D, d]
        ctx.save_for_backward(K, V)
        ctx.d = d
        ctx.deg = deg
        return S, N

    @staticmethod
    def backward(ctx, dS, dN):
        K, V = ctx.saved_tensors

        phi_K = reference_expand(K, ctx.deg) # [b, n, h, c, D]
        
        dphi_K = V @ dS.transpose(-1, -2) + dN[..., None, :]  # [b, n, h, c, D]
        dV = (phi_K @ dS).transpose(2, 3)  # [b, n, c, h d]

        dK = torch.zeros(K.shape).to(K.device).to(K.dtype)
        dphi_K = rearrange(dphi_K, 'b n h c (z i o) -> b n h c z i o', i = InnerBlock_TD, o = OuterBlock_TD).to(K.dtype)
        K_inner = rearrange(K, 'b n h c (y i) -> b n h c y i', i=InnerBlock_TD)
        K_outer = rearrange(K, 'b n h c (x o) -> b n h c x o', o=OuterBlock_TD)
        y, x = ctx.d // InnerBlock_TD, ctx.d // OuterBlock_TD

        for j in range(ctx.d // OuterBlock_TD):
            for i in range((j * OuterBlock_TD) // InnerBlock_TD, y):
                z = (i * (i + 1) // 2 * InnerBlock_TD // OuterBlock_TD) + j
                multiplier = 1 if (j + 1) * OuterBlock_TD > i * InnerBlock_TD else 2
                dPK_block = dphi_K[..., z, :, :] * multiplier # [b, n, h, c, InnerBlock_TD, OuterBlock_TD]
                dPK_block = rearrange(dPK_block, 'b n h c i o -> b n h c (i o)')
                K_i = K_inner[..., i, :] # [b, n, h, c, InnerBlock_TD]
                K_o = K_outer[..., j, :] # [b, n, h, c, OuterBlock_TD]
                dK_i = (dPK_block * K_o)
                dK_o = (dPK_block * K_i).sum(dim=-1, keepdim=True)
                dK[..., i * InnerBlock_TD:(i + 1) * InnerBlock_TD] += dK_i
                dK[..., j * OuterBlock_TD:(j + 1) * OuterBlock_TD] += dK_o

        dK = dK.transpose(2, 3)
        return dK, dV, None


def update_state(K, V, deg):
    if len(K.shape) == 4: # inference call
        K = K.unsqueeze(1) # [b, 1, c, h, d]
        V = V.unsqueeze(1) # [b, 1, c, h, d]
        S, N = update_state(K, V, deg)
        return S.squeeze(1), N.squeeze(1)
    
    S, N = SymmetricPowerUpdateStateReference.apply(K, V, deg) # type: ignore
    return S, N

update_state_fwd = dummify(SymmetricPowerUpdateStateReference.forward)