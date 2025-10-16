import numpy as np
import torch
from typing import Tuple, Union
from torch import nn
import torch.nn.functional as F
from torch import Tensor
import math

class DepthwiseConv2d(nn.Module):
    """
    When groups == in_channels and out_channels == K * in_channels, where K is a positive integer,
    this operation is termed in literature as depthwise convolution.
    ref : https://pytorch.org/docs/stable/generated/torch.nn.Conv2d.html

    Args:
        in_channels (int): Number of channels in the input
        out_channels (int): Number of channels produced by the convolution
        kernel_size (int or tuple): Size of the convolving kernel
        stride (int, optional): Stride of the convolution. Default: 2
        padding (int or tuple, optional): Zero-padding added to both sides of the input. Default: 0
    Inputs: inputs
        - **inputs** (batch, in_channels, time): Tensor containing input vector
    Returns: outputs
        - **outputs** (batch, out_channels, time): Tensor produces by depthwise 2-D convolution.
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: Union[int, Tuple],
        stride: int = 2,
    ) -> None:
        super(DepthwiseConv2d, self).__init__()
        assert out_channels % in_channels == 0, "out_channels should be constant multiple of in_channels"
        self.conv = nn.Conv2d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=kernel_size,
            stride=stride,
            padding=(kernel_size - 1 )// 2,
            groups=in_channels,
        )

    def forward(self, inputs: Tensor) -> Tensor:
        return self.conv(inputs)
    

class DepthwiseSeparableConv(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, padding=1, dilation=1, bias=False, norm=True):
        super(DepthwiseSeparableConv, self).__init__()
        self.depthwise = nn.Conv1d(in_channels, in_channels, kernel_size=kernel_size, stride=stride, padding=padding, dilation=dilation, groups=in_channels, bias=bias)
        self.activation1 = nn.GELU()
        self.pointwise = nn.Conv1d(in_channels, out_channels, kernel_size=1, stride=1, padding=0, bias=bias)
        self.activation2 = nn.GELU()
        self.use_norm = norm
        if self.use_norm:
            self.norm1 = nn.BatchNorm1d(in_channels)
            self.norm2 = nn.BatchNorm1d(out_channels)
        
    def forward(self, x):
        x = self.depthwise(x)
        if self.use_norm:
            x = self.norm1(x)
        x = self.activation1(x)
        x = self.pointwise(x)
        if self.use_norm:
            x = self.norm2(x)
        x = self.activation2(x)
        
        return x
    
    
class ConformerConv(nn.Module):
    def __init__(self, embed_size, kernel_size=31, dropout=0.1, activation=nn.GELU):
        super(ConformerConv, self).__init__()
        self.pointwise_conv1 = nn.Conv1d(embed_size, 2 * embed_size, kernel_size=1)
        self.depthwise_conv = nn.Conv1d(
            embed_size, embed_size, kernel_size=kernel_size, padding=(kernel_size - 1) // 2, groups=embed_size
        )
        self.norm = nn.BatchNorm1d(embed_size)
        #self.norm = nn.GroupNorm(embed_size, embed_size)
        self.activation = activation()
        self.pointwise_conv2 = nn.Conv1d(embed_size, embed_size, kernel_size=1)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        x = x.transpose(1, 2)
        x = self.pointwise_conv1(x)
        x = F.glu(x, dim=1)
        x = self.norm(self.depthwise_conv(x))
        x = self.activation(x)
        x = self.pointwise_conv2(x)
        return x.transpose(1, 2)
  

 
class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, stride=1, groups=1, padding=None, activation=nn.GELU, norm=True):
        super(ConvBlock, self).__init__()
        if padding is None:
            padding = (kernel_size - 1) // 2  
        
        self.conv = nn.Conv1d(in_channels, out_channels, groups=groups, kernel_size=kernel_size, stride=stride, padding=padding, bias=False)
        #self.layer_norm = nn.LayerNorm(out_channels, elementwise_affine=True)
        self.layer_norm = nn.BatchNorm1d(out_channels)
        #self.layer_norm = nn.GroupNorm(out_channels, out_channels, eps=1e-05, affine=True)
        self.activation = activation()
        self.norm = norm
        
        self.apply(self._init_weights)

    def forward(self, x):
        x = self.conv(x)
        if self.norm:
            x = self.layer_norm(x)
            #x = x.transpose(-2, -1)
            #x = self.layer_norm(x)
            #x = x.transpose(-2, -1)
        x = self.activation(x)
        return x
    
    def _init_weights(self, module):
        if isinstance(module, (nn.LayerNorm, nn.GroupNorm)):
            module.bias.data.zero_()
            module.weight.data.fill_(1.0)