""" Bid for Game
    Acol RespondersLaterBid module
"""
import inspect
from .bidding import Bid, Pass
from .blackwood import Blackwood
from .hand import Hand

inspection = inspect.currentframe

class RespondersLaterBid(Hand):
    """BfG RespondersLaterBid class."""
    def __init__(self, hand_cards, board):
        super(RespondersLaterBid, self).__init__(hand_cards, board)
        self.openers_last_bid = Bid(self.bid_history[-2])
        self.openers_penultimate_bid = Bid(self.bid_history[-6])
        self.openers_first_bid = Bid(self.bid_history[-6])
        if len(self.bid_history) >= 10:
            self.openers_first_bid = Bid(self.bid_history[-10])
        self.trace = 0

    def suggested_bid(self):
        """Direct control to relevant method and return a Bid object."""
        suit = self.openers_last_bid.denomination

        if self.opener_bid_one.name == '2C':
            bid = self._two_club_opening()

        elif self._has_support_for_openers_new_suit_at_level_four():
            bid = self.next_level_bid(self.opener_suit_three, '3809')

        elif (self.opener_bid_one.is_suit_call and
              self.opener_bid_two.name == '2NT' and
              self.opener_bid_three.name == '3NT' and
              self.hcp >= 16
              and self.nt_level <= 4):
            bid = self.nt_bid(4, '3862')

        # Blackwood
        elif self._opener_jumped_and_can_support():
            bid = self.nt_bid(4, '3806')
        elif self.hcp >= 16 and not self.openers_last_bid.is_pass and self.nt_level <= 4:
            bid = self.nt_bid(4, '3810')
        elif self._opener_strong_and_balanced_and_fifteen_points():
            bid = self.nt_bid(6, '3811')

        # NT in auction
        elif self.openers_last_bid.is_nt and 4 <=self.openers_last_bid.level <= 5:
            bid = self._opener_bid_blackwood()
        elif self.previous_bid.is_nt and self.previous_bid.level >= 4:
            bid = self._responder_bid_nt()
        elif (self.opener_bid_one.is_major and self.suit_holding[self.opener_suit_one] >=3 and
                    self.openers_last_bid.name == '3NT'):
            bid = self.next_level_bid(self.opener_suit_one, '3860')
        elif self._opener_bids_three_nt_after_change_of_major():
            bid = self.next_level_bid(self.opener_suit_one, '3802')
        elif self._opener_bids_three_nt_and_hand_has_six_card_major():
            bid = self.suit_bid(4, self.longest_suit, '3803')
        elif self._five_five_majors_after_3nt():
            bid = self.suit_bid(4, self.heart_suit, '3819')
        elif (self.opener_bid_two.is_nt and
                self.openers_last_bid.denomination == self.bid_one.denomination  and
                self.hcp >= 15 and
                self.nt_level <= 4):
            bid = self.nt_bid(4, '3853')
        elif (self.opener_bid_two.is_nt and
                self.openers_last_bid.denomination == self.bid_one.denomination  and
                self.hcp >= 10 and
                self.nt_level <= 4):
            bid = self.bid_to_game(self.bid_one.denomination, '3876')

        # Misc bids
        elif self._opener_rebids_first_suit_two_card_support():
            bid = self.next_level_bid(self.opener_suit_one, '3808')

        elif self._two_card_support_for_openers_six_card_suit_twelve_points():
            bid = self.next_level_bid(self.opener_suit_one, '3812')

        elif self._opener_support_six_card_suit() and not Bid(self.bid_history[-2]).is_game:
            bid = self.next_level_bid(self.longest_suit, '3813')

        elif self._has_support_for_openers_six_card_suit():
            bid = self.next_level_bid(self.opener_suit_one, '3814')

        elif self._opener_repeats_second_suit():
            bid = self._opener_has_rebid_second_suit()

        elif self._opener_has_bid_same_suit_three_times_and_not_at_game():
            bid = self.bid_to_game(self.opener_suit_one, '3820')

        elif (self.openers_last_bid.denomination == self.bid_two.denomination and
                not self.bid_two.is_pass and
                12 <=self.hcp <= 15 and
                self.nt_level <= 3):
            bid = self.suit_bid(4, self.bid_two.denomination, '3844')

        elif self._can_support_openers_second_suit_and_twelve_points():
            bid = self.next_level_bid(suit, '3805')

        elif self._opener_rebids_second_suit_at_three_level():
            bid = self.suit_bid(4, self.bid_two.denomination, '3804')
        elif (self._opener_has_repeated_suit()and
              self.opener_bid_one.is_minor and
              self.opener_bid_three.level == 4 and
              self.suit_holding[self.opener_suit_one] >= 2 and
              self.nt_level <= 5 and
              self.hcp >= 10):
            bid = self.bid_to_game(self.opener_suit_one, '3878')
        elif (self._opener_has_repeated_suit() and
              self.opener_bid_one.is_major and
              self.opener_bid_three.level == 3 and
              self.suit_holding[self.opener_suit_one] >= 2 and
              self.nt_level <= 4 and
              self.hcp >= 11):
            bid = self.bid_to_game(self.opener_suit_one, '3879')
        elif (not self.bid_one.is_pass and
            self.opener_suit_three == self.bid_one.denomination and
              self.hcp >= 13 and
              self.nt_level <= 3):
            bid = self.bid_to_game(self.bid_one.denomination, '3884')

        # 3NT bids
        elif (self._opener_has_repeated_suit() and
              not (self.opener_suit_one.name == 'NT') and
              1 <= self.suit_holding[self.opener_suit_one] <= 2 and
              self.hcp >= 13 and
              self.stoppers_in_unbid_suits() and
              self.nt_level <= 3):
            bid = self.nt_bid(3, '3894')
        elif self._opener_bid_minor_at_level_three_twelve_points():
            bid = self.nt_bid(3, '3807')
        elif self._opener_at_level_three_nine_points_and_stoppers():
            bid = self.nt_bid(3, '3815')
        elif self._support_after_opener_shows_six_four():
            bid = self.next_level_bid(self.opener_suit_one, '3817')
        elif self._opener_has_bid_two_nt_and_five_four():
            bid = self.nt_bid(3, '3818')
        elif self._opener_is_strong_and_has_bid_two_nt():
            bid = self.nt_bid(3, '3821')
        elif (self.opener_bid_three.name == '2NT' and
              self.stoppers_in_unbid_suits() and
              self.hcp >= 12):
            bid = self.nt_bid(3, '3869')
        elif (self.opener_suit_one != self.opener_suit_three and
              self.opener_suit_one.is_suit and
              self.opener_suit_three.is_suit and
              self.suit_holding[self.opener_suit_one] <= 1 and
              self.suit_holding[self.opener_suit_three] <= 2 and
              self.stoppers_in_unbid_suits()):
            bid = self.nt_bid(3, '3881')
        elif (self.opener_suit_one == self.opener_suit_two and
              self.opener_suit_one != self.opener_suit_three and
              not (self.opener_suit_one.name == 'NT' or self.opener_suit_three.name == 'NT') and
              self.suit_holding[self.opener_suit_one] <= 2 and
              self.stoppers_in_unbid_suits() and
              self.hcp >= 14):
            bid = self.nt_bid(3, '3883')
        else:
            bid = self._select_pass_bid()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _select_pass_bid(self):
        """ Bids the culminate in Pass"""
        # Opener bids slam
        if self.openers_last_bid.level >= 6:
            bid = Pass('3841')

        elif self.openers_last_bid.is_game:
            bid = Pass('3816')

        # Oppenents at game
        elif self._opponents_at_game() and self.bid_history[-2] == 'P':
            bid = Pass('3874')
        elif (self._opponents_at_game() and self.hcp <= 10):
             bid = Pass('3887')

        elif (self.opener_suit_one == self.opener_suit_three and
                self.opener_bid_one.level == self.opener_bid_three.level - 1 and
                self.hcp <= 9):
            bid = Pass('3873')

        # Opener has passed
        elif (self.opener_bid_two.is_pass or self.opener_bid_three.is_pass):
            bid = Pass('3875')

        # Opener repeats suit
        elif (self._opener_has_repeated_suit() and
                self.opener_bid_one.is_suit_call and
                self.suit_holding[self.opener_suit_one] <= 1 and
                self.opener_bid_three.level <= 4 and
                self.hcp <= 18):
            bid = Pass('3877')
        elif (self._opener_has_repeated_suit() and
                self.opener_bid_one.is_suit_call and
                self.nt_level == 4 and
                self.hcp <= 10):
            bid = Pass('3888')
        elif (self.opener_suit_one == self.opener_suit_three and
                self.opener_bid_one.is_minor and
                self.opener_bid_three.level == 4 and
                self.hcp <= 10):
            bid = Pass('3889')

        # Opener has id NT on third bid
        elif self.openers_last_bid.name == '2NT' and self.hcp <= 12:
            bid = Pass('3823')

        # Suit preference
        elif (self.opener_bid_one.is_suit_call and self.opener_bid_three.is_suit_call and
              self.opener_bid_two.is_nt and
              (self.suit_holding[self.opener_suit_three] > self.suit_holding[self.opener_suit_one] + 1 or
               self.suit_holding[self.opener_suit_three] >= 4) and
              self.hcp <= 8):
            bid = Pass('3893')

        elif (self.opener_bid_one.is_suit_call and self.opener_bid_three.is_suit_call and
              (self.suit_holding[self.opener_suit_three] > self.suit_holding[self.opener_suit_one] + 1 or
               self.suit_holding[self.opener_suit_three] >= 4) and
              self.hcp <= 10):
            bid = Pass('3886')

        elif (self.openers_last_bid.denomination == self.openers_first_bid.denomination and
              self.nt_level == 3 and
              (self.openers_last_bid.denomination.is_major and self.hcp <= 10 or
               self.openers_last_bid.denomination.is_minor and self.hcp <= 12)):
            bid = Pass('3843')

        elif (self.opener_suit_one == self.opener_suit_three and
              self.suit_holding[self.opener_suit_one] <= 2):
            bid = Pass('3880')

        elif (self.opener_suit_one == self.opener_suit_two and
              self.opener_suit_one != self.opener_suit_three and
              self.next_level(self.opener_suit_one) >=4  and
              self.hcp <= 10):
            bid = Pass('3891')

        elif (self.opener_bid_one.is_suit_call and self.opener_bid_three.is_suit_call and
              not (self.suit_holding[self.opener_suit_three] > self.suit_holding[self.opener_suit_one] + 1 or
               self.suit_holding[self.opener_suit_three] >= 4) and
              self.next_level(self.opener_suit_one) == self.opener_bid_three.level):
            bid = self.next_level_bid(self.opener_suit_one, '3892')

        # Opener has changed suit on second bid
        elif (self.bid_one.denomination != self.bid_two.denomination and
              self.opener_suit_three == self.bid_one.denomination and
              self.hcp <= 12):
            bid = Pass('3871')

        elif (self.opener_suit_one == self.opener_suit_two and
              self.opener_suit_one != self.opener_suit_three and
              self.opener_bid_one.is_suit_call and
              self.suit_holding[self.opener_suit_one] <= 2 and
              self.opener_suit_three.is_suit and
              self.suit_holding[self.opener_suit_three] <= 3 and
              self.hcp <= 10):
            bid = Pass('3882')

        elif (self.five_five_or_better and
              self.next_level(self.second_suit) <= 3 and
              self.second_suit not in self.opponents_suits):
            bid = self.next_level_bid(self.second_suit, '3895')

        # elif (self.opener_suit_three == self.bid_two.denomination and
        #       self.suit_holding[self.bid_two.denomination]<= 4 and
        #       self.hcp <= 8):
        #     bid = Pass('3890')

        # Weak hand
        elif self.hcp < 6:
            bid = Pass('3872')
        elif self.hcp <= 8 and self.bid_history[-4] == 'P' and self.nt_level >= 4:
            bid = Pass('3896')
        elif self.openers_last_bid.denomination == self.responder_bid_one.denomination and self.hcp <= 12:
            bid = Pass('3897')
        elif (self.opener_bid_one.is_suit_call and
              self .opener_bid_three.is_suit_call and
              self.opener_suit_one != self.opener_suit_three and
              self.suit_holding[self.opener_suit_three] > self.suit_holding[self.opener_suit_one] + 1):
            bid = Pass('3898')
        elif (self.shape[0] >=6 and
              self.suit_points(self.longest_suit) >= 4 and
              self.next_level(self.longest_suit) <= 3):
            bid = self.next_level_bid(self.longest_suit, '3899')
        else:
            bid = Pass('3867')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_bid_blackwood(self):
        """Return bid after opener has bid Blackwood."""
        if self.openers_last_bid.name == '4NT':
            bid = Blackwood(self.cards, self.board).ace_count_bid
        elif self.openers_last_bid.name == '5NT':
            bid = Blackwood(self.cards, self.board).king_count_bid
        elif self.openers_last_bid.level >= 6:
            bid = Pass('3848')
        elif self.openers_last_bid.level == 5:
            bid = Pass('3838')
        else:
            bid = Pass('3861')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_bid_nt(self):
        """Return bid after responder has bid NT."""
        if self.previous_bid.name == '4NT':
            bid = self._after_my_4nt()
        elif self.previous_bid.name == '4NT':
            bid = Blackwood(self.cards, self.board).select_contract()
        elif self.previous_bid.name == '5NT':
            bid = Blackwood(self.cards, self.board).select_contract()
        elif self.openers_last_bid.level >= 6:
            bid = Pass('3859')
        else:
            bid = Pass('3825')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def suit_preference(self):
        """Return suit preference."""
        suit_one_holding = self.suit_length(self.opener_suit_one)
        suit_two_holding = self.suit_length(self.opener_suit_two)
        if suit_one_holding >= suit_two_holding:
            suit = self.opener_suit_one
        else:
            suit = self.opener_suit_two
        return suit

    def _after_my_4nt(self):
        """Return bid after partner has responded to my 4NT bid."""
        aces = Blackwood(self.cards, self.board).partnership_aces()
        # agreed_suit = None
        if aces == 4:
            bid = self.nt_bid(5, '3826')
        elif (self.opener_suit_one == self.opener_suit_two and
                self.opener_suit_one != self.responder_bid_one.denomination and
                self.suit_length(self.opener_suit_one) >= 2):
            bid = self.suit_bid(6, self.opener_suit_one, '3827')
        elif (aces == 3 and self.hcp < 19 and
              self.openers_last_bid.denomination == self.opener_suit_one):
            bid = Pass('3847')
        elif self.nt_level == 5:
            agreed_suit = Blackwood(self.cards, self.board).agreed_suit
            if not agreed_suit or agreed_suit.name == '':
                print('Suit failure responderts later bid', self.board.__dict__)
            if aces == 3:
                bid = self.next_level_bid(agreed_suit, '3839')
            elif agreed_suit.name:
                bid = self.next_level_bid(agreed_suit, '3854')
            else:
                bid = Pass('0000')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _two_club_opening(self):
        if self._suit_support_after_two_club_opening_opening():
            bid = self.next_level_bid(self.longest_suit, '3829')
        elif self._opener_changes_suit_after_two_club_opening_opening():
            suit = self.suit_preference()
            if self.suit_length(suit) <= 2 and self.nt_level <= 3:
                bid = self.nt_bid(3, '3830')
            else:
                bid = self.next_level_bid(suit, '3831')
        elif self.opener_bid_three.is_nt and self.opener_bid_three.level >= 4:
            bid = self._opener_bid_blackwood()
        elif self.shape[1] >= 5 and self.next_level(self.second_suit) <= 5:
            bid = self.next_level_bid(self.second_suit, '3832')
        elif self.openers_last_bid.level == 6:
            bid = Pass('3851')
        elif self.openers_last_bid.is_game:
            bid = Pass('3850')
        elif (self.suit_holding[self.openers_last_bid.denomination] >= 2 and
                self.next_level(self.openers_last_bid.denomination) <= 4):
            bid = self.next_level_bid(self.openers_last_bid.denomination, '3856')
        elif self.suit_holding[self.openers_last_bid.denomination] <= 1 and self.nt_level <= 3:
            bid = self.next_nt_bid('3855')
        elif (self.suit_holding[self.openers_last_bid.denomination] <= 3 and
                self.openers_last_bid.is_minor and
                self.hcp <= 3):
            bid = Pass('3857')
        elif (self.suit_holding[self.openers_last_bid.denomination] <= 3 and
                self.openers_last_bid.is_minor and
                self.openers_last_bid.level == 4):
            bid = self.next_level_bid(self.openers_last_bid.denomination, '3858')
        else:
            bid = Pass('3833') # This shouldn't happen!!!
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_has_rebid_second_suit(self):
        """Return bid if opener has rebid second suit."""
        if self.hcp >= 15:
            bid = self.nt_bid(4, '3834')
        elif self._can_support_partner_ditributional_hand():
            bid = self.next_level_bid(self.partner_bid_one.denomination, '3835')
        elif self.opener_bid_three.is_game:
            bid = Pass('3836')
        elif self.shape[0] >= 6 and self.longest_suit.is_major:
            bid = self.next_level_bid(self.longest_suit, '3837')
        elif self.opener_suit_three == self.second_suit:
            bid = self.next_level_bid(self.second_suit, '3865')
        else:
            if (self.shape[0] >= 6 and
                    self.suit_points(self.longest_suit) >= 8 and
                    self.next_level(self.longest_suit) <= 4 and
                    self.longest_suit not in self.opponents_suits):
                suit = self.longest_suit
            elif self.opener_suit_two == self.responder_bid_two.denomination:
                suit = self.opener_suit_two
            elif self.suit_length(self.opener_suit_one) >= 2:
                suit = self.opener_suit_one
            elif self.suit_length(self.opener_suit_two) >= 2:
                suit = self.opener_suit_two
            else:
                suit = self.opener_suit_one
            bid = self.next_level_bid(suit, '3864')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_has_repeated_suit(self):
        """Return True id opener bids the same suit three times."""
        return (self.opener_suit_one == self.opener_suit_two and
                self.opener_suit_one == self.opener_suit_three)

    # Various boolean functions

    def _opener_bids_three_nt_after_change_of_major(self):
        """Return True if opener bids 3NT after change of suit."""
        result = (self.opener_bid_three.name == '3NT' and
                  self.opener_suit_one != self.opener_suit_two and
                  self.opener_bid_one.is_suit_call and
                  self.opener_bid_two.is_suit_call and
                  self.opener_suit_one.is_major and
                  self.suit_length(self.opener_suit_one) >= 3)
        return result

    def _opener_bids_three_nt_and_hand_has_six_card_major(self):
        """Return True if opener bids 3NT and hand has 6 card major."""
        result = (self.opener_bid_three.name == '3NT' and
                  self.shape[0] >= 6 and
                  self.longest_suit.is_major and
                  self.longest_suit not in self.opponents_suits and
                  self.next_level(self.longest_suit) <= 4)
        return result

    def _opener_rebids_second_suit_at_three_level(self):
        """Return True if opener rebids second suit at three level."""
        result = (self.opener_suit_three == self.bid_two.denomination and
                  self.bid_one.denomination != self.bid_two.denomination and
                  self.opener_bid_three.is_suit_call and
                  self.opener_bid_three.level == 3 and
                  self.next_level(self.bid_two.denomination) <= 4 and
                  self.hcp >= 9)
        return result

    def _can_support_openers_second_suit_and_twelve_points(self):
        """Return True if can support openers second suit with opening hand."""
        result = (self.openers_last_bid.level == 3 and
                  (self.openers_last_bid.denomination == self.longest_suit or
                   self.openers_last_bid.denomination == self.second_suit) and
                  self.hcp >= 12)
        return result

    def _opener_jumped_and_can_support(self):
        """Return True if opener jumps and can support."""
        result = (self.is_jump(self.bid_one, self.opener_bid_two) and
                  self.bid_one.denomination == self.opener_suit_three and
                  self.hcp >= 16 and
                  not self.openers_last_bid.is_pass and
                  self.nt_level <= 4)
        return result

    def _opener_bid_minor_at_level_three_twelve_points(self):
        """Return True if opener bids minor at level 3."""
        result = (self.opener_bid_three.level == 3 and
                  self.opener_suit_three.is_minor and
                  self.hcp >= 12 and
                  self.is_balanced and
                  self.nt_level <= 3)
        return result

    def _opener_rebids_first_suit_two_card_support(self):
        """Return True if opener rebids opening suit and two card support."""
        result = (self.opener_suit_one == self.opener_suit_three and
                  self.opener_suit_one != self.opener_suit_two and
                  not self.responder_bid_two.is_nt and
                  self.suit_length(self.opener_suit_one) >= 2 and
                  self.opener_bid_three.level <= 4 and
                  not self.opener_bid_three.is_game and
                  self.hcp >= 8)
        return result

    def _suit_support_after_two_club_opening_opening(self):
        """Return True if after 2C can support."""
        result = (self.opener_bid_one.name == '2C' and
                  self.hcp >= 8 and
                  (self.opener_suit_two == self.longest_suit or
                   self.opener_suit_three == self.longest_suit) and
                  self.shape[0] >= 6)
        return result

    def _opener_changes_suit_after_two_club_opening_opening(self):
        """Return True if opener changes suit after 2C opening."""
        result = (self.opener_bid_one.name == '2C' and
                  self.opener_suit_two != self.opener_suit_three and
                  not self.openers_last_bid.is_game)
        return result

    def _opener_strong_and_balanced_and_fifteen_points(self):
        """Return True if opener is strong and balanced."""
        result = (self.opener_bid_two.name == '2NT' and
                  self.opener_bid_three.name == '3NT' and
                  self.hcp >= 15)
        return result

    def _two_card_support_for_openers_six_card_suit_twelve_points(self):
        """Return True if two card support for opener's six card suit."""
        result = (self.opener_suit_one.is_major and
                  self._opener_has_repeated_suit() and
                  self.suit_length(self.opener_suit_one) >= 2 and
                  self.hcp >= 12 and
                  self.next_level(self.opener_suit_one) <= 4)
        return result

    def _opener_at_level_three_nine_points_and_stoppers(self):
        """Return True if nine points and stoppers."""
        result = (self.openers_last_bid.level == 3 and
                  not self._opener_has_repeated_suit() and
                  self.hcp >= 11 and
                  self.stoppers_in_unbid_suits() and
                  self.nt_level <= 3)
        return result

    def _opener_repeats_second_suit(self):
        """Return True if opener repeats second_suit."""
        result = (self.opener_bid_two.is_suit_call and
                  self.opener_suit_one != self.opener_suit_two and
                  self.opener_suit_two == self.opener_suit_three
                  and self.nt_level <= 4)
        return result

    def _opener_support_six_card_suit(self):
        """Return True if opener support six card suit."""
        result = (self.opener_suit_three == self.longest_suit and
                  self.shape[0] >= 6 and
                  self.hcp >= 8 and
                  self.next_level(self.longest_suit) <= 6)
        return result

    def _has_support_for_openers_new_suit_at_level_four(self):
        """Return True if opener shows new suit at 4 level and support."""
        result = (self.opener_bid_three.level == 4 and
                  self.opener_suit_three != self.opener_suit_one and
                  self.opener_suit_three != self.opener_suit_two and
                  self.suit_length(self.opener_suit_three) >= 3 and
                  not self.opener_bid_three.is_game)
        return result

    def _support_after_opener_shows_six_four(self):
        """Return True if support for opener who shows six four."""
        result = (self.hcp >= 9 and
                  self.opener_suit_one == self.opener_suit_two and
                  self.opener_suit_one != self.opener_suit_three and
                  not self.opener_bid_three.is_nt and
                  # self.responder_bid_two.is_nt and
                  not Bid(self.bid_history[-6]).is_pass and
                  self.suit_length(self.opener_suit_one) >= 2 and
                  not (self.openers_last_bid.denomination == self.opener_suit_one and
                       self.openers_last_bid.is_game))
        return result

    def _opener_has_bid_two_nt_and_five_four(self):
        """Return True if opener hand bid 2NT and hand is 5/4."""
        result = (self.opener_bid_three.name == '2NT' and
                  self.five_four and
                  self.hcp >= 10 and
                  self.nt_level <= 3)
        return result

    def _has_support_for_openers_six_card_suit(self):
        """Return True if opener has 6 card suit and support."""
        result = (self.opener_suit_one == self.opener_suit_three and
                  self.opener_suit_one != self.opener_suit_two and
                  self.suit_length(self.opener_suit_one) >= 2 and
                  self.hcp >= 12 and
                  self.opener_bid_three.level <= 6 and
                  self.next_level(self.opener_suit_one) <= 5 and
                  not self.opener_bid_three.is_game)
        return result

    def _five_five_majors_after_3nt(self):
        """Return True if _five_five_majors_after_3nt."""
        result = (self.openers_last_bid.name == '3NT' and
                  self.spades >= 5 and self.hearts >= 5 and
                  self.next_level(self.heart_suit) <= 4 and
                  self.heart_suit not in self.opponents_suits)
        return result

    def _opener_has_bid_same_suit_three_times_and_not_at_game(self):
        """Return True if opener has bid suit 3 times and not at game."""
        result = (self._opener_has_repeated_suit() and
                  self.suit_length(self.opener_suit_one) >= 3 and
                  not self.bidding_above_game and
                  self.hcp >= 12)
        return result

    def _opener_is_strong_and_has_bid_two_nt(self):
        """Return True if opener is strong and has bid 2NT."""
        result = (self.opener_bid_three.name == '2NT' and
                  self.hcp >= 8 and
                  self.opener_suit_one != self.opener_suit_two)
        return result

    def _can_support_partner_ditributional_hand(self):
        """Return True partner has shown 5/5 hand."""
        result = (self.partner_bid_one.denomination.is_suit and
                    self.partner_bid_one.denomination != self.partner_bid_two.denomination and
                    self.openers_last_bid.denomination == self.partner_bid_two.denomination and
                    self.suit_length(self.partner_bid_one.denomination) > self.suit_length(self.partner_bid_two.denomination))
        return result
