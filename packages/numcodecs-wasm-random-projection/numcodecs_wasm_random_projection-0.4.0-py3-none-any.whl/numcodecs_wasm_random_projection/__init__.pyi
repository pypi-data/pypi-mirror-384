__all__ = ['RandomProjection']

import numcodecs.abc

class RandomProjection(numcodecs.abc.Codec):
    r"""
    Codec that uses random projections to reduce the dimensionality of high-
    dimensional data to compress it.
    
    A two-dimensional array of shape $N \times D$ is encoded as n array of
    shape $N \times K$, where $K$ is either set explicitly or chosen using
    the the Johnson-Lindenstrauss lemma. For $K$ to be smaller than $D$,
    $D$ must be quite large. Therefore, this codec should only applied on
    large datasets as it otherwise significantly inflates the data size instead
    of reducing it.
    
    Choosing a lower distortion rate `epsilon` will improve the quality of the
    lossy compression, i.e. reduce the compression error, at the cost of
    increasing $K$.
    
    This codec only supports finite floating point data.
    
    Parameters
    ----------
    projection : ...
         - "gaussian": The random projection matrix is dense and its components are sampled
            from $\text{N}\left( 0, \frac{1}{k} \right)$
        
         - "sparse": The random projection matrix is sparse where only `density`% of entries
            are non-zero.
            
            The matrix's components are sampled from
            
            - $-\sqrt{\frac{1}{k \cdot density}}$ with probability
              $0.5 \cdot density$
            - $0$ with probability $1 - density$
            - $+\sqrt{\frac{1}{k \cdot density}}$ with probability
              $0.5 \cdot density$
    reduction : ...
         - "johnson-lindenstrauss": The reduced dimensionality $K$ is derived from `epsilon`, as defined
            by the Johnson-Lindenstrauss lemma.
        
         - "explicit": The reduced dimensionality $K$, to which the data is projected, is
            given explicitly.
    seed : ...
        Seed for generating the random projection matrix
    _version : ..., optional, default = "0.1.0"
        The codec's encoding format version. Do not provide this parameter explicitly.
    density : ..., optional
        The `density` of the sparse projection matrix.
        
        Setting `density` to $\frac{1}{3}$ reproduces the settings by
        Achlioptas [^1]. If `density` is `None`, it is set to
        $\frac{1}{\sqrt{d}}$,
        the minimum density as recommended by Li et al [^2].
        
        
        [^1]: Achlioptas, D. (2003). Database-friendly random projections:
              Johnson-Lindenstrauss with binary coins. *Journal of Computer
              and System Sciences*, 66(4), 671-687. Available from:
              [doi:10.1016/S0022-0000(03)00025-4](https://doi.org/10.1016/S0022-0000(03)00025-4).
        
        [^2]: Li, P., Hastie, T. J., and Church, K. W. (2006). Very sparse
              random projections. In *Proceedings of the 12th ACM SIGKDD
              international conference on Knowledge discovery and data
              mining (KDD '06)*. Association for Computing Machinery, New
              York, NY, USA, 287–296. Available from:
              [doi:10.1145/1150402.1150436](https://doi.org/10.1145/1150402.1150436).
    epsilon : ..., optional
        Maximum distortion rate
    k : ..., optional
        Reduced dimensionality
    **kwargs
        This codec takes *any* additional parameters.
    """

    def __init__(self, projection, reduction, seed, _version='0.1.0', density=None, epsilon=None, k=None, **kwargs): ...

    codec_id = 'random-projection.rs'

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
