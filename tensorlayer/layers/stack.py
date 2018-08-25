#! /usr/bin/python
# -*- coding: utf-8 -*-

import tensorflow as tf

from tensorlayer.layers.core import Layer

from tensorlayer.decorators import auto_parse_inputs
from tensorlayer.decorators import deprecated_alias
from tensorlayer.decorators import deprecated_args

__all__ = [
    'StackLayer',
    'UnStackLayer',
]


class StackLayer(Layer):
    """
    The :class:`StackLayer` class is a layer for stacking a list of rank-R tensors into one rank-(R+1) tensor, see `tf.stack() <https://www.tensorflow.org/api_docs/python/tf/stack>`__.

    Parameters
    ----------
    layers : list of :class:`Layer`
        Previous layers to stack.
    axis : int
        Dimension along which to concatenate.
    name : str
        A unique layer name.

    Examples
    ---------
    >>> import tensorflow as tf
    >>> import tensorlayer as tl
    >>> x = tf.placeholder(tf.float32, shape=[None, 30])
    >>> net = tl.layers.InputLayer(x, name='input')
    >>> net1 = tl.layers.DenseLayer(net, 10, name='dense1')
    >>> net2 = tl.layers.DenseLayer(net, 10, name='dense2')
    >>> net3 = tl.layers.DenseLayer(net, 10, name='dense3')
    >>> net = tl.layers.StackLayer([net1, net2, net3], axis=1, name='stack')
    (?, 3, 10)

    """

    @deprecated_args(
        end_support_version="2.1.0",
        instructions="`layers` is deprecated, use the functional API instead",
        deprecated_args=("layers", ),
    )  # TODO: remove this line before releasing TL 2.1.0
    def __init__(
        self,
        layers=None,
        axis=1,
        name='stack',
    ):

        self.prev_layer = layers
        self.axis = axis
        self.name = name

        super(StackLayer, self).__init__()

    def __str__(self):
        additional_str = []

        try:
            additional_str.append("axis: %s" % self.axis)
        except AttributeError:
            pass

        return self._str(additional_str)

    @auto_parse_inputs
    def compile(self, prev_layer, is_train=True):

        self._temp_data['outputs'] = tf.stack(self._temp_data['inputs'], axis=self.axis, name=self.name)


class UnStackLayer(Layer):
    """
    The :class:`UnStackLayer` class is a layer for unstacking the given dimension of a rank-R tensor into rank-(R-1) tensors., see `tf.unstack() <https://www.tensorflow.org/api_docs/python/tf/unstack>`__.

    Parameters
    ----------
    prev_layer : :class:`Layer`
        Previous layer
    num : int or None
        The length of the dimension axis. Automatically inferred if None (the default).
    axis : int
        Dimension along which axis to concatenate.
    name : str
        A unique layer name.

    Returns
    -------
    list of :class:`Layer`
        The list of layer objects unstacked from the input.

    """

    @deprecated_alias(
        layer='prev_layer', end_support_version="2.0.0"
    )  # TODO: remove this line before releasing TL 2.0.0
    def __init__(self, prev_layer=None, num=None, axis=0, name='unstack'):

        self.prev_layer = prev_layer
        self.num = num
        self.axis = axis
        self.name = name

        super(UnStackLayer, self).__init__()

    def __str__(self):
        additional_str = []

        try:
            additional_str.append("num: %s" % self.num)
        except AttributeError:
            pass

        try:
            additional_str.append("axis: %s" % self.axis)
        except AttributeError:
            pass

        try:
            additional_str.append("n_outputs: %s" % self.n_outputs)
        except AttributeError:
            pass

        return self._str(additional_str)

    @auto_parse_inputs
    def compile(self, prev_layer, is_train=True):

        self._temp_data['outputs'] = tf.unstack(self._temp_data['inputs'], num=self.num, axis=self.axis, name=self.name)
        self.n_outputs = len(self._temp_data['outputs'])

        net_new = []

        for i, unstacked_dim in enumerate(self._temp_data['outputs']):
            layer = Layer()

            layer.name = self.name + "_%d" % i
            layer.outputs = unstacked_dim

            layer.all_drop = self.all_drop
            layer._add_params(self.all_params)
            layer._add_layers(self.all_layers)
            layer._add_layers(layer.outputs)

            net_new.append(layer)

        self._temp_data['outputs'] = net_new
