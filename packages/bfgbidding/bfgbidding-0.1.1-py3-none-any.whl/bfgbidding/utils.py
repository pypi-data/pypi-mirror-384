"""Utility functions for bidding."""

from bridgeobjects import ROLES
from .bidding import Bid, Pass


NUMBER_OF_PLAYERS = 4


def get_role(bid_history: list[str]) -> int:
    """Return the role_id based on the length of the bid_history."""
    active_bid_history = get_active_bid_history(bid_history)
    if len(active_bid_history) % NUMBER_OF_PLAYERS == 0:
        return ROLES['Opener']

    if len(active_bid_history) % NUMBER_OF_PLAYERS == 2:
        return ROLES['Responder']

    all_passes = True
    for index, bid in enumerate(active_bid_history[1::2]):
        if bid != 'P':
            all_passes = False
            break

    if all_passes:  # Must be overcaller
        return ROLES['Overcaller']

    # Get number of calls after first overcall
    overcall_index = (index * 2) + 2
    remaining_calls = len(active_bid_history) - overcall_index + 1

    if remaining_calls % NUMBER_OF_PLAYERS == 0:
        return ROLES['Overcaller']
    return ROLES['Advancer']


def get_active_bid_history(bid_history) -> list[str]:
    """Return the bid history without leading PASSES."""
    for index, bid in enumerate(bid_history):
        if bid != 'P':
            return bid_history[index:]
    return []


