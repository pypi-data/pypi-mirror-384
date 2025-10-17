__all__ = ['FourierNetwork']

import numcodecs.abc

class FourierNetwork(numcodecs.abc.Codec):
    r"""
    Fourier network codec which trains and overfits a fourier feature neural
    network on encoding and predicts during decoding.
    
    The approach is based on the papers by Tancik et al. 2020
    (<https://dl.acm.org/doi/abs/10.5555/3495724.3496356>)
    and by Huang and Hoefler 2020 (<https://arxiv.org/abs/2210.12538>).
    
    Parameters
    ----------
    fourier_features : ...
        The number of Fourier features that the data coordinates are projected to
    fourier_scale : ...
        The standard deviation of the Fourier features
    learning_rate : ...
        The learning rate for the `Adam` optimizer
    mini_batch_size : ...
        The optional mini-batch size used during training
        
        Setting the mini-batch size to `None` disables the use of batching,
        i.e. the network is trained using one large batch that includes the
        full data.
    num_blocks : ...
        The number of blocks in the network
    num_epochs : ...
        The number of epochs for which the network is trained
    seed : ...
        The seed for the random number generator used during encoding
    _version : ..., optional, default = "0.1.0"
        The codec's encoding format version. Do not provide this parameter explicitly.
    """

    def __init__(self, fourier_features, fourier_scale, learning_rate, mini_batch_size, num_blocks, num_epochs, seed, _version='0.1.0'): ...

    codec_id = 'fourier-network.rs'

    def decode(self, buf, out=None):
        r"""
        Decode the data in `buf`.
        
        Parameters
        ----------
        buf : Buffer
            Encoded data. May be any object supporting the new-style buffer
            protocol.
        out : Buffer, optional
            Writeable buffer to store decoded data. N.B. if provided, this buffer must
            be exactly the right size to store the decoded data.
        
        Returns
        -------
        dec : Buffer
            Decoded data. May be any object supporting the new-style
            buffer protocol.
        """
        ...

    def encode(self, buf):
        r"""
        Encode the data in `buf`.
        
        Parameters
        ----------
        buf : Buffer
            Data to be encoded. May be any object supporting the new-style
            buffer protocol.
        
        Returns
        -------
        enc : Buffer
            Encoded data. May be any object supporting the new-style buffer
            protocol.
        """
        ...

    @classmethod
    def from_config(cls, config):
        r"""
        Instantiate the codec from a configuration [`dict`][dict].
        
        Parameters
        ----------
        config : dict
            Configuration of the codec.
        
        Returns
        -------
        codec : Self
            Instantiated codec.
        """
        ...

    def get_config(self):
        r"""
        Returns the configuration of the codec.
        
        [`numcodecs.registry.get_codec(config)`][numcodecs.registry.get_codec]
        can be used to reconstruct this codec from the returned config.
        
        Returns
        -------
        config : dict
            Configuration of the codec.
        """
        ...
