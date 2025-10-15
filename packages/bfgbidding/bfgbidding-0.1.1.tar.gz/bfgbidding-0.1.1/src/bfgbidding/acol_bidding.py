""" Bid for Game
    Acol bidding module
"""

# trace 2.0.8

from bridgeobjects import ROLES, Board, Card
from .bidding import Bid, Pass, Call
from .hand import Hand
from .acol_openers_bid import OpeningBid
from .acol_openers_rebid import OpenersReBid
from .acol_openers_third_bid import OpenersThirdBid
from .acol_openers_later_bid import OpenersLaterBid
from .acol_responders_bid import RespondersBid
from .acol_responders_rebid import RespondersRebid
from .acol_responders_later_bid import RespondersLaterBid
from .acol_overcallers_bid import OverCallersBid
from .acol_overcallers_rebid import OverCallersRebid
from .acol_overcallers_third_bid import OverCallersThirdBid
from .acol_advancers_bid import AdvancersBid
from .acol_advancers_rebid import AdvancersRebid
from .acol_advancers_later_bid import AdvancersLaterBid


class AcolBid(object):
    """BfG AcolBid class."""
    def __init__(self, hand: Hand, board: Board, role: int):
        """
            Identify the bidder and direct control accordingly.

            Return a bid.
        """
        self.board = board
        bid_history = board.active_bid_history
        self.bid = self.get_bid(hand.cards, bid_history, role)

    def get_bid(self, hand_cards: list[Card], bid_history: list[Call], role: int) -> Bid:
        """Direct bidding to correct bidder and return a bid."""
        if role == ROLES['Opener']:
            bid = self.openers_bid(hand_cards, bid_history)
        elif role == ROLES['Responder']:
            bid = self.responders_bid(hand_cards, bid_history)
        elif role == ROLES['Overcaller']:
            bid = self.overcallers_bid(hand_cards, bid_history)
        elif role == ROLES['Advancer']:
            bid = self.advancers_bid(hand_cards, bid_history)
        else:
            assert False, 'Bid not defined'
        return bid

    def openers_bid(self, hand_cards: list[Card], bid_history: list[Call]) -> Bid:
        """Return opener's bid."""
        if not bid_history:
            bid = OpeningBid(hand_cards, self.board).suggested_bid()
        elif len(bid_history) == 4:
            bid = OpenersReBid(hand_cards, self.board).suggested_bid()
        elif len(bid_history) == 8:
            bid = OpenersThirdBid(hand_cards, self.board).suggested_bid()
        else:
            bid = OpenersLaterBid(hand_cards, self.board).suggested_bid()
        return bid

    def responders_bid(self, hand_cards: list[Card], bid_history: list[Call]) -> Bid:
        """Return responder's bid."""
        if len(bid_history) == 2:
            bid = RespondersBid(hand_cards, self.board).suggested_bid()
        elif len(bid_history) == 6:
            bid = RespondersRebid(hand_cards, self.board).suggested_bid()
        else:
            bid = RespondersLaterBid(hand_cards, self.board).suggested_bid()
        return bid

    def overcallers_bid(self, hand_cards: list[Card], bid_history: list[Call]) -> Bid:
        """Return overcaller's bid."""
        if len(bid_history) <= 4:
            bid = OverCallersBid(hand_cards, self.board).suggested_bid()
        elif len(bid_history) <= 8:
            bid = OverCallersRebid(hand_cards, self.board).suggested_bid()
        elif len(bid_history) <= 12:
            bid = OverCallersThirdBid(hand_cards, self.board).suggested_bid()
        else:
            bid = Pass('130')
        return bid

    def advancers_bid(self, hand_cards: list[Card], bid_history: list[Call]) -> Bid:
        """Return overcaller responder's bid."""
        if (len(bid_history) <= 6 or
                (Bid(bid_history[-4]).is_pass and
                 len(bid_history) <= 6)):
            bid = AdvancersBid(hand_cards, self.board).suggested_bid()
        elif len(bid_history) <= 10:
            bid = AdvancersRebid(hand_cards, self.board).suggested_bid()
        elif len(bid_history) <= 14:
            bid = AdvancersLaterBid(hand_cards, self.board).suggested_bid()
        else:
            bid = Pass('130')
        return bid
