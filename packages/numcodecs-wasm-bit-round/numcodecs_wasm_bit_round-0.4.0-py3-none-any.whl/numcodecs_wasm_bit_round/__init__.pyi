__all__ = ['BitRound']

import numcodecs.abc

class BitRound(numcodecs.abc.Codec):
    r"""
    Codec providing floating-point bit rounding.
    
    Drops the specified number of bits from the floating point mantissa,
    leaving an array that is more amenable to compression. The number of
    bits to keep should be determined by information analysis of the data
    to be compressed.
    
    The approach is based on the paper by Klöwer et al. 2021
    (<https://www.nature.com/articles/s43588-021-00156-2>).
    
    Parameters
    ----------
    keepbits : ...
        The number of bits of the mantissa to keep.
        
        The valid range depends on the dtype of the input data.
        
        If keepbits is equal to the bitlength of the dtype's mantissa, no
        transformation is performed.
    _version : ..., optional, default = "1.0.0"
        The codec's encoding format version. Do not provide this parameter explicitly.
    """

    def __init__(self, keepbits, _version='1.0.0'): ...

    codec_id = 'bit-round.rs'

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
