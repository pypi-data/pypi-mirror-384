__all__ = ['Zstd']

import numcodecs.abc

class Zstd(numcodecs.abc.Codec):
    r"""
    Codec providing compression using Zstandard
    
    Parameters
    ----------
    level : ...
        Zstandard compression level.
        
        The level ranges from small (fastest) to large (best compression).
    _version : ..., optional, default = "0.1.0"
        The codec's encoding format version. Do not provide this parameter explicitly.
    """

    def __init__(self, level, _version='0.1.0'): ...

    codec_id = 'zstd.rs'

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