class NamedBids():
    """Specifically named bids."""
    def __init__(self, hand: object, bid_history: list[str]) -> None:
        self.hand = hand
        self.bid_history = bid_history

        self.pass_bid = Pass('9999')
        self.opener_bid_one = self.pass_bid
        self.opener_bid_two = self.pass_bid
        self.opener_bid_three = self.pass_bid
        self.responder_bid_one = self.pass_bid
        self.responder_bid_two = self.pass_bid
        self.responder_bid_three = self.pass_bid
        self.overcaller_bid_one = self.pass_bid
        self.overcaller_bid_two = self.pass_bid
        self.overcallers_last_bid = self.pass_bid
        self.advancer_bid_one = self.pass_bid
        self.advancer_bid_two = self.pass_bid

        self.previous_bid = self.pass_bid
        self.last_bid = self.pass_bid
        self.right_hand_bid = self.pass_bid
        self.my_last_bid = self.pass_bid

        self.partner_bid_one = self.pass_bid
        self.partner_bid_two = self.pass_bid
        self.partner_penultimate_bid = self.pass_bid
        self.partner_last_bid = self.pass_bid

        self.bid_one = self.pass_bid
        self.bid_two = self.pass_bid
        self.bid_three = self.pass_bid

        self.responders_support = False
        self.overcaller_has_jumped = False
        self.bid_after_stayman = False
        self.overcaller_in_second_seat = self._overcaller_in_second_seat()
        self.overcaller_in_fourth_seat = self._overcaller_in_fourth_seat()

        self.assign_bids()

        self.suit_one = None
        if self.bid_one and self.bid_one.is_suit_call:
            self.suit_one = self.bid_one.denomination

        self.overcaller_suit_one = None
        self.advancer_suit_one = None
        self.advancer_suit_two = None
        self.holding_partner_one = 0
        if self.hand:
            if self.overcaller_bid_one.is_suit_call:
                self.overcaller_suit_one =  self.overcaller_bid_one.denomination
            if self.advancer_bid_one.is_suit_call:
                self.advancer_suit_one = self.advancer_bid_one.denomination
                self.holding_partner_one = self.hand.suit_length(self.advancer_suit_one)
            if self.advancer_bid_two.is_suit_call:
                self.advancer_suit_two = self.advancer_bid_two.denomination

    @staticmethod
    def is_jump(first_bid: Bid, second_bid: Bid) -> bool:
        """Return True if second bid is a jump over first."""
        # e.g.  first_bid = Bid('1S')
        #       second_bid = Bid('2NT')
        if second_bid.is_value_call and first_bid.is_value_call:
            jump_level = second_bid.level - first_bid.level
            if jump_level > 1:
                return True
            elif jump_level == 1:
                if second_bid.is_suit_call and first_bid.is_suit_call:
                    if second_bid.denomination > first_bid.denomination:
                        return True
                elif second_bid.is_nt:
                    return True
        return False

    def _bid_after_stayman(self) -> bool:
        """Return True if responder has bid Clubs after NT opening."""
        if (self.hand and self.opener_bid_one.is_nt and
                self.responder_bid_one.denomination == self.hand.club_suit):
            return True
        return False

    def _overcaller_in_second_seat(self) -> bool:
        """Assign seat to overcaller."""
        if (len(self.bid_history) >= 2 and
                Bid(self.bid_history[1]).name != Pass().name):
            return True
        return False

    def _overcaller_in_fourth_seat(self) -> bool:
        """Assign seat to overcaller."""
        if (len(self.bid_history) >= 2 and
                Bid(self.bid_history[1]).is_pass and
                len(self.bid_history) >= 4 and
                not Bid(self.bid_history[3]).is_pass):
            return True
        return False

    def assign_bids(self) -> None:
        """Assign bids to named attributes based on bid_history."""
        if not self.bid_history:
            return

        bids = len(self.bid_history)
        if bids >= 1:
            self.last_bid = Bid(self.bid_history[-1])
            self._assign_first_bid()
            if bids == 1:
                return
        if bids >= 2:
            self._assign_second_bid()
            if bids == 2:
                return
        if bids >= 3:
            self._assign_third_bid()
            if bids == 3:
                return
        if bids >= 4:
            self._assign_fourth_bid()
            if bids == 4:
                return
        if bids >= 5:
            self._assign_fifth_bid()
            if bids == 5:
                return
        if bids >= 6:
            self._assign_sixth_bid()
            if bids == 6:
                return
        if bids >= 7:
            self._assign_seventh_bid()
            if bids == 7:
                return
        if bids >= 8:
            self._assign_eighth_bid()
            if bids == 8:
                return
        if bids >= 9:
            self._assign_ninth_bid()
            if bids == 9:
                return
        if bids >= 10:
            self._assign_tenth_bid()
            if bids == 10:
                return
        if bids >= 11:
            self._assign_eleventh_bid()
            if bids == 11:
                return
        if bids >= 12:
            self._assign_twelfth_bid()
            if bids == 12:
                return

    def _assign_first_bid(self) -> None:
        """Assign first bid."""
        self.opener_bid_one = Bid(self.bid_history[0])

    def _assign_second_bid(self) -> None:
        """Assign second bid."""
        # if self.bid_history[1] == 'P':
        self.overcaller_bid_one = Bid(self.bid_history[1])
        self.overcaller_has_jumped = self.is_jump(self.opener_bid_one,
                                                self.overcaller_bid_one)
        self.right_hand_bid = Bid(self.bid_history[-1])
        self.partner_last_bid = Bid(self.bid_history[-2])

        if self.partner_bid_one == self.pass_bid:
            self.partner_bid_one = Bid(self.bid_history[-2])

        if self.hand and self.partner_bid_one.is_suit_call:
            self.holding_partner_one = self.hand.suit_holding[self.partner_bid_one.denomination]

        if len(self.bid_history) >= 7:
            self.partner_penultimate_bid = Bid(self.bid_history[-6])

    def _assign_third_bid(self) -> None:
        """Assign third bid."""
        self.responder_bid_one = Bid(self.bid_history[2])
        self.responders_support = (self.opener_bid_one.denomination ==
                                   self.responder_bid_one.denomination)

    def _assign_fourth_bid(self) -> None:
        """Assign fourth bid."""
        self.advancer_bid_one = Bid(self.bid_history[3])
        self.bid_one = Bid(self.bid_history[-4])
        self.previous_bid = Bid(self.bid_history[-4])
        if self.overcaller_in_fourth_seat:
            self.overcaller_bid_one = Bid(self.bid_history[3])
            self.overcaller_has_jumped = self.is_jump(self.responder_bid_one,
                                                      self.overcaller_bid_one)
        self.my_last_bid = Bid(self.bid_history[-4])

    def _assign_fifth_bid(self) -> None:
        """Assign fifth bid."""
        self.opener_bid_two = Bid(self.bid_history[4])
        self.bid_after_stayman = self._bid_after_stayman()

    def _assign_sixth_bid(self) -> None:
        """Assign sixth bid."""
        self.partner_bid_one = Bid(self.bid_history[-6])
        self.partner_bid_two = Bid(self.bid_history[-2])
        if self.overcaller_in_fourth_seat:
            self.overcaller_bid_one = Bid(self.bid_history[3])
            self.advancer_bid_one = Bid(self.bid_history[5])

    def _assign_seventh_bid(self) -> None:
        """Assign seventh bid."""
        self.responder_bid_two = Bid(self.bid_history[6])
        self.overcaller_bid_two = Bid(self.bid_history[5])

    def _assign_eighth_bid(self) -> None:
        """Assign eighth bid."""
        self.bid_one = Bid(self.bid_history[-8])
        self.bid_two = Bid(self.bid_history[-4])
        self.overcallers_last_bid = Bid(self.bid_history[-1])
        if self.overcaller_in_fourth_seat:
            self.overcaller_bid_two = Bid(self.bid_history[7])
        else:
            self.advancer_bid_two = Bid(self.bid_history[7])

    def _assign_ninth_bid(self) -> None:
        """Assign ninth bid."""
        self.opener_bid_three = Bid(self.bid_history[8], '')

    def _assign_tenth_bid(self) -> None:
        """Assign tenth bid."""
        self.partner_bid_one = Bid(self.bid_history[-10])
        self.partner_bid_two = Bid(self.bid_history[-6])

    def _assign_eleventh_bid(self) -> None:
        """Assign eleventh bid."""
        self.responder_bid_three = Bid(self.bid_history[10])
        # self.overcaller_bid_two = Bid(self.bid_history[5])

    def _assign_twelfth_bid(self) -> None:
        """Assign twelfth bid."""
        self.bid_one = Bid(self.bid_history[-12])
        self.bid_two = Bid(self.bid_history[-8])
        self.bid_three = Bid(self.bid_history[-4])
