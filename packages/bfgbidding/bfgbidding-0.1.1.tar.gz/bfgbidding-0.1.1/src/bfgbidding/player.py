""" Bid for Game
    Player class
"""
# from termcolor import cprint

from bridgeobjects import ROLES, Board, Hand
from .bidding import Bid
from .acol_bidding import AcolBid
from .utils import get_role, get_active_bid_history

MODULE_COLOUR = 'blue'


class Player(object):
    """Define BfG Player class."""
    NUMBER_OF_PLAYERS = 4

    def __init__(self,
                 board: Board | None = None,
                 hand: Hand | None = None,
                 index: int | None = None) -> None:
        self.board = board
        self.hand = hand
        self.index = index
        self.role = -1

    def __repr__(self) -> str:
        """Return a string representation of player."""
        return f'player: {self.hand}'

    def make_bid(self, update_bid_history: bool = True) -> Bid:
        """Make a bid and return bid object."""
        # roles = Roles(self.board.bid_history)
        self.role = get_role(self.board.bid_history)
        self.board.active_bid_history = get_active_bid_history(self.board.bid_history)

        bid = AcolBid(self.hand, self.board, self.role).bid

        if update_bid_history:
            self.board.bid_history.append(bid.name)
        hc_points = self.hand.high_card_points

        if bid.use_shortage_points:
            distribution_points = 0
            hand_points = f'{hc_points}+{distribution_points}'
            hand_description = f'{hand_points} = {hc_points+distribution_points}'
        else:
            hand_description = str(hc_points)
        hand_description = f'{hand_description} '
        bid.hand_points = hand_description
        return bid
