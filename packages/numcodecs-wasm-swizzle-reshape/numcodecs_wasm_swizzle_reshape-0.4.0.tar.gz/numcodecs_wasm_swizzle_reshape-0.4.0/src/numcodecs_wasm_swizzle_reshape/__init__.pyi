__all__ = ['SwizzleReshape']

import numcodecs.abc

class SwizzleReshape(numcodecs.abc.Codec):
    r"""
    Codec to swizzle/swap the axes of an array and reshape it.
    
    This codec does not store metadata about the original shape of the array.
    Since axes that have been combined during encoding cannot be split without
    further information, decoding may fail if an output array is not provided.
    
    Swizzling axes is always supported since no additional information about the
    array's shape is required to reconstruct it.
    
    Parameters
    ----------
    axes : ...
        The permutation of the axes that is applied on encoding.
        
        The permutation is given as a list of axis groups, where each group
        corresponds to one encoded output axis that may consist of several
        decoded input axes. For instance, `[[0], [1, 2]]` flattens a three-
        dimensional array into a two-dimensional one by combining the second and
        third axes.
        
        The permutation also allows specifying a special catch-all remaining
        axes marker:
        - `[[0], {}]` moves the second axis to be the first and appends all
          other axes afterwards, i.e. the encoded array has the same number
          of axes as the input array
        - `[[0], [{}]]` in contrast collapses all other axes into one, i.e.
          the encoded array is two-dimensional
    _version : ..., optional, default = "1.0.0"
        The codec's encoding format version. Do not provide this parameter explicitly.
    """

    def __init__(self, axes, _version='1.0.0'): ...

    codec_id = 'swizzle-reshape.rs'

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
