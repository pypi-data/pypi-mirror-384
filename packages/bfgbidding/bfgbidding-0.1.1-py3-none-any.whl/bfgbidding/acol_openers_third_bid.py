""" Bid for Game
    Acol Opener's third bid module
"""

import inspect
from .bidding import Pass
from .blackwood import Blackwood
from .hand import Hand

inspection = inspect.currentframe


class OpenersThirdBid(Hand):
    """BfG OpeningThirdBid class."""
    def __init__(self, hand_cards, board):
        super(OpenersThirdBid, self).__init__(hand_cards, board)
        self.last_level = 1
        self.responder_weak_1nt = (self.responder_bid_one.name == '1NT')
        self.opener_two_suited = self.bid_one.denomination != self.bid_two.denomination
        self.stayman_bid = (self.bid_one.is_nt and
                            self.responder_bid_one.denomination == self.club_suit and
                            self.last_bid.is_pass)
        self.trace = 0

    def suggested_bid(self):
        """Directs control to relevant method and returns a Bid object."""
        if self.bid_two.name == '4NT':
            bid = self._blackwood_bids()
        elif self.responder_bid_two.name == '4NT':
            bid = Blackwood(self.cards, self.board).count_aces()
        elif self.bid_two.is_pass or self.responder_bid_two.is_pass:
            bid = self._weak_contested_auction()
        elif self.responder_bid_two.is_nt:
            bid = self._responder_bids_nt()
        elif self._four_suits_bid():
            bid = self._rebid_after_four_suits()
        elif self._strong_responder_better_than_minimum():
            bid = self.nt_bid(4, '1601')
        elif self._both_partners_better_than_minimum_and_no_overcall():
            bid = self.nt_bid(4, '1602')
        elif self.responder_bid_two.is_game:
            bid = Pass('1603')
        elif self.last_level >= 5:
            bid = Pass('1723')
        elif self._responder_supports_opener():
            bid = self._responder_support()
        elif self._three_card_support_for_responders_major():
            bid = self.next_level_bid(self.responder_bid_one.denomination, '1604')
        elif (self.responder_bid_one.denomination == self.responder_bid_two.denomination and
              not self.responder_bid_one.is_pass):
            bid = self._responder_repeats_suit()
        elif self.five_five_or_better:
            bid = self._rebid_with_five_five()
        elif self._has_seven_card_major():
            bid = self.suit_bid(4, self.longest_suit, '1605')
        elif self._responder_bid_one_is_clubs():
            bid = self._support_for_responder()
        elif self._three_card_support_for_responders_second_suit():
            bid = self.next_level_bid(self.responder_bid_two.denomination, '1606')
        elif self.overcaller_bid_one.is_double and self.shape[0] >= 6:
            bid = self.next_level_bid(self.longest_suit, '1607')
        elif self._three_suits_bid():
            bid = self.next_nt_bid('1608')
        elif self.shape[0] >= 6:
            bid = self._rebid_long_suit()
        elif self.bid_two.name == '2NT' and self.responder_bid_two.denomination.is_major:
            bid = self._responder_shows_five_card_major()
        else:
            bid = Pass('1609')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_shows_five_card_major(self):
        """Return bid after 2NT when responder shows a 5 card suit."""
        suit = self.responder_bid_two.denomination
        if self.suit_length(suit) >= 3:
            bid = self.bid_to_game(suit, '1610')
        elif self.nt_level <= 3:
            bid = self.bid_to_game(self.no_trumps, '1611')
        elif (self.overcallers_last_bid.level >= 4 and
              self.suit_holding[self.responder_bid_two.denomination] <= 2):
            bid = Pass('1612')
        else:
            bid = Pass('1724')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _blackwood_bids(self):
        """Bid if in Blackwood process."""
        if Blackwood(self.cards, self.board).four_aces:
            if self.responder_bid_one.level == 4 and self.hcp <= 22:
                bid = self.suit_bid(6, self.bid_one.denomination, '1613')
            else:
                bid = self.nt_bid(5, '1614')
        else:
            bid = Blackwood(self.cards, self.board).select_contract()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _weak_contested_auction(self):
        """Bid if contested but weak or partner passes."""
        preference_suit = self._show_preference()
        if self._four_card_support_for_responder_and_passed():
            bid = self.next_level_bid(self.responder_bid_one.denomination, '1615')
        elif self.overcaller_bid_two.is_game:
            bid = Pass('1719')
        elif (self.overcaller_bid_one.is_double and
              self.responder_bid_two.is_pass and
              not (self.overcaller_bid_two.is_pass and
                   self.advancer_bid_two.is_pass)):
            bid = Pass('1616')
        elif self.shape[0] >= 7:
            bid = self._rebid_long_suit()
        elif self._can_rebid_long_suit_at_level_three():
            bid = self.next_level_bid(self.longest_suit, '1617')
        elif self._three_suits_bid_contested_auction(preference_suit):
            bid = self.bid_to_game(preference_suit, '1618')
        elif (self.hcp >= 16 and
                self.shape[0] >= 6 and
                self.next_level(self.bid_one.denomination) <= 3):
            bid = self.next_level_bid(self.bid_one.denomination, '1619')
        elif self._can_support_responders_four_card_major():
            bid = self.next_level_bid(self.responder_bid_two.denomination, '1620')
        elif self._responder_promises_stopper():
            bid = self.nt_bid(3, '1621')
        elif (self.hcp <= 14 and
              self.bid_one.is_minor and
              self.responder_bid_two.denomination == self.bid_one.denomination):
            bid = Pass('1712')
        elif self.next_level(self.bid_one.denomination) > 4:
            bid = Pass('1713')
        elif self.hcp <= 10:
            bid = Pass('1714')
        elif self.bid_one.name == '1NT' and self.bid_two.is_pass:
            bid = Pass('1715')
        elif self.responder_bid_two.is_pass:
            bid = Pass('1716')
        else:
            bid = Pass('1622')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_support(self):
        """Rebid with responder support."""
        if self._responder_has_jumped_in_minor():
            bid = self.nt_bid(3, '1623')
        elif self._intermediate_with_six_four():
            bid = self.next_level_bid(self.opener_suit_one, '1624')
        elif self._responder_repeats_suit_and_can_support():
            bid = self.next_level_bid(self.opener_suit_two, '1625')
        elif self._responder_has_invited_in_six_card_suit():
            bid = self.bid_to_game(self.longest_suit, '1626')
        elif self._responder_has_invited_in_second_suit():
            bid = self.bid_to_game(self.second_suit, '1705')
        elif self._weak_and_two_suited():
            bid = Pass('1628')
        elif self.opener_bid_one.name == '1NT' and self.hcp == 14:
            bid = self.bid_to_game(self.opener_suit_two, '1629')
        elif not self.responder_weak_1nt or self.hcp >= 17:
            bid = self._responder_support_strong()
        elif self.responder_bid_one.level >= 2:
            bid = self._responder_support_strong()
        else:
            bid = Pass('1630')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_support_strong(self):
        """Rebid with responder support with strong hand."""
        if (self.responder_bid_one.is_pass and
                self.responder_bid_two.denomination == self.opener_suit_one and
                self.responder_bid_two.level == 2):
            bid = Pass('1721')
        elif (self.responder_bid_two.denomination == self.opener_suit_one and
                self.responder_bid_two.level == 2):
            bid = Pass('1631')
        elif self._can_bid_again():
            bid = self._responder_support_strong_constructive()
        elif self._better_than_minimum_six_card_major():
            bid = self.bid_to_game(self.longest_suit, '1632')
        elif self._respsonder_invites_game_in_minor():
            bid = self.next_level_bid(self.opener_suit_one, '1633')
        else:
            bid = Pass('1634')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_support_strong_constructive(self):
        """Rebid with responder support - constructive"""
        if self._responder_rebids_minor_and_semi_balanced():
            bid = self.nt_bid(3, '1635')
        elif self.hcp >= 19 and self.is_balanced and self.nt_level <= 3:
            bid = self.nt_bid(3, '1636')
        elif self._strong_and_responder_supports_four_card_major():
            bid = self.nt_bid(3, '1637')
        elif self._strong_or_responder_bids_minor_at_level_four():
            bid = self.next_level_bid(self.responder_bid_two.denomination, '1638')
        elif self._responder_has_jumped_in_openers_minor():
            bid = self.bid_to_game(self.opener_suit_one, '1639')
        elif self.responder_bid_two.denomination.is_minor:
            bid = Pass('1640')
        elif self.hcp >= 15 and self.responder_bid_one.level >= 2:
            if (self.responder_bid_two.denomination == self.bid_two.denomination and
                    self.hcp >= 15):
                bid = self.next_level_bid(self.bid_two.denomination, '1641')
            else:
                bid = self.nt_bid(3, '1642')
        elif self._has_five_card_major() and not self.responder_weak_bid():
            bid = self.suit_bid(4, self.bid_one.denomination, '1643')
        elif self._responder_has_jumped_in_openers_major():
            suit = self.opener_suit_one
            if (self.suit_length(suit) <= 4 and
                    self.stoppers_in_bid_suits and self.nt_level <= 3):
                bid = self.nt_bid(3, '1646')
            else:
                bid = self.bid_to_game(suit, '1646')
        elif (16 <= self.hcp <= 17 and
              self.responder_bid_two.denomination == self.bid_two.denomination):
            bid = Pass('1647')
        elif (self.responder_bid_one.is_pass):
            bid = Pass('1717')
        else:
            bid = Pass('1718')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _support_for_responder(self):
        """Rebid with support for responder"""
        suit = self._select_better_suit_from_partner()
        level = self.next_level(suit)
        opener_previously_jumped = False  # see hand 3_9_9
        if self.hcp >= 16 and not opener_previously_jumped and level < 4:
            level += 1
        if (suit.is_minor and
                self.three_suits_bid_and_stopper() and
                self.nt_level <= 3):
            bid = self.nt_bid(3, '1648')
        elif self.shape[0] >= 6 and self.longest_suit.is_major:
            bid = self.next_level_bid(self.longest_suit, '1649')
        elif (self.is_jump(self.opener_bid_two, self.responder_bid_two) and
                self.responder_bid_one.denomination.is_major and
                self.suit_length(self.responder_bid_one.denomination) >= 3 and
                self.next_level(self.responder_bid_one.denomination) <= 4):
            bid = self.bid_to_game(self.responder_bid_one.denomination, '')
        elif ((suit == self.responder_bid_one.denomination and
               self.suit_holding[suit] >= 3) or
              (suit == self.responder_bid_two.denomination and
               self.suit_holding[suit] >= 4)):
            bid = self.suit_bid(level, suit, '1650')
        else:
            bid = self.suit_bid(level, suit, '1716')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_bids_nt(self):
        """Rebid after responder bids NT"""
        if self.responder_bid_two.name == '6NT':
            bid = Pass('1651')
        elif self.responder_bid_two.name == '5NT' and self.bid_history[-6] == '4NT':
            bid = Blackwood(self.cards, self.board).count_kings()
        elif self.responder_bid_two.name == '2NT':
            bid = self._responder_bids_two_nt()
        elif self.hcp == 19 and self.responder_bid_two.name == '3NT':
            bid = self.nt_bid(6, '1652')
        elif self._responder_bids_three_nt_after_stayman_two_four_card_majors():
            bid = self._responder_bids_3nt_and_stayman()
        elif self.hcp >= 16 and self.five_five_or_better:
            bid = self.next_level_bid(self.bid_two.denomination, '1653')
        elif (self.five_five_or_better and
                self.second_suit not in self.opponents_suits):
            bid = self.next_level_bid(self.second_suit, '1654')
        elif self.hcp >= 16 and self.nt_level <= 3:
            bid = self.next_nt_bid('1655')
        elif self.responder_bid_two.is_game:
            bid = Pass('1656')
        else:
            bid = Pass('1728')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_bids_two_nt(self):
        """Rebid after responder bids 2NT"""
        if self._better_than_minimum_and_five_card_suit():
            bid = self.nt_bid(3, '1657')
        elif self._can_call_3nt():
            bid = self.nt_bid(3, '1658')
        elif self.shape[0] >= 7:
            bid = self.next_level_bid(self.longest_suit, '1659')
        elif self.stayman_bid:
            bid = self._nt_has_been_bid_after_stayman()
        elif (self.hcp >= 15 and
              self.opener_bid_two.is_suit_call and
              self.responder_bid_one.is_suit_call and
              (self.shape[0] <= 5 or
               self.longest_suit.is_minor)):
            bid = self.next_nt_bid('1660')
        elif self.shape[0] >= 6 and self.hcp <= 14:
            bid = self.next_level_bid(self.longest_suit, '1661')
        elif self.shape[0] >= 6:
            bid = self.bid_to_game(self.longest_suit, '1662')
        else:
            bid = Pass('1663')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _nt_has_been_bid_after_stayman(self):
        """Return bid if NT has been bid after Stayman."""
        suit = None
        if self._two_four_card_majors_after_stayman():
            if (self.bid_two.denomination == self.heart_suit and
                    self.spade_suit not in self.opponents_suits):
                suit = self.spade_suit
            elif self.heart_suit not in self.opponents_suits:
                suit = self.heart_suit
            if suit:
                if self.next_level(suit) <= 4:
                    bid = self.bid_to_game(suit, '1664')
                # elif self.nt_level <= 3:
                #     bid = self.nt_bid(3, '1665')
                # else:
                #     bid = Pass('1666')
            elif self.hcp >= 13 and self.nt_level <= 3:
                bid = self.nt_bid(3, '1711')
            else:
                bid = Pass('1708')
        elif self._maximum_after_stayman():
            bid = self.nt_bid(3, '1668')
        elif self._minimum_after_stayman():
            bid = Pass('1669')
        else:
            bid = Pass('1725')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_bids_3nt_and_stayman(self):
        """Rebid after responder bids 3NT and stayman"""
        if self._has_two_four_card_majors_after_hearts():
            bid = self.next_level_bid(self.spade_suit, '1670')
        elif self._has_two_four_card_majors_after_spades():
            bid = self.next_level_bid(self.heart_suit, '1671')
        elif self.responder_bid_two.name == '3NT':
            bid = Pass('1709')
        else:
            bid = Pass('1726')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_long_suit(self):
        """Rebid own long suit"""
        if self.responder_bid_two.is_game:
            bid = Pass('1673')
        elif self.shape[0] >= 8:
            bid = self._rebid_long_suit_eight_cards()
        elif self.shape[0] == 7:
            bid = self._rebid_long_suit_seven_cards()
        elif self.shape[0] == 6:
            if self._responder_has_jumped_in_major():
                bid = self.next_level_bid(self.responder_bid_one.denomination, '1674')
            else:
                bid = self._rebid_long_suit_six_cards()
        else:
            bid = Pass('1710')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_long_suit_eight_cards(self):
        """Rebid own long suit - 8+ cards"""
        suit = self.longest_suit
        if self.next_level(suit) <= 4:
            bid = self.suit_bid(4, suit, '1676')
        else:
            bid = Pass('1677')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_long_suit_seven_cards(self):
        """Rebid own long suit - 7 cards"""
        if self.shape[1] >= 5 and self.second_suit not in self.opponents_suits:
            bid = self.next_level_bid(self.second_suit, '1678')
        elif self._can_bid_strong_major_at_level_three():
            bid = self.next_level_bid(self.longest_suit, '1679')
        elif self.shape[0] >= 7 and self.hcp >= 15:
            bid = self.next_level_bid(self.longest_suit, '1680')
        elif (self.hcp <= 14 and self.responder_bid_one.name == '1NT' and
              not self.overcaller_bid_one.is_pass):
            bid = Pass('1681')
        else:
            bid = Pass('1722')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_long_suit_six_cards(self):
        """Rebid own long suit - 6 cards"""
        if self.shape[1] >= 5 and self.second_suit not in self.opponents_suits:
            suit = self.second_suit
            bid = self.next_level_bid(suit, '1682')
        elif (self.is_jump(self.bid_one,  self.responder_bid_one) and self.hcp >= 12):
            bid = self.next_level_bid(self.longest_suit, '1683')
        elif self.responder_bid_one.level == 2 and self.hcp >= 15:
            bid = self.next_level_bid(self.longest_suit, '1684')
        elif self._responder_changes_suit_at_level_three():
            bid = self.next_level_bid(self.longest_suit, '1685')
        elif (self.partner_bid_one.is_suit_call and
                self.partner_bid_one.denomination != self.partner_bid_two.denomination):
            bid = self.next_level_bid(self.longest_suit, '1686')
        # elif self._responder_jumps_in_major():
        #     if self.suit_length(self.partner_bid_one.denomination) >= 2:
        #         bid = self.bid_to_game(self.partner_bid_one.denomination, '1687')
        #     else:
        #         bid = self.nt_bid(3, '1688')
        elif (self.hcp <= 15 and
              self.responder_bid_one.denomination == self.responder_bid_two.denomination):
            bid = Pass('1689')
        else:
            bid = Pass('1720')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_repeats_suit(self):
        """Rebid responder has repeated suit"""
        if self._is_unbalanced_and_has_two_card_support_for_responders_major():
            bid = self.next_level_bid(self.responder_bid_one.denomination, '1690')
        elif self.shape[0] >= 6:
            bid = self._rebid_long_suit()
        elif self.is_balanced and self.hcp >= 18 and self.nt_level <= 3:
            bid = self.next_nt_bid('1691')
        elif self.is_balanced and self.responder_bid_two.level <= 3:
            bid = Pass('1692')
        else:
            bid = self._support_responders_rebid_suit()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _support_responders_rebid_suit(self):
        """Rebid responder has repeated suit, support suit."""
        responders_suit = self.responder_bid_one.denomination
        # hand_value_points = (self.hcp + self.support_shape_points(responders_suit))
        if self.five_five_or_better and self.hcp >= 13:
            bid = self._rebid_with_five_five()
        elif self.bid_one.name == '2C' and self.five_four_or_better:
            bid = self.next_level_bid(self.second_suit, '1693')
        elif self._can_raise_responders_invitation():
            bid = self.next_level_bid(responders_suit, '1694')
        elif self._strong_with_stoppers():
            bid = self.nt_bid(3, '1698')
        elif self._responder_repeats_suit_after_two_nt():
            bid = self.nt_bid(3, '1699')
        elif self._partner_bid_minor_at_level_four_two_card_support():
            bid = self.suit_bid(6, responders_suit, '1700')
        elif self.suit_holding[self.responder_bid_two.denomination] <= 2:
            bid = Pass('1701')
        else:
            bid = Pass('1729')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_with_five_five(self):
        """Rebid with 5/5 hand."""
        suit = self.bid_two.denomination
        if (self.partner_bid_one.name == '1NT' and
                self.partner_bid_two.level == 3):
            bid = Pass('1702')
        elif self.suit_length(self.responder_bid_two.denomination) >= 5:
            bid = self.next_level_bid(self.responder_bid_two.denomination, '1703')
        elif True:
            bid = self.next_level_bid(suit, '1704')
        else:
            bid = self.next_level_bid(suit, '1727')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_after_four_suits(self):
        """Rebid after 4 suits bid."""
        suit = self._select_after_four_suits()
        if suit == self.responder_bid_two.denomination and self.responder_bid_two.is_game:
            bid = Pass('1705')
        elif (self.nt_level <= 3 and
                self.suit_stopper(self.responder_bid_two.denomination)):
            bid = self.nt_bid(3, '1706')
        else:
            bid = self.next_level_bid(suit, '1707')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    # Various utility functions

    def _select_better_suit_from_partner(self):
        """Return the best suit after parner shows two"""
        if (self.responder_bid_two.denomination.is_major and
                self.suit_length(self.responder_bid_two.denomination) >= 4):
            return self.responder_bid_two.denomination
        elif self.suit_length(self.responder_bid_one.denomination) >= 3:
            return self.responder_bid_one.denomination
        elif self.suit_length(self.responder_bid_two.denomination) >= 3:
            return self.responder_bid_two.denomination
        assert False, 'suit not assigned'

    def _select_after_four_suits(self):
        """Select suit after 4 have been bid."""
        suit_one = self.responder_bid_one.denomination
        suit_two = self.responder_bid_two.denomination
        holding_one = 6 + self.suit_length(suit_one)
        holding_two = 5 + self.suit_length(suit_two)
        if holding_one == holding_two:
            if suit_one.is_major:
                suit = suit_one
            elif suit_two.is_major:
                suit = suit_two
            else:
                suit = suit_one
        elif holding_one > holding_two:
            suit = suit_one
        else:
            suit = suit_two
        if self.suit_length(suit) <= 1:
            if self.shape[1] >= 5:
                suit = self.second_suit
            else:
                suit = self.longest_suit
        self.tracer(__name__, inspection(), suit, self.trace)
        return suit

    # Various boolean functions

    def _four_suits_bid(self):
        """Return True if all 4 suits have been bid."""
        value = False
        suits_bid = (self.bid_one.is_suit_call and
                     self.bid_two.is_suit_call and
                     self.responder_bid_one.is_suit_call and
                     self.responder_bid_two.is_suit_call)
        if (suits_bid and
                self.bid_one.denomination != self.bid_two.denomination and
                self.bid_one.denomination != self.responder_bid_one.denomination and
                self.bid_one.denomination != self.responder_bid_two.denomination and
                self.bid_two.denomination != self.responder_bid_one.denomination and
                self.bid_two.denomination != self.responder_bid_two.denomination and
                self.responder_bid_one.denomination != self.responder_bid_two.denomination):
            value = True
        return value

    def _responder_supports_opener(self):
        """Return True if responder supports opener."""
        value = False
        if (self.responder_bid_two.denomination == self.bid_one.denomination or
                self.responder_bid_two.denomination == self.bid_two.denomination):
            value = True
        return value

    def _show_preference(self):
        """Return suit preference."""
        if self.responder_bid_one.is_suit_call:
            holding_one = self.suit_length(self.responder_bid_one.denomination)
        else:
            holding_one = 0
        if self.responder_bid_two.is_suit_call:
            holding_two = self.suit_length(self.responder_bid_two.denomination)
        else:
            holding_two = 0
        if holding_one >= holding_two + 1:
            suit = self.responder_bid_one.denomination
        else:
            suit = self.responder_bid_two.denomination
        return suit

    def _strong_responder_better_than_minimum(self):
        """Return True if strong and responder better than minimum."""
        return (self.is_jump(self.bid_one, self.responder_bid_one) and
                not self.overcall_made and
                self.hcp >= 17 and
                self.nt_level <= 4)

    def _both_partners_better_than_minimum_and_no_overcall(self):
        """Return True if better than minimum and no overcall."""
        return (self.is_jump(self.bid_one, self.responder_bid_one) and
                not self.overcall_made and
                self.hcp >= 15 and
                self.nt_level <= 4 and
                not self.is_jump(self.bid_two, self.responder_bid_two))

    def _three_card_support_for_responders_major(self):
        """Return True if 3 card support for responders major."""
        return (self.responder_bid_one.denomination == self.responder_bid_two.denomination and
                self.responder_bid_one.denomination.is_major and
                self.suit_length(self.responder_bid_one.denomination) >= 3 and
                self.next_level(self.responder_bid_one.denomination) <= 4)

    def _has_seven_card_major(self):
        """Return True if hand has 7 card major."""
        return (self.shape[0] >= 7 and
                self.longest_suit.is_major and
                self.next_level(self.longest_suit) <= 4)

    def _responder_bid_one_is_clubs(self):
        """Return True if responder has bid clubs."""
        if self.responder_bid_one.is_suit_call:
            responder_suit_length_one = self.suit_length(self.responder_bid_one.denomination)
        else:
            responder_suit_length_one = 0
        if self.responder_bid_two.is_suit_call:
            responder_suit_length_two = self.suit_length(self.responder_bid_two.denomination)
        else:
            responder_suit_length_two = 0
        return ((responder_suit_length_one >= 3 or responder_suit_length_two >= 4) and
                self.responder_bid_one.is_suit_call and
                self.responder_bid_two.is_suit_call and
                not (self.bid_one.is_nt and
                self.responder_bid_one.denomination == self.club_suit))

    def _three_card_support_for_responders_second_suit(self):
        """Return True if support for responder's major."""
        return (self.bid_one.name == '1NT' and
                self.responder_bid_two.denomination.is_major and
                self.suit_length(self.responder_bid_two.denomination) >= 3)

    def _three_suits_bid(self):
        """Return True if 3 suits bid."""
        return (self.three_suits_bid_and_stopper() and
                self.responder_bid_one.name != '1NT' and
                self.overcaller_bid_two.name != '2NT' and
                self.nt_level <= 3)

    def _can_rebid_long_suit_at_level_three(self):
        """Return True if can bid long suit at 3 level."""
        return (self.suit_length(self.longest_suit) >= 5 and
                self.suit_points(self.longest_suit) >= 8 and
                self.responder_bid_one.is_value_call and
                self.longest_suit not in self.opponents_suits and
                self.next_level_bid(self.longest_suit).level <= 3 and
                # self.hcp >= 16 and
                self.longest_suit.is_major)

    def _three_suits_bid_contested_auction(self, preference_suit):
        """Return True if 3 suits bid and contested auction."""
        return (self.responder_bid_one.denomination != self.responder_bid_two.denomination and
                self.responder_bid_two.denomination != self.bid_one.denomination and
                self.responder_bid_two.level >= 3 and
                self.responder_bid_one.is_suit_call and
                self.responder_bid_two.is_suit_call and
                self.next_level(preference_suit) <= preference_suit.game_level)

    def _four_card_support_for_responder_and_passed(self):
        """Return True four card support for responder."""
        return (self.responder_bid_one.is_suit_call and
                self.bid_history[1] != 'P' and
                self.opener_bid_two.is_pass and
                self.suit_length(self.responder_bid_one.denomination) >= 4 and
                self.next_level(self.responder_bid_one.denomination) <= 3)

    def _responder_has_jumped_in_minor(self):
        """Return True responder has bid in a minor."""
        return (self.is_semi_balanced and
                self.hcp >= 15 and
                self.responder_bid_two.denomination.is_minor and
                self.is_jump(self.responder_bid_one, self.responder_bid_two) and
                self.stoppers_in_unbid_suits() and
                not self.overcall_made and
                self.nt_level <= 3)

    def _weak_and_two_suited(self):
        """Return True if weak and two suited."""
        return (self.opener_two_suited and
                self.hcp <= 15 and
                self.responder_bid_one.level == 1)

    def _can_bid_again(self):
        """Return True can bid again."""
        return ((self.hcp >= 14 and
                not self.responder_bid_one.is_pass) or
                (self.hcp >= 15 and
                self.responder_bid_one.level >= 2) or
                (self.hcp >= 17 and
                self.responder_bid_two.level >= 2) or
                self.hcp >= 18)

    def _better_than_minimum_six_card_major(self):
        """Return True if six card major."""
        return (self.shape[0] >= 6 and
                self.hcp >= 13 and
                self.longest_suit.is_major and
                self.next_level(self.longest_suit) <= 4)

    def _responder_rebids_minor_and_semi_balanced(self):
        """Return True if responder changes to a minor."""
        return (self.responder_bid_two.denomination.is_minor and
                self.responder_bid_two.denomination != self.responder_bid_one.denomination and
                self.next_level_bid(self.responder_bid_two.denomination).level == 4 and
                self.is_semi_balanced and
                self.shape[3] > 1 and
                self.stoppers_in_bid_suits and
                self.stoppers_in_unbid_suits() and
                self.nt_level <= 3)

    def _has_doubled_after_responder_passed(self):
        """Return True if double after responder has passed."""
        return (self.hcp <= 20 and
                self.responder_bid_one.is_pass and
                self.bid_two.is_double)

    def _strong_or_responder_bids_minor_at_level_four(self):
        """Return True if strong and responder bids minor at level 4."""
        return ((self.responder_bid_two.level == 4 and
                self.responder_bid_two.denomination.is_minor and
                self.shape[0] >= 6) or
                (self.hcp >= 17 and
                self.responder_bid_two.denomination.is_major and
                (self.five_five or
                 not self.responder_weak_bid())))

    def _has_five_card_major(self):
        """Return True if better than minimum and 5 card major."""
        return (self.hcp >= 14 and
                self.bid_one.denomination.is_major and
                self.shape[0] >= 5 and
                self.next_level(self.bid_one.denomination) <= 4)

    def _responder_bids_three_nt_after_stayman_two_four_card_majors(self):
        """Return True if responder bids 3nt after stayman."""
        return (self.bid_after_stayman and
                self.responder_bid_two.name == '3NT' and
                self.spades >= 4 and
                self.hearts >= 4)

    def _better_than_minimum_and_five_card_suit(self):
        """Return True if better than minimum and five card suit."""
        return (self.hcp >= 13 and
                self.shape[0] == 5 and
                self.nt_level <= 3 and
                self.partner_bid_one.name != '1NT')

    def _minimum_after_stayman(self):
        """Return True if minimum after stayman."""
        return (self.bid_one.name == '1NT' and
                self.responder_bid_one.name == '2C' and
                self.hcp <= 13 and
                self.nt_level <= 3)

    def _maximum_after_stayman(self):
        """Return True if maximum after stayman."""
        return (self.bid_one.name == '1NT' and
                self.responder_bid_one.name == '2C' and
                self.hcp >= 14 and
                self.nt_level <= 3)

    def _has_two_four_card_majors_after_hearts(self):
        """Return True if two four card majors after hearts."""
        return (self.spades >= 4 and
                self.hearts >= 4 and
                self.previous_bid.denomination == self.heart_suit and
                self.spade_suit not in self.opponents_suits)

    def _has_two_four_card_majors_after_spades(self):
        """Return True if two four card majors after spades."""
        return (self.spades >= 4 and
                self.hearts >= 4 and
                self.previous_bid.denomination == self.spade_suit and
                self.heart_suit not in self.opponents_suits)

    def _responder_has_jumped_in_major(self):
        """Return True if Responder has jumped in a major."""
        return (self.responder_bid_one.denomination == self.responder_bid_two.denomination and
                self.responder_bid_one.is_suit_call and
                self.is_jump(self.responder_bid_one, self.responder_bid_two) and
                self.responder_bid_one.denomination.is_major and
                self.suit_length(self.responder_bid_one.denomination) >= 2)

    def _is_unbalanced_and_has_two_card_support_for_responders_major(self):
        """Return True if two card support for responders major."""
        return (self.responder_bid_one.denomination.is_major and
                self.suit_length(self.responder_bid_one.denomination) >= 2 and
                self.hcp >= 13 and
                not self.is_balanced and
                (self.responder_bid_one.level == 2 or
                 self.hcp >= 16))

    def _responders_suit_is_minor_and_semi_balanced(self):
        """Return True if responders suit is minor and semi-balanced."""
        return (self.responder_bid_one.denomination.is_minor and
                self.is_semi_balanced and
                self.nt_level <= 3)

    def _strong_with_stoppers(self):
        """Return True if strong hand and stoppers."""
        return (self.hcp >= 18 and
                self.stoppers_in_unbid_suits() and
                self.nt_level <= 3)

    def _responder_repeats_suit_after_two_nt(self):
        """Return True if responder repeats suit after 2nt."""
        return (self.bid_two.name == '2NT' and
                self.responder_bid_one.denomination == self.responder_bid_two.denomination and
                self.stoppers_in_unbid_suits() and
                self.nt_level <= 3)

    def _partner_bid_minor_at_level_four_two_card_support(self):
        """Return True if responder at level 4 in a minor and 2 card support."""
        return (self.responder_bid_one.denomination.is_minor and
                self.responder_bid_two.level == 4 and
                self.suit_length(self.responder_bid_one.denomination) >= 2)

    def _strong_and_responder_supports_four_card_major(self):
        """Return True if responder supports 4 card major."""
        return (self.hcp >= 17 and
                self.bid_one.denomination.is_major and
                self.suit_length(self.bid_one.denomination) == 4 and
                self.responder_bid_two.denomination == self.bid_one.denomination)

    def _two_four_card_majors_after_stayman(self):
        """Return True if two four card majors."""
        return (self.bid_two.is_major and
                self.hearts >= 4 and
                self.spades >= 4)

    def _can_support_responders_four_card_major(self):
        """Return True if can support responders 4 card major."""
        return (self.opener_bid_one.level == 1 and
                self.suit_length(self.responder_bid_two.denomination) >= 4 and
                self.responder_bid_two.denomination.is_major)

    def _responder_changes_suit_at_level_three(self):
        """Return True if responder_changes_suit_at_level_three."""
        return (self.responder_bid_one.denomination != self.responder_bid_two.denomination and
                self.responder_bid_two.level >= 3)

    def _can_bid_strong_major_at_level_three(self):
        """Return True if strong major."""
        return (self.suit_points(self.longest_suit) >= 5 and
                self.next_level(self.longest_suit) <= 3 and
                self.longest_suit.is_major)

    def _responder_has_jumped_in_second_suit(self):
        """Return True if responder jumps in second suit."""
        return (self.responder_bid_two.denomination == self.opener_suit_two and
                self.responder_bid_two.level == self.opener_bid_two.level+2 and
                self.opener_suit_two.is_major and
                self.next_level(self.opener_suit_two) <= 4)

    def _responder_has_jumped_in_openers_major(self):
        """Return True if responder jumps in openers_major."""
        return (self.responder_bid_two.denomination == self.opener_suit_one and
                self.responder_bid_two.level == self.opener_bid_two.level+2 and
                self.opener_suit_one.is_major and
                self.next_level(self.opener_suit_two) <= 4)

    def _responder_has_jumped_in_openers_minor(self):
        """Return True if responder jumps in minor."""
        return (self.responder_bid_two.denomination == self.opener_suit_one and
                self.responder_bid_two.level >= self.opener_bid_two.level+2 and
                not self.opener_bid_two.is_nt and
                not self.opener_bid_two.is_double and
                self.next_level(self.opener_suit_two) <= 5)

    def _intermediate_with_six_four(self):
        """Return True if responder has replied 1NT and 15 points and 6/4."""
        return (self.responder_bid_one.name == '1NT' and
                self.six_four and
                self.hcp >= 15 and
                self.next_level(self.opener_suit_one) <= 3 and
                self.opener_suit_one.is_major)

    def _responder_repeats_suit_and_can_support(self):
        """Return True if responder moderate and repeats suit."""
        return (self.opener_suit_two == self.responder_bid_two.denomination and
                self.responder_bid_one.denomination == self.responder_bid_two.denomination and
                self.responder_bid_two.level == 3 and
                self.hcp >= 14)

    def _medium_balanced_responder_repeats_at_level_three(self):
        """Return True if medium, balanced, and opener bid suit at level 3."""
        return (self.is_balanced and
                self.responder_bid_two.level <= 3 and
                self.hcp >= 16 and
                self.nt_level <= 3)

    def _can_call_3nt(self):
        """Return True if can call 3NT."""
        return (self.hcp >= 16 and
                (self.partner_bid_one.name != '1NT' or
                 self.hcp >= 18) and
                self.nt_level <= 3)

    def _can_raise_responders_invitation(self):
        """2 card support for responders 6 card suit and better than opening hand."""
        responders_suit = self.responder_bid_one.denomination
        return (self.suit_length(responders_suit) == 2 and
                self.responder_bid_two.level == 3 and
                responders_suit.is_major and self.hcp >= 14)

    def _respsonder_invites_game_in_minor(self):
        """Return True if responder invites game."""
        return (self.responder_bid_two.denomination == self.opener_suit_one and
                self.responder_bid_two.level == 4 and
                self.opener_bid_one.is_minor and
                self.next_level(self.opener_suit_one) <= 5)

    def _responder_promises_stopper(self):
        """Return True if responder promises stopper."""
        return (self.opener_bid_one.name == '1NT' and
                self.responder_bid_two.name == '2NT' and
                self.last_bid.is_pass and self.hcp == 14 and
                self.nt_level <= 3)

    def _responder_jumps_in_major(self):
        """Return True if responder jumps in major."""
        return (self.hcp >= 13 and
                self.partner_bid_one.is_suit_call and
                self.partner_bid_one.denomination == self.partner_bid_two.denomination and
                self.is_jump(self.partner_bid_one, self.partner_bid_two))

    def _responder_has_invited_in_six_card_suit(self):
        """Return True if partner invites in six card suit."""
        return (self.shape[0] >= 6 and
                self.hcp >= 14 and
                self.is_jump(self.opener_bid_two, self.responder_bid_two) and
                self.responder_bid_two.denomination == self.longest_suit and
                self.next_level(self.longest_suit) <= self.game_level(self.longest_suit))

    def _responder_has_invited_in_second_suit(self):
        """Return True if partner invites in second suit."""
        return (self.hcp >= 14 and
                self.is_jump(self.opener_bid_two, self.responder_bid_two) and
                self.opener_suit_two == self.responder_bid_two.denomination and
                self.next_level(self.second_suit) <= self.game_level(self.second_suit) and
                self.second_suit not in self.opponents_suits)
