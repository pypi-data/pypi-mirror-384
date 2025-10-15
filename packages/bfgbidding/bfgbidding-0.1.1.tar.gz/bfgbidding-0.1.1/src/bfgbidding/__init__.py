"""Expose the classes in the API."""
from ._version import __version__
# from icecream import ic, install
# ic.configureOutput(includeContext=True)
# install()


from .hand import Hand
from .comments import comments, strategies, comment_xrefs, convert_text_to_html
from .strategy_xref import StrategyXref, strategy_descriptions
from .bidding import Bid, Pass, Double
from .player import Player
from .utils import get_role

VERSION = __version__
