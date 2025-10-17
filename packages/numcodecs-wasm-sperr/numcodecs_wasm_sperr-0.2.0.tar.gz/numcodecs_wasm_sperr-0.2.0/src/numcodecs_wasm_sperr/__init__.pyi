__all__ = ['Sperr']

import numcodecs.abc

class Sperr(numcodecs.abc.Codec):
    r"""
    Codec providing compression using SPERR.
    
    Arrays that are higher-dimensional than 3D are encoded by compressing each
    3D slice with SPERR independently. Specifically, the array's shape is
    interpreted as `[.., depth, height, width]`. If you want to compress 3D
    slices along three different axes, you can swizzle the array axes
    beforehand.
    
    Parameters
    ----------
    mode : ...
         - "bpp": Fixed bit-per-pixel rate
        
         - "psnr": Fixed peak signal-to-noise ratio
        
         - "pwe": Fixed point-wise (absolute) error
        
         - "q": Fixed quantisation step
    _version : ..., optional, default = "0.2.0"
        The codec's encoding format version. Do not provide this parameter explicitly.
    bpp : ..., optional
        positive bits-per-pixel
    psnr : ..., optional
        positive peak signal-to-noise ratio
    pwe : ..., optional
        positive point-wise (absolute) error
    q : ..., optional
        positive quantisation step
    """

    def __init__(self, mode, _version='0.2.0', bpp=None, psnr=None, pwe=None, q=None): ...

    codec_id = 'sperr.rs'

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
