# the order matters for dependencies
# (e.g. pad depends on zeros, hstack and
# vstack)
from .zeros import zeros
from .cat import hstack, vstack, concat
from .eye import eye
from .anti_eye import anti_eye
from .kron import kron
from .ones import ones
from .pad import mpad, pad
from .blockdiag import block_diag
from .add import add
from .kron import kron
from .diag import diag
from .anti_diag import anti_diag
from .roll import roll
from .diff import diff
from .flip import flip
from .slicer import slicer, indexer
from .bitrev import bitrev
from .tri import tri, cumsum
from .padder import padder
