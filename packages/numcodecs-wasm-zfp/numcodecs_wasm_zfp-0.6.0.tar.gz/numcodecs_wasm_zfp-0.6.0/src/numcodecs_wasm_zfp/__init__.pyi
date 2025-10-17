__all__ = ['Zfp']

import numcodecs.abc

class Zfp(numcodecs.abc.Codec):
    r"""
    Codec providing compression using ZFP
    
    Parameters
    ----------
    mode : ...
         - "expert": The most general mode, which can describe all four other modes
        
         - "fixed-rate": In fixed-rate mode, each d-dimensional compressed block of $4^d$
            values is stored using a fixed number of bits. This number of
            compressed bits per block is amortized over the $4^d$ values to give
            a rate of $rate = \frac{maxbits}{4^d}$ in bits per value.
        
         - "fixed-precision": In fixed-precision mode, the number of bits used to encode a block may
            vary, but the number of bit planes (the precision) encoded for the
            transform coefficients is fixed.
        
         - "fixed-accuracy": In fixed-accuracy mode, all transform coefficient bit planes up to a
            minimum bit plane number are encoded. The smallest absolute bit plane
            number is chosen such that
            $minexp = \text{floor}(\log_{2}(tolerance))$.
        
         - "reversible": Lossless per-block compression that preserves integer and floating point
            bit patterns.
    _version : ..., optional, default = "0.2.0"
        The codec's encoding format version. Do not provide this parameter explicitly.
    max_bits : ..., optional
        Maximum number of bits used to represent a block
    max_prec : ..., optional
        Maximum number of bit planes encoded
    min_bits : ..., optional
        Minimum number of compressed bits used to represent a block
    min_exp : ..., optional
        Smallest absolute bit plane number encoded.
        
        This parameter applies to floating-point data only and is ignored
        for integer data.
    non_finite : ..., optional, default = "deny"
        ZFP non-finite values mode
    precision : ..., optional
        Number of bit planes encoded
    rate : ..., optional
        Rate in bits per value
    tolerance : ..., optional
        Absolute error tolerance
    """

    def __init__(self, mode, _version='0.2.0', max_bits=None, max_prec=None, min_bits=None, min_exp=None, non_finite='deny', precision=None, rate=None, tolerance=None): ...

    codec_id = 'zfp.rs'

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
