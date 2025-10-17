__all__ = ['Asinh']

import numcodecs.abc

class Asinh(numcodecs.abc.Codec):
    r"""
    Asinh codec, which applies a quasi-logarithmic transformation on encoding.
    
    For values close to zero that are within the codec's `linear_width`, the
    transform is close to linear. For values of larger magnitudes, the
    transform is asymptotically logarithmic. Unlike a logarithmic transform,
    this codec supports all finite values, including negative values and zero.
    
    In detail, the codec calculates
    $c = w \cdot \text{asinh}\left( \frac{x}{w} \right)$
    on encoding and
    $d = w \cdot \text{sinh}\left( \frac{c}{w} \right)$
    on decoding, where $w$ is the codec's `linear_width`.
    
    The codec only supports finite floating point numbers.
    
    Parameters
    ----------
    linear_width : ...
        The width of the close-to-zero input value range where the transform is
        nearly linear
    _version : ..., optional, default = "1.0.0"
        The codec's encoding format version. Do not provide this parameter explicitly.
    """

    def __init__(self, linear_width, _version='1.0.0'): ...

    codec_id = 'asinh.rs'

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
