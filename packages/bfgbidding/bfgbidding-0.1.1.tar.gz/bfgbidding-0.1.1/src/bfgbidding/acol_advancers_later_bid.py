""" Bid for Game
    Acol OverCallerRespondersLaterBid module
"""

import inspect
from .bidding import Bid, Pass
from .hand import Hand

inspection = inspect.currentframe


class AdvancersLaterBid(Hand):
    """BfG AdvancersRebid class."""
    def __init__(self, hand_cards, board):
        super().__init__(hand_cards, board)
        if len(self.bid_history) >= 11:
            self.overcaller_bid_one = Bid(self.bid_history[-10], '')
            self.overcaller_bid_two = Bid(self.bid_history[-6], '')
            self.overcaller_bid_three = Bid(self.bid_history[-2], '')
        else:
            self.overcaller_bid_one = Bid(self.bid_history[-6], '')
            self.overcaller_bid_two = None
        self.advancer_bid_one = Bid(self.bid_history[-8], '')
        self.trace = 0

    def suggested_bid(self):
        """Direct control to relevant method and return a Bid object."""
        if self._overcaller_shows_two_suits_after_double():
            bid = self.advancer_preference('4801')
            if (self.suit_length(bid.denomination) <= 2 and
                    self.nt_level <= 3):
                bid = self.nt_bid(3, '4802')
        elif self._has_two_card_support_for_overcallers_six_card_suit():
            if self.overcaller_bid_one.is_double:
                overcaller_bid = self.overcaller_bid_two
            else:
                overcaller_bid = self.overcaller_bid_one
            bid = self.bid_to_game(overcaller_bid.denomination, '4803')
        elif self._can_show_second_five_card_suit():
            bid = self. next_level_bid(self.second_suit, '4804')
        elif self._has_biddable_seven_card_suit():
            bid = self.next_level_bid(self.longest_suit, '4805')
        elif self.overcaller_bid_one.name == '1NT':
            bid = self._responses_to_overcall_of_one_nt()
        else:
            bid = Pass('4806')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responses_to_overcall_of_one_nt(self):
        """Handle responses after overcaller opens 1NT."""
# TODO: this is just a stub - much more logic required
        if self.advancer_bid_one.name == '2C':
            bid = self._responses_after_stayman()
        else:
            bid = Pass('4807')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responses_after_stayman(self):
        """Handle responses after Stayman."""
# TODO: this is just a stub - much more logic required
        if (self.overcaller_bid_two.denomination == self.heart_suit and
                self.overcaller_bid_three.denomination == self.spade_suit):
            if self.spades >= 4:
                bid = self.spade_bid(4, '4808')
            elif self.nt_level <= 3:
                bid = self.nt_bid(3, '4809')
            else:
                bid = Pass('4810')
        else:
            bid = Pass('4811')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    # Various utility functions

    # Various boolean functions

    def _overcaller_shows_two_suits_after_double(self):
        """Return True if overcaller shows two suits after double."""
        result = (self.overcaller_bid_one.is_double and
                  self.overcaller_bid_two.is_suit_call and
                  self.overcaller_bid_three.is_suit_call and
                  self.overcaller_bid_two.denomination != self.overcaller_bid_three.denomination and
                  not self.overcaller_bid_three.is_game)
        return result

    def _has_two_card_support_for_overcallers_six_card_suit(self):
        """Return True if 2 card support for overcallers six card suit."""
        if self.opponents_at_game:
            return False
        if self.overcaller_bid_one.is_double:
            overcaller_bid = self.overcaller_bid_two
        else:
            overcaller_bid = self.overcaller_bid_one
        if self.overcaller_bid_two.is_double:
            overcaller_bid = self.overcaller_bid_three
        else:
            overcaller_bid = self.overcaller_bid_two
        if overcaller_bid.is_pass or overcaller_bid.is_double:
            return False
        game_level = self.bid_to_game(overcaller_bid.denomination).level
        result = (overcaller_bid == self.overcaller_bid_three.denomination and
                  self.suit_length(self.overcaller_bid_one.suit) >= 2 and
                  self.hcp >= 9 and
                  not self.overcaller_bid_three.is_game and
                  self.next_level(overcaller_bid.denomination) <= game_level)
        return result

    def _can_show_second_five_card_suit(self):
        """Return True if can show second 5 card suit."""
        result = (self.five_five and
                  not self.advancer_bid_one.is_pass and
                  self.second_suit not in self.opponents_suits and
                  self.next_level(self.second_suit) <= 4 and
                  (not self.overcaller_bid_three.is_game or
                   self.second_suit.is_major))
        return result

    def _has_biddable_seven_card_suit(self):
        """Return True if can show 7 card suit."""
        result = (not self.overcaller_bid_three.is_pass and
                  self.shape[0] >= 7 and
                  self.next_level(self.longest_suit) <= 4 and
                  self.longest_suit not in self.opponents_suits)
        return result
