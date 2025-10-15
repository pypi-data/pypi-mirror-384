""" Bid for Game
    Acol OverCallersBid module
"""

import inspect
from .bidding import Pass, Double, Call
from .hand import Hand

inspection = inspect.currentframe


class OverCallersThirdBid(Hand):
    """BfG OverCallersRebid class."""
    def __init__(self, hand_cards, board):
        super(OverCallersThirdBid, self).__init__(hand_cards, board)
        self.trace = 0

    def suggested_bid(self):
        """Direct control to relevant method and return a Bid object."""
        my_first_bid = Call(self.bid_history[-8])
        my_second_bid = Call(self.bid_history[-4])
        advancers_first_bid = Call(self.bid_history[-6])
        advancers_last_bid = Call(self.bid_history[-2])
        if (my_first_bid.is_pass and my_second_bid._is_pass and advancers_last_bid.is_pass):
            bid = Pass('2835')
        elif self._advancer_supports_major_after_stayman():
            if self.hcp >= 16:
                bid = self.next_level_bid(self.bid_two.denomination, '2801')
            else:
                bid = Pass('2802')
        elif self._can_show_second_major_after_stayman():
            bid = self.next_level_bid(self.spade_suit, '2803')
        elif self._has_thirteen_points_advancer_supports_second_suit():
            bid = self.next_level_bid(self.bid_two.denomination, '2804')
        elif self._has_fifteen_points_advancer_bids_two_suits():
            bid = self._fifteen_points_advancer_bids_two_suits()
        elif self._is_very_strong_and_five_four():
            if self.second_suit not in self.opponents_suits:
                suit = self.second_suit
            else:
                suit = self.longest_suit
            bid = self.next_level_bid(suit, '2805')
        elif self._is_strong_and_advancer_bids():
            bid = self._strong_hand()
        elif self._three_suits_have_been_bid():
            bid = self._three_suits_bid()
        elif self._has_two_card_support_for_advancers_major():
            bid = self.next_level_bid(self.advancer_suit_one, '2806')
        elif self._has_six_card_suit_advancer_repeats_suit():
            bid = self.next_level_bid(self.longest_suit, '2807')
        elif self._is_strong_advancer_bids_nt_after_stayman():
            bid = self.nt_bid(3, '2808')
        elif advancers_last_bid.is_game:
            bid = Pass('2826')
        elif (advancers_last_bid.denomination.name == self.longest_suit.name and
              self.bid_one.denomination != self.bid_two.denomination):
            bid = Pass('2842')
        elif advancers_last_bid.denomination.name == self.longest_suit.name:
            bid = Pass('2828')
        elif (my_first_bid.name == '1NT' and advancers_last_bid.name == '2NT' and
                self.hcp <= 15):
            bid = Pass('2829')
        elif (my_first_bid.name == '1NT' and advancers_last_bid.name == '2NT' and
                self.hcp <= 15):
            bid = Pass('2829')
        elif (not advancers_last_bid.is_pass and (advancers_last_bid.denomination == my_first_bid.denomination or
                    advancers_last_bid.denomination == my_second_bid.denomination)):
            bid = Pass('2830')
        elif (not advancers_last_bid.is_pass and advancers_first_bid.denomination == advancers_last_bid.denomination and
                self.suit_length(advancers_first_bid.denomination) <= 2):
            bid = Pass('2832')
        elif (not advancers_last_bid.is_pass and
              advancers_first_bid.denomination == advancers_last_bid.denomination and
                self.hcp < 16):
            bid = Pass('2833')
        elif (self.partner_bid_one.is_suit_call and self.advancer_bid_two.is_suit_call and
              self.advancer_suit_one != self.advancer_bid_two.denomination and
              self.suit_holding[self.advancer_suit_one] >= self.suit_holding[self.advancer_bid_two.denomination] + 1 and
              self.next_level(self.advancer_suit_one) < self.next_level(self.advancer_bid_two.denomination) + 1):
            bid = self.next_level_bid(self.advancer_suit_one, '2834')
        elif advancers_last_bid.is_pass:
            bid = Pass('2831')
        elif my_first_bid.is_double and my_second_bid.is_double and advancers_first_bid.is_pass:
            bid = Pass('2836')
        elif self.nt_level >= 3 and self.hcp <= 13:
            bid = Pass('2837')
        elif self.partner_last_bid.name == '2NT' and self.shape[1] <= 3:
            bid = Pass('2844')
        elif (self.advancer_bid_two.is_suit_call and
                self.suit_holding[self.advancer_bid_two.denomination] <= 3):
            bid = Pass('2845')
        elif not self.advancer_bid_two.is_pass:
            bid = Pass('2848')
        elif (self.advancer_bid_one.is_pass and
              self.advancer_bid_two.is_suit_call and
              self.suit_holding[self.advancer_suit_two] <= 3):
            bid = Pass('2850')
        else:
            bid = Pass('2809')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _strong_hand(self):
        """Return bid with strong hand."""
        if self.bid_one.is_double and self.bid_two.is_double:
            bid = Pass('2810')
        elif self._support_for_advancer():
            bid = self.next_level_bid(self.advancer_suit_one, '2811')
        elif self.is_balanced and self.nt_level <= 3:
            bid = self.next_nt_bid('2812')
        elif self.five_five and self.second_suit not in self.opponents_suits:
            bid = self.next_level_bid(self.second_suit, '2813')
        elif self.five_four and self.second_suit not in self.opponents_suits:
            bid = self.next_level_bid(self.second_suit, '2814')
        elif (self.advancer_suit_one != self.partner_last_bid.denomination and
                self.suit_length(self.second_suit) >= 5 and
                self.second_suit not in self.opponents_suits):
            bid = self.next_level_bid(self.second_suit, '2827')
        elif (self.partner_penultimate_bid.name == '1NT' and
              self.partner_last_bid.name == '2NT' and
              self.five_five and
              self.second_suit in self.opponents_suits and
              self.longest_suit not in self.opponents_suits):
            bid = self.next_level_bid(self.longest_suit, '2841')
        elif (self.advancer_suit_one != self.partner_last_bid.denomination and
                self.longest_suit not in self.opponents_suits):
            bid = self.next_level_bid(self.longest_suit, '2815')
        elif (not self.partner_bid_one.is_pass and
                self.suit_length(self.advancer_suit_one) >= 3):
            bid = self.next_level_bid(self.advancer_suit_one, '2816')
        elif self.advancer_bid_two.name == '2NT' and self.hcp <= 17:
            bid = Pass('2840')
        elif self.nt_level >= 4:
            bid = Pass('2846')
        elif self.advancer_suit_two and self.suit_holding[self.advancer_suit_two] <= 1:
            bid = Pass('2847')
        elif 1:
            bid = Pass('2849')
        else:
            bid = Pass('2817')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _three_suits_bid(self):
        """Return bid after 3 suits have been bid."""
        suit_to_bid = self._select_suit_after_three_suits_bid()
        if self._suit_is_minor(suit_to_bid):
            bid = self.next_nt_bid('2818')
        elif suit_to_bid not in self.opponents_suits:
            bid = self.next_level_bid(suit_to_bid, '2821')
        else:
            bid = Pass('2820')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _fifteen_points_advancer_bids_two_suits(self):
        """Return bid if strong and advancer bids two suits."""
        if self.nt_level >= 6 and self.hcp >= 16 and self.is_semi_balanced and self.double_allowed():
            bid = Double('2838')
        elif self.bidding_above_game and self.double_allowed():
            bid = Double('2825')
        elif self._advancer_has_passed_after_double():
            bid = Pass('2822')
        elif (self.advancer_bid_one.is_suit_call and
              self.advancer_suit_one != self.advancer_bid_two.denomination and
              self.suit_length(self.advancer_suit_one) >= 3
              and self.hcp >= 20):
            bid = self.next_level_bid(self.advancer_suit_one,'2839')
        elif (self.advancer_bid_one.is_suit_call and
              self.advancer_suit_one != self.advancer_bid_two.denomination and
              self.suit_length(self.advancer_bid_two.denomination) >= 4
               and self.hcp >= 20):
            # allowed duplicate comment x_refs
            bid = self.next_level_bid(self.advancer_suit_one,'2839')
        elif (self.suit_length(self.opener_suit_one) >= 3 and
                self.suit_points(self.opener_suit_one) >= 5):
            bid = Pass('2823')
        elif (self.advancer_suit_one != self.partner_bid_two.denomination and
              self.hcp >= 15):
            suit = self._suit_preference()
            bid = self.next_level_bid(suit, '2843')
        else:
            bid = Pass('2824')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    # Various utility functions

    def _suit_preference(self):
        """Return preference (if any) for partner's suits."""
        suit = None
        suit_one = None
        suit_two = None
        if (self.partner_bid_one.is_suit_call):
            suit_one = self.partner_bid_one.denomination
        if self.partner_last_bid.denomination.is_suit:
            suit_two = self.partner_last_bid.denomination

        if suit_one and suit_two:
            suit = suit_two
            if self.suit_length(suit_one) >= self.suit_length(suit_two) - 1:
                suit = suit_one
        else:

            if suit_one and self.suit_length(suit_one) >= 3:
                suit = suit_one
            if suit_two and self.suit_length(suit_two) >= 4:
                return suit_two
        if not suit:
            return self.no_trumps
        return suit

    def _select_suit_after_three_suits_bid(self):
        if self.suit_length(self.partner_last_bid.denomination) >= 4:
            return self.partner_last_bid.denomination
        elif self.five_five:
            suit_to_bid = self.second_suit
            if suit_to_bid in self.opponents_suits:
                return self.longest_suit
            return self.second_suit
        return  self.longest_suit

    # Various boolean functions

    def _advancer_supports_major_after_stayman(self):
        """Return True if advancer supports major after Stayman."""
        return (self.bid_one.name == '1NT' and
                self.partner_bid_one.name == '2C' and
                self.partner_last_bid.denomination == self.bid_two.denomination and
                self.partner_last_bid.level == 3)

    def _can_show_second_major_after_stayman(self):
        """Return True if got 4 spades and 4 hearts."""
        return (self.bid_one.name == '1NT' and
                self.partner_bid_one.name == '2C' and
                self.bid_two.name == '2H' and
                self.partner_last_bid.name == '2NT' and
                self.spades >= 4 and
                self.spade_suit not in self.opponents_suits)

    def _has_thirteen_points_advancer_supports_second_suit(self):
        """Return True if 13 points and advancer support second suit."""
        return (self.partner_last_bid.denomination == self.bid_two.denomination and
                self.partner_last_bid.is_suit_call and
                not self.partner_last_bid.is_game and
                self.hcp >= 13 and
                not self.singleton_honour)

    def _has_fifteen_points_advancer_bids_two_suits(self):
        """Return True if fifteen points and advancer bids two suits."""
        return (self.advancer_suit_one != self.partner_last_bid.denomination and
                not self.bid_one.is_nt and
                not self.partner_last_bid.is_nt and
                not self.partner_last_bid.is_game and
                self._suit_preference().is_suit and
                self.hcp >= 15)

    def _is_very_strong_and_five_four(self):
        """Return True if strong and 5/4."""
        return (self.hcp >= 19 and
                self.five_four_or_better and
                not self.bid_two.is_nt and
                not self.bidding_above_game and
                self.longest_suit not in self.opponents_suits)

    def _is_strong_and_advancer_bids(self):
        """Return True if strong and advancer bids."""
        return (self.hcp >= 16 and
                not self.partner_last_bid.is_pass and
                not self.partner_last_bid.is_game)

    def _three_suits_have_been_bid(self):
        """Return True if 3 suits bid."""
        my_suits = [self.bid_one.denomination, self.bid_two.denomination]
        return (self.advancer_suit_one != self.partner_last_bid.denomination and
                self.partner_bid_one.is_suit_call and
                self.partner_last_bid.level == 3 and
                self.bid_one.denomination != self.partner_last_bid.denomination and
                not self.partner_last_bid.is_game and
                self.partner_last_bid.denomination not in my_suits)

    def _advancer_has_passed_after_double(self):
        """Return True if advancer passes after double."""
        return (self.bid_one.is_double and
                (self.partner_bid_one.is_pass or
                 self.partner_last_bid.is_pass))

    def _has_two_card_support_for_advancers_major(self):
        """Return True if 2 card support for advancers major."""
        return (self.advancer_suit_one == self.partner_last_bid.denomination and
                self.partner_bid_one.is_value_call and
                self.advancer_suit_one.is_major and
                self.suit_length(self.advancer_suit_one) >= 2 and
                self.hcp >= 15 and
                not self.partner_last_bid.is_game)
        return result

    def _has_six_card_suit_advancer_repeats_suit(self):
        """Return True if 6 card suit and advancer repeats their suit."""
        return (self.advancer_suit_one == self.partner_last_bid.denomination and
                self.partner_bid_one.is_value_call and
                self.shape[0] >= 6 and
                not self.partner_last_bid.is_game and
                self.longest_suit not in self.opponents_suits and
                self.hcp >= 12)

    def _is_strong_advancer_bids_nt_after_stayman(self):
        """Return True if strong and advancer bids NT after stayman."""
        return (self.bid_one.name == '1NT' and
                self.partner_bid_one.name == '2C' and
                self.partner_last_bid.name == '2NT' and
                self.hcp >= 17 and
                self.nt_level <= 3)

    def _suit_is_minor(self, suit_to_bid):
        """Return True if suit is minor."""
        return (self.nt_level <= 3 and
                (suit_to_bid.is_minor or
                suit_to_bid in self.opponents_suits))

    def _support_for_advancer(self):
        """Return True if xxx."""
        if not self.advancer_bid_two:
           return False
        return (self.advancer_suit_one == self.advancer_bid_two.denomination and
                self.suit_length(self.advancer_suit_one) >= 3)
