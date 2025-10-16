"""RWKV v7 model with enhanced state space and LoRA decompositions."""
from typing import Optional, Tuple, Callable

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.init import orthogonal_, zeros_, ones_, uniform_

from .base import RWKVBaseModel
from .ops.wkv_ops import wkv7_forward as wkv_forward
from .utils import time_shift, lerp


class TimeMix(nn.Module):
    """Time-mixing with state space model and LoRA decompositions."""
    
    def __init__(self, n_embd: int, dim_att: int, head_size: int, layer_id: int, n_layer: int,
                 decay_lora: int = 64, aaa_lora: int = 64, mv_lora: int = 32, gate_lora: int = 128):
        super().__init__()
        
        # Configuration and validation
        self.layer_id, self.n_embd, self.dim_att, self.head_size, self.n_layer = layer_id, n_embd, dim_att, head_size, n_layer
        self.n_head = dim_att // head_size
        
        if dim_att % head_size != 0:
            raise ValueError(f"dim_att ({dim_att}) must be divisible by head_size ({head_size})")
        
        # Convenience aliases
        H, N, C = self.n_head, self.head_size, n_embd

        # Time-shift operation
        self.time_shift = nn.ZeroPad2d((0, 0, 1, -1))

        # Time-mixing parameters
        self.tmix_r, self.tmix_w, self.tmix_k, self.tmix_v, self.tmix_a, self.tmix_g = (
            nn.Parameter(torch.empty(1, 1, C)) for _ in range(6)
        )

        # LoRA parameters
        self.w1, self.w2, self.w0 = self._create_lora_params(n_embd, decay_lora) # decay lora
        self.a1, self.a2, self.a0 = self._create_lora_params(n_embd, aaa_lora) # aaa lora
        self.v1, self.v2, self.v0 = self._create_lora_params(n_embd, mv_lora) # mv lora
        self.g1, self.g2, _ = self._create_lora_params(n_embd, gate_lora) # gate lora

        # 
        self.k_k = nn.Parameter(torch.empty(1,1,C)) # removal key
        self.k_a = nn.Parameter(torch.empty(1,1,C)) # replacement key
        self.r_k = nn.Parameter(torch.empty(H,N)) # key bonus

        # Linear layers
        self.receptance = nn.Linear(C, C, bias=False)
        self.key = nn.Linear(C, C, bias=False)
        self.value = nn.Linear(C, C, bias=False)
        
        # Output projection and normalization
        self.output = nn.Linear(C, C, bias=False)
        self.ln_x = nn.GroupNorm(H, C, eps=64e-5) # !!! notice eps value !!!
        
        # Initialize parameters
        self._init_parameters()
            
    def _create_lora_params(self, input_dim: int, lora_dim: int) -> Tuple[nn.Parameter, nn.Parameter, nn.Parameter]:
        """Create LoRA parameters: down projection, up projection, bias."""
        down = nn.Parameter(torch.empty(input_dim, lora_dim))
        up = nn.Parameter(torch.empty(lora_dim, input_dim))
        bias = nn.Parameter(torch.empty(1, 1, input_dim))
        return down, up, bias
    
    def _init_parameters(self):
        """Initialize parameters with stable values."""

        self._init_tmix()
        self._init_loras()

        # Key parameters
        ones_(self.k_k)
        zeros_(self.k_a)
        orthogonal_(self.r_k)

        # Value residual parameters
        if self.layer_id > 0:
            zeros_(self.v0)
            orthogonal_(self.v1)
            orthogonal_(self.v2)

    def _compute_layer_ratios_and_ddd(self):
        """Compute layer ratios and dimension decay tensor."""
        ratio_0_to_1 = self.layer_id / (self.n_layer - 1)  # 0 to 1
        ratio_1_to_almost0 = 1.0 - (self.layer_id / self.n_layer)  # 1 to ~0
        ddd = torch.ones(1, 1, self.n_embd)
        for i in range(self.n_embd):
            ddd[0, 0, i] = i / self.n_embd
        return ratio_0_to_1, ratio_1_to_almost0, ddd
    
    def _init_tmix(self):
        _, ratio_1_to_almost0, ddd = self._compute_layer_ratios_and_ddd()
        params = [self.tmix_r, self.tmix_w, self.tmix_k, self.tmix_v, self.tmix_a, self.tmix_g]
        powers = [0.2, 0.9, 0.7, 0.7, 0.9, 0.2]
        for param, power in zip(params, powers):
            param.data = 1.0 - torch.pow(ddd, power * ratio_1_to_almost0)

    def _init_lora(self, A: nn.Parameter, B: nn.Parameter, bias: Optional[nn.Parameter] = None):
        """Initialize LoRA matrices"""
        orthogonal_(A)
        orthogonal_(B)
        if bias is not None:
            zeros_(bias)

    def _init_loras(self):
        self._init_lora(self.w1, self.w2, self.w0)  # Decay LoRA
        self._init_lora(self.a1, self.a2, self.a0)  # AAA LoRA
        self._init_lora(self.v1, self.v2, self.v0)  # MV LoRA
        self._init_lora(self.g1, self.g2, None)     # Gate LoRA
    
    def _loramlp(self, f: Callable[[torch.Tensor], torch.Tensor], x: torch.Tensor, A: torch.Tensor, B: torch.Tensor, bias: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Eq.2 LoRA-MLP operation: f(x @ A) @ B + bias."""
        result = f(x @ A) @ B
        if bias is not None:
            result = result + bias
        return result

    def forward(self, xt: torch.Tensor, v_first: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass through time-mixing layer."""

        # prepare shapes
        B, T, C = xt.shape
        # C = self.dim_att
        H = self.n_head

        # Shifted input for time-mixing
        xt_prev = time_shift(xt)
        
        # Eq.3 token shift inputs
        xt_r = lerp(xt, xt_prev, self.tmix_r)
        xt_w = lerp(xt, xt_prev, self.tmix_w)
        xt_k = lerp(xt, xt_prev, self.tmix_k)
        xt_v = lerp(xt, xt_prev, self.tmix_v)
        xt_a = lerp(xt, xt_prev, self.tmix_a)
        xt_g = lerp(xt, xt_prev, self.tmix_g)

        # Eq.4 in-context learning rate
        at = torch.sigmoid(
                self._loramlp(f=lambda x: x, x=xt_a, A=self.a1, B=self.a2, bias=self.a0)
            )

        # Eq.5 key precursor
        kt = self.key(xt_k)

        # Eq.6 removal key
        kk = kt * self.k_k

        # Eq.7 replacement key
        k = kt * lerp(a=torch.ones_like(at), b=at, x=self.k_a)

        # Eq.8 value residual gate
        vt = torch.sigmoid(
                self._loramlp(f=lambda x: x, x=xt_v, A=self.v1, B=self.v2, bias=self.v0)
            )

        # Eq.9 value precursor
        v = self.value(xt_v)

        # Eq.10 value
        if self.layer_id == 0:
            v_first = v # store the v of the first layer
        else:
            v = v + (v_first - v) * torch.sigmoid(self.v0 + (xt_v @ self.v1) @ self.v2) # add value residual

        # Eq.11 decay precursor
        dt = self._loramlp(f=torch.tanh, x=xt_w, A=self.w1, B=self.w2, bias=self.w0)

        # Eq.12 decay
        wt = -F.softplus(-dt) - 0.5 # soft-clamp to [-inf, 5]
        
        # Eq.13 receptance
        rt = self.receptance(xt_r)

        # Eq.14 rwkv gate
        gt = self._loramlp(f=torch.sigmoid, x=xt_g, A=self.g1, B=self.g2, bias=None)

        # Eq.15 normalized removal key
        kk = F.normalize(kk.view(B,T,H,-1), dim=-1, p=2.0).view(B,T,C)

        # Eq.16-17 WKV computation
        wkvt = wkv_forward(rt, wt, kt, vt, -kk, kk*at, self.head_size)

        # Eq.20 bonus
        ut =  (rt.view(B,T,H,-1)*k.view(B,T,H,-1)*self.r_k).sum(dim=-1, keepdim=True) * v.view(B,T,H,-1).view(B,T,C)

        # Eq.21 attention result
        pt = self.ln_x(rt * wkvt) + ut

        # Eq.22
        ot = self.output(gt * pt)

        return ot, v_first


class ChannelMix(nn.Module):
    """Channel-mixing FFN with squared ReLU and time-mixing."""
    
    def __init__(self, n_embd: int, dim_ffn: int):
        super().__init__()
        
        self.x_k = nn.Parameter(torch.empty(1, 1, n_embd))
        self.key = nn.Linear(n_embd, dim_ffn, bias=False)
        self.value = nn.Linear(dim_ffn, n_embd, bias=False)

        self._init_parameters()

    def _init_parameters(self):
        """Initialize parameters with stable values."""
        uniform_(self.x_k, -0.01, 0.01)
    
    def forward(self, xt: torch.Tensor) -> torch.Tensor:
        xt_prev = time_shift(xt)
        kt = self.key(lerp(xt, xt_prev, self.x_k))
        ot = self.value(torch.relu(kt) ** 2)
        return ot


class Block(nn.Module):
    """RWKV v7 block with time-mixing and channel-mixing."""

    def __init__(self, n_embd: int, dim_att: int, dim_ffn: int, head_size: int, layer_id: int, n_layer: int,
                 decay_lora: int = 64, aaa_lora: int = 64, mv_lora: int = 32, gate_lora: int = 128):
        super().__init__()
        self.layer_id = layer_id
        self.n_embd = n_embd

        if layer_id == 0:
            self.ln0 = nn.LayerNorm(n_embd)
        self.ln1 = nn.LayerNorm(n_embd)
        self.ln2 = nn.LayerNorm(n_embd)
        
        self.tmix = TimeMix(n_embd, dim_att, head_size, layer_id, n_layer, decay_lora, aaa_lora, mv_lora, gate_lora)
        self.cmix = ChannelMix(n_embd, dim_ffn)

    def forward(self, xt: torch.Tensor, vt_first: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        if self.layer_id == 0:
            xt = self.ln0(xt)

        tmix_out, vt_first = self.tmix(self.ln1(xt), vt_first)
        xt = xt + tmix_out

        cmix_out = self.cmix(self.ln2(xt))
        xt = xt + cmix_out

        return xt, vt_first


class RWKV(RWKVBaseModel):
    """RWKV v7 language model with enhanced state space and LoRA."""
    
    def __init__(self, n_layer: int, n_embd: int, vocab_size: int, head_size: int,
                 dim_att: Optional[int] = None, dim_ffn: Optional[int] = None,
                 decay_lora: int = 64, aaa_lora: int = 64, mv_lora: int = 32, gate_lora: int = 128,
                 **kwargs):
        # Set defaults for v7-specific parameters
        if dim_att is None:
            dim_att = n_embd
        if dim_ffn is None:
            dim_ffn = n_embd * 4
            
        # Create config dict for base class
        config_dict = {
            "n_layer": n_layer,
            "n_embd": n_embd,
            "vocab_size": vocab_size,
            "head_size": head_size,
            "dim_att": dim_att,
            "dim_ffn": dim_ffn,
            "decay_lora": decay_lora,
            "aaa_lora": aaa_lora,
            "mv_lora": mv_lora,
            "gate_lora": gate_lora,
            **kwargs
        }
        super().__init__(config_dict)

        self.emb = nn.Embedding(vocab_size, n_embd)
        self.blocks = nn.ModuleList([
            Block(n_embd, dim_att, dim_ffn, head_size, i, n_layer, decay_lora, aaa_lora, mv_lora, gate_lora) 
            for i in range(n_layer)
        ])
        self.ln_out = nn.LayerNorm(n_embd)
        self.head = nn.Linear(n_embd, vocab_size, bias=False)

    def forward(
        self,
        x: torch.Tensor,
        state: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Forward pass through RWKV v7.
        
        Args:
            x: Input token indices [batch, seq_len]
            state: Optional recurrent state (not used in v7)
            
        Returns:
            logits: Output logits [batch, seq_len, vocab_size]
            state: Updated state (passthrough)
        """
        x = self.emb(x)
        B, T, C = x.shape
        
        # v_first will be populated by first block
        v_first = torch.empty(B, T, C, device=x.device, dtype=x.dtype)
        
        for block in self.blocks:
            x, v_first = block(x, v_first)

        logits = self.head(self.ln_out(x))
        return logits, state
