import torch as th
from torch.nn import Module


class Conv2d(Module):
    """
    This class is the beginning of an exact python port of the torch.nn.Conv2d
    module. Because PySyft cannot hook into layers which are implemented in C++,
    our special functionalities (such as encrypted computation) do not work with
    torch.nn.Conv2d and so we must have python ports available for all layer types
    which we seek to use.

    Note that this module has been tested to ensure that it outputs the exact output
    values that the main module outputs in the same order that the main module does.

    However, there is often some rounding error of unknown origin, usually less than
    1e-6 in magnitude.

    This module has not yet been tested with GPUs but should work out of the box.
    """

    def __init__(
        self,
        in_channels,
        out_channels,
        kernel_size,
        stride=1,
        padding=0,
        dilation=1,
        groups=1,
        bias=False,
        padding_mode="zeros",
    ):
        """For information on the constructor arguments, please see PyTorch's
        documentation in torch.nn.Conv2d"""

        super().__init__()

        # because my particular experiment does not demand full functionality of
        # a convolutional layer, I will only implement the basic functionality.
        # These assertions are the required settings.

        assert in_channels == 1
        assert stride == 1
        assert padding == 0
        assert dilation == 1
        assert groups == 1
        assert padding_mode == "zeros"

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        self.dilation = dilation
        self.groups = groups
        self.has_bias = bias
        self.padding_mode = padding_mode

        temp_init = th.nn.Conv2d(
            in_channels=self.in_channels,
            out_channels=self.out_channels,
            kernel_size=self.kernel_size,
            stride=self.stride,
            padding=self.padding,
            dilation=self.dilation,
            groups=self.groups,
            bias=self.has_bias,
            padding_mode=self.padding_mode,
        )

        self.weight = temp_init.weight
        self.bias = temp_init.bias

    def forward(self, data):

        batch_size, _, rows, cols = data.shape

        expanded_data = data.unsqueeze(1).expand(batch_size, self.out_channels, 1, rows, cols)

        expanded_model = self.weight.unsqueeze(0).expand(
            batch_size, self.out_channels, 1, self.kernel_size, self.kernel_size
        )

        kernel_results = list()

        for i in range(0, rows - self.kernel_size + 1):
            for j in range(0, cols - self.kernel_size + 1):
                kernel_out = (
                    (
                        expanded_data[:, :, :, i : i + self.kernel_size, j : j + self.kernel_size]
                        * expanded_model
                    )
                    .sum(3)
                    .sum(3)
                )
                kernel_results.append(kernel_out)

        pred = th.cat(kernel_results, axis=2).view(
            batch_size, self.out_channels, rows - self.kernel_size + 1, cols - self.kernel_size + 1
        )

        if self.has_bias:
            pred = pred + self.bias.unsqueeze(0).unsqueeze(2).unsqueeze(3).expand(
                batch_size,
                self.out_channels,
                rows - self.kernel_size + 1,
                cols - self.kernel_size + 1,
            )

        return pred
