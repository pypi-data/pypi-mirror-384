__all__ = ['Sz3']

import numcodecs.abc

class Sz3(numcodecs.abc.Codec):
    r"""
    Codec providing compression using SZ3
    
    Parameters
    ----------
    eb_mode : ...
         - "abs-and-rel": Errors are bounded by *both* the absolute and relative error, i.e. by
            whichever bound is stricter
        
         - "abs-or-rel": Errors are bounded by *either* the absolute or relative error, i.e. by
            whichever bound is weaker
        
         - "abs": Absolute error bound
        
         - "rel": Relative error bound
        
         - "psnr": Peak signal to noise ratio error bound
        
         - "l2": Peak L2 norm error bound
    _version : ..., optional, default = "0.1.0"
        The codec's encoding format version. Do not provide this parameter explicitly.
    eb_abs : ..., optional
        Absolute error bound
    eb_l2 : ..., optional
        Peak L2 norm error bound
    eb_psnr : ..., optional
        Peak signal to noise ratio error bound
    eb_rel : ..., optional
        Relative error bound
    predictor : ..., optional, default = "cubic-interpolation-lorenzo"
        Predictor
    """

    def __init__(self, eb_mode, _version='0.1.0', eb_abs=None, eb_l2=None, eb_psnr=None, eb_rel=None, predictor='cubic-interpolation-lorenzo'): ...

    codec_id = 'sz3.rs'

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
