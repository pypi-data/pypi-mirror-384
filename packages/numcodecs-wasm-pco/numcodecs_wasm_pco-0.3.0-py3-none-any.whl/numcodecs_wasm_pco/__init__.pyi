__all__ = ['Pco']

import numcodecs.abc

class Pco(numcodecs.abc.Codec):
    r"""
    Codec providing compression using pco
    
    Parameters
    ----------
    delta : ...
         - "auto": Automatically detects a detects a good delta encoding.
            
            This works well most of the time, but costs some compression time and
            can select a bad delta encoding in adversarial cases.
        
         - "none": Never uses delta encoding.
            
            This is best if your data is in a random order or adjacent numbers have
            no relation to each other.
        
         - "try-consecutive": Tries taking nth order consecutive deltas.
            
            Supports a delta encoding order up to 7. For instance, 1st order is
            just regular delta encoding, 2nd is deltas-of-deltas, etc. It is legal
            to use 0th order, but it is identical to None.
        
         - "try-lookback": Tries delta encoding according to an extra latent variable of
            "lookback".
            
            This can improve compression ratio when there are nontrivial patterns
            in the array, but reduces compression speed substantially.
    level : ...
        Compression level, ranging from 0 (weak) over 8 (very good) to 12
        (expensive)
    mode : ...
         - "auto": Automatically detects a good mode.
            
            This works well most of the time, but costs some compression time and
            can select a bad mode in adversarial cases.
        
         - "classic": Only uses the classic mode
        
         - "try-float-mult": Tries using the `FloatMult` mode with a given base.
            
            Only applies to floating-point types.
        
         - "try-float-quant": Tries using the `FloatQuant` mode with the given number of bits of
            quantization.
            
            Only applies to floating-point types.
        
         - "try-int-mult": Tries using the `IntMult` mode with a given base.
            
            Only applies to integer types.
    paging : ...
         - "equal-pages-up-to": Divide the chunk into equal pages of up to this many numbers.
            
            For example, with equal pages up to 100,000, a chunk of 150,000 numbers
            would be divided into 2 pages, each of 75,000 numbers.
    _version : ..., optional, default = "0.1.0"
        The codec's encoding format version. Do not provide this parameter explicitly.
    delta_encoding_order : ..., optional
        the order of the delta encoding
    equal_pages_up_to : ..., optional, default = 262144
        maximum amount of numbers in a page
    float_mult_base : ..., optional
        the base for the `FloatMult` mode
    float_quant_bits : ..., optional
        the number of bits to which floating-point values are quantized
    int_mult_base : ..., optional
        the base for the `IntMult` mode
    """

    def __init__(self, delta, level, mode, paging, _version='0.1.0', delta_encoding_order=None, equal_pages_up_to=262144, float_mult_base=None, float_quant_bits=None, int_mult_base=None): ...

    codec_id = 'pco.rs'

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
