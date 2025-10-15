""" Bid for Game
    Acol Blackwood module
"""

import inspect

from bridgeobjects import Call
from .bidding import Bid, Pass
from .hand import Hand

inspection = inspect.currentframe


class Blackwood(Hand):
    """ Return BfG Blackwood class."""
    HONOURS = {'aces': 1, 'kings': 2}

    def __init__(self, hand_cards, board):
        super(Blackwood, self).__init__(hand_cards, board)

        self.trace = 0

        bw_index = self.bid_history.index('4NT')
        base_index = bw_index % 2
        self.base_index = base_index

        self.partners_last_bid = Bid(self.bid_history[-2], '')
        if len(self.bid_history) >= base_index + 7:
            self.responders_second_bid = Bid(self.bid_history[base_index + 6], '')

        self.openers_first_bid = Bid(self.bid_history[base_index], '')
        self.responders_first_bid = Bid(self.bid_history[base_index + 2], '')
        if len(self.bid_history) >= base_index + 5:
            self.openers_second_bid = Bid(self.bid_history[base_index + 4], '')
        if len(self.bid_history) >= base_index + 9:
            self.my_penultimate_bid = Bid(self.bid_history[-8], '')
            self.opener_bid_three = Bid(self.bid_history[base_index + 8], '')
        if len(self.bid_history) >= base_index + 11:
            self.responders_third_bid = Bid(self.bid_history[base_index + 10], '')
        self.responders_last_bid = Bid(self.bid_history[-2], '')

        self.agreed_suit = self._get_agreed_suit()

        self.ace_count = self.HONOURS['aces']
        self.king_count = self.HONOURS['kings']

        self.ace_count_bid = self.count_aces()
        self.king_count_bid = self.count_kings()
        self.four_aces = self.has_four_aces()
        self.three_aces = self.has_three_aces()

    def _get_agreed_suit(self):
        # Return agreed suit in a slam auction
        calls = [Call(bid) for bid in self.bid_history]
        opener_index = 0
        for opener_call in calls[self.base_index::4]:
            responder_index = 2
            for responder_call in calls[self.base_index+2::4]:
                if responder_call.name == '4NT':
                    if (self.opener_bid_one.is_major and
                            self.suit_holding[self.opener_suit_one] >= 4):
                        self.check_agreed_suit(self.opener_suit_one,
                                               'opener bid one')
                        return self.opener_suit_one

                    check_denomination = Call(self.bid_history[responder_index-2]).denomination
                    self.check_agreed_suit(check_denomination, 'responder_index-2')
                    return Call(self.bid_history[responder_index-2]).denomination

                if opener_call.name == '4NT':
                    check_denomination = Call(self.bid_history[opener_index-2]).denomination
                    self.check_agreed_suit(check_denomination, 'opener index -2')
                    return Call(self.bid_history[opener_index-2]).denomination
                if responder_call.denomination == opener_call.denomination:
                    self.check_agreed_suit(opener_call.denomination, 'opener call')
                    return opener_call.denomination
                responder_index += 4
            opener_index += 4
        check_denomination = Call(self.bid_history[self.base_index]).denomination
        self.check_agreed_suit(check_denomination, 'bid_history[self.base_index])')
        return Call(self.bid_history[self.base_index]).denomination

    def check_agreed_suit(self, agreed_suit, suit_type):
        if not agreed_suit:
            print(f'Suit failure in Blackwood: {suit_type}')
            print(self.pbn_string)

    def count_aces(self):
        """Return bid for Aces in hand."""
        bid = self._count_honours(self.HONOURS['aces'])
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def count_kings(self):
        """Return bid for Kings in hand."""
        bid = self._count_honours(self.HONOURS['kings'])
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _count_honours(self, honour):
        """Return bid based on number of aces or kings in hand."""
        if honour == self.HONOURS['aces']:
            honours = self.aces
            bid_level = 5
            comment = '5000'  # don't change
        else:
            honours = self.kings
            bid_level = 6
            comment = '5001'
        suit_name = [self.club_suit, self.diamond_suit, self.heart_suit,
                     self.spade_suit, self.club_suit][honours]
        level = self.next_level(suit_name)
        if level <= bid_level:
            bid = self.suit_bid(bid_level, suit_name, comment)

            if ((self.partnership_aces == 4 or self.aces == 0 and self.hcp >= 16)
                    and self.kings == 4 and
                    self.partner_last_bid.name != '4NT'):
                bid = self.nt_bid(6, '5002')
        else:
            bid = Pass('5003')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def has_four_aces(self):
        """Return True if partnership has 4 Aces."""
        suit = self.partners_last_bid.denomination
        aces = 0
        if suit.is_suit:
            partners_aces = suit.rank
            if self.aces == 0 and partners_aces == 0:
                partners_aces = 4
            aces = self.aces + partners_aces
        value = aces == 4
        self.tracer(__name__, inspection(), value, self.trace)
        return value

    def has_three_aces(self):
        """Return True if partnership has 3 Aces."""
        suit = self.partners_last_bid.denomination
        aces = 0
        if suit.is_suit:
            partners_aces = suit.rank
            if self.aces == 0 and partners_aces == 0:
                partners_aces = 4
            aces = self.aces + partners_aces
        value = aces >= 3
        self.tracer(__name__, inspection(), value, self.trace)
        return value

    def select_contract(self):
        """Return the selected contract after Blackwood process."""
        suit = self.select_contract_suit()
        aces = self.partnership_aces()
        kings = self.partnership_kings()
        if aces == 4 and kings == 4:
            level = 7
        elif aces == 4 and kings == 3:
            level = 6
        elif self.hcp < 20 and self.queens+self.jacks+self.tens+self.nines <= 4:
            level = 5
        elif aces < 3:
            level = 5
        else:
            level = 6
        partners_last_bid = Bid(self.bid_history[-2])
        if (partners_last_bid.denomination == suit and
                partners_last_bid.level == level):
            bid = Pass('0867')
        elif (suit.is_suit and
                self.next_level(suit) <= level):
            bid = self.suit_bid(level, suit, '5008')
        elif self.nt_level <= level:
            bid = self.nt_bid(level, '5005')
        elif partners_last_bid.level == 6:
            bid = Pass('5009')
        else:
            bid = Pass('5006')
        if bid.name == self.bid_history[-2]:
            bid = Pass('5007')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def partnership_aces(self):
        """Return the number of aces in the partnership."""
        aces = self.aces
        if self.bid_history[-4] == '4NT':
            aces = (Bid(self.bid_history[-2]).denomination.rank + self.aces)
        elif self.bid_history[-8] == '4NT':
            aces = (Bid(self.bid_history[-6]).denomination.rank + self.aces)
        return aces

    def partnership_kings(self):
        """Return the number of kings in the partnership."""
        kings = self.kings
        if self.bid_history[-4] == '5NT':
            kings = (Bid(self.bid_history[-2]).denomination.rank + self.kings)
            if kings == 0:
                kings = 4
        return kings

    def select_contract_suit(self):
        """Return the selected suit after Blackwood process."""
        if (self.openers_first_bid.name == '2C' and
                self.opener_bid_two.name == '4NT' and
                self.suit_length(self.responder_bid_one.denomination) >= 3):
            suit = self.responder_bid_one.denomination
        elif (self.openers_first_bid.name == '2C' and
                self.suit_length(self.opener_suit_two) >= 3):
            suit = self.opener_suit_two
        elif self.responders_first_bid.denomination == self.openers_first_bid.denomination:
            suit = self.openers_first_bid.denomination
        elif self.responders_first_bid.denomination == self.openers_second_bid.denomination:
            suit = self.responders_first_bid.denomination
        elif self.responders_second_bid.denomination == self.openers_second_bid.denomination:
            suit = self.openers_second_bid.denomination
        elif self.responders_second_bid.denomination == self.openers_first_bid.denomination:
            suit = self.openers_first_bid.denomination
        elif self.responders_first_bid.denomination == self.opener_suit_three:
            suit = self.responders_first_bid.denomination
        elif (self.suit_length(self.openers_first_bid.denomination) >= 3 and
                len(self.bid_history) % 4 == 2):
            suit = self.openers_first_bid.denomination
        elif (self.is_jump(self.openers_first_bid, self.responders_first_bid) and
              self.hcp >= 16 and
              self.openers_first_bid.denomination.is_minor and
              self.responders_first_bid.denomination.is_minor):
            suit = self.no_trumps
        elif self.shape[0] >= 7:
            suit = self.longest_suit
        else:
            suit = self.no_trumps
        self.tracer(__name__, inspection(), suit, self.trace)
        return suit
