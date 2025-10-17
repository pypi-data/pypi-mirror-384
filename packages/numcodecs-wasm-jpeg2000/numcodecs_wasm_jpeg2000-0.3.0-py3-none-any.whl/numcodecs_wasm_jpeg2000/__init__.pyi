__all__ = ['Jpeg2000']

import numcodecs.abc

class Jpeg2000(numcodecs.abc.Codec):
    r"""
    Codec providing compression using JPEG 2000.
    
    Arrays that are higher-dimensional than 2D are encoded by compressing each
    2D slice with JPEG 2000 independently. Specifically, the array's shape is
    interpreted as `[.., height, width]`. If you want to compress 2D slices
    along two different axes, you can swizzle the array axes beforehand.
    
    Parameters
    ----------
    mode : ...
         - "psnr": Peak signal-to-noise ratio
        
         - "rate": Compression rate
        
         - "lossless": Lossless compression
    _version : ..., optional, default = "0.1.0"
        The codec's encoding format version. Do not provide this parameter explicitly.
    psnr : ..., optional
        Peak signal-to-noise ratio
    rate : ..., optional
        Compression rate, e.g. `10.0` for x10 compression
    """

    def __init__(self, mode, _version='0.1.0', psnr=None, rate=None): ...

    codec_id = 'jpeg2000.rs'

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
