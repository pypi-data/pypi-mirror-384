""" Bid for Game
    Responder's Rebid class
"""

import inspect
from .bidding import Bid, Pass, HandSuit
from .blackwood import Blackwood
from .hand import Hand
from bridgeobjects import Denomination, SUITS, Suit

inspection = inspect.currentframe


class RespondersRebid(Hand):
    """Responder's Rebid class."""
    def __init__(self, hand_cards, board):
        super(RespondersRebid, self).__init__(hand_cards, board)
        self.overcaller_bid_one = Bid(self.bid_history[1])
        self.overcaller_bid_two = Bid(self.bid_history[5])
        for pos in range(1, 6, 2):
            if self.bid_history[pos] != 'P':
                self.overcaller_bid_one = Bid(self.bid_history[pos])
                if pos <= 2:
                    self.overcaller_bid_two = Bid(self.bid_history[pos+4])
                break
        self.barrier_broken = self.barrier_is_broken(self.opener_bid_one,
                                                     self.opener_bid_two)
        self.trace = 0

    def suggested_bid(self) -> Bid:
        """Direct control to relevant method and return a Bid object."""
        if self._weak_two_opening():
            bid = self._after_weak_opening()
        elif self._has_six_card_suit_and_opener_passed():
            bid = self.next_level_bid(self.longest_suit, '3301')
        elif self.opener_bid_two.is_pass:
            bid = self._opener_has_passed()
        elif self.opener_bid_two.name == '4NT':
            bid = self._response_to_blackwood()
        elif self.bid_one.name == '4NT':
            bid = self._after_responders_blackwood()
        elif self._opener_at_game_but_can_show_preference():
            suit_to_bid = self._suit_preference()
            if suit_to_bid == self.opener_suit_one:
                bid = self.next_level_bid(suit_to_bid, '3302')
            else:
                bid = Pass('3303')
        # elif self._game_has_been_bid_by_opposition():
        #     bid = Pass('3304')
        elif self._has_fifteen_points_and_opener_has_rebid_three_nt():
            level = 6
            if self.hcp >= 19:
                level = 7
            bid = self.nt_bid(level, '3306')
            if self.opener_bid_one.name == '2C':
                bid = self.nt_bid(7, '3305')
        elif self._has_fourteen_with_openers_twenty_three_in_nt():
            bid = self.nt_bid(7, '3307')
        elif self._has_twelve_with_openers_nineteen_in_nt():
            bid = self.nt_bid(6, '3308')
        elif self._has_eighteen_with_openers_nineteen_in_nt():
            bid = self.nt_bid(7, '3580')
        elif self._has_six_card_suit_with_openers_nineteen_in_nt():
            bid = self.next_level_bid(self.longest_suit, '3309')
        elif self.opener_bid_two.name == '3NT' and self.hcp >= 19:
            bid = self.nt_bid(6, '3310')
        elif self.opener_bid_one.name == '2C' and self.hcp >= 9:
            bid = self.nt_bid(4, '3311')
        elif self._thirteen_points_support_and_opener_in_game_in_major():
            bid = self.nt_bid(4, '3312')
        elif (self.opener_bid_one.name == '2NT' and
                self.five_five_or_better):
            suit = self.second_suit
            bid = self.next_level_bid(suit, '3313')
        elif self.opener_bid_two.is_game:
            bid = Pass('3314')
        elif self.opener_bid_one.is_nt:
            bid = self._after_nt_opening()
        else:
            bid = self._after_suit_opening()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_weak_opening(self) -> Bid:
        """Rebid after a weak opening."""
        if self._opener_has_passed_can_compete():
            bid = self._weak_opening_and_competitive_auction()
        elif self._has_sixteen_and_six_card_suit():
            bid = self.next_level_bid(self.longest_suit, '3315')
        # elif self._has_sixteen_and_three_card_support():
        #     bid = self.next_level_bid(self.opener_suit_one, 'xxxx')
        elif (self.hcp >= 15 and self.shape[0] >= 5 and
              self.opener_suit_two == self.longest_suit):
            bid = self.bid_to_game(self.longest_suit, '3317')
        elif self.is_balanced:
            bid = Pass('3318')
        elif self.overcall_made:
            bid = Pass('3584')
        elif (self.hcp <= 15 and
              self.suit_holding[self.opener_suit_one] <= 4 and
              self.suit_holding[self.opener_suit_two] <= 4):
            bid = Pass('3606')
        elif self.bid_one.is_value_call:
            bid = Pass('3316')
        else:
            bid = Pass('3581')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _weak_opening_and_competitive_auction(self) -> Bid:
        """Rebid after a weak opening and competitive auction."""
        if self._has_seventeen_and_three_card_support_can_bid_game():
            bid = self.suit_bid(4, self.opener_suit_one, '3319')
        elif self._can_rebid_openers_suit():
            bid = self.next_level_bid(self.opener_suit_one, '3564')
        elif self.opponents_at_game:
            bid = Pass('3321')
        elif self.nt_level >= 3:
            bid = Pass('3592')
        else:
            bid = Pass('3591')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_nt_opening(self) -> Bid:
        """Rebid after NT opening."""
        if self._opener_has_responded_to_stayman():
            bid = self._after_stayman()
        elif self._opener_has_bid_major_at_three_level_thirteen_points():
            bid = self._strong_after_nt_opening()
        elif self._has_six_card_suit_ten_points_and_opener_support():
            bid = self.bid_to_game(self.bid_one.denomination, '3322')
        elif self._support_for_openers_major_after_nt_opening():
            bid = self.bid_to_game(self.opener_suit_two, '3323')
        elif self.opener_bid_two.is_suit_call:
            bid = Pass('3324')
        else:
            bid = Pass('3583')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _strong_after_nt_opening(self) -> Bid:
        """Return bid after 1NT opening with opening hand."""
        if self.suit_length(self.opener_suit_two) >= 3:
            bid = self.next_level_bid(self.opener_suit_two, '3325')
        elif self.nt_level <= 3:
            bid = self.nt_bid(3, '3326')
        else:
            bid = Pass('3327')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_stayman(self) -> Bid:
        """Return bid after Stayman."""
        if self.opener_bid_one.name == '2NT':
            bid = self._after_stayman_two_nt_opening()
        elif self.opener_bid_two.name == '2NT' and self.overcaller_bid_one.is_suit_call:
            bid = self._after_stayman_two_nt_rebid()
        elif (self.opener_suit_two.is_major and
              self.suit_length(self.opener_suit_two) >= 4):
            bid = self._after_stayman_four_card_major()
        elif self.hcp >= 12 and not self.is_semi_balanced:
            bid = self._after_stayman_other_major()
        else:
            bid = self._after_stayman_no_four_card_major()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_stayman_other_major(self) -> Bid:
        """Return bid after Stayman with distribution."""
        if self._opener_bids_hearts_but_fewer_than_four_hearts():
            bid = self.suit_bid(3, self.spade_suit, '3328')
        else:
            bid = self.nt_bid(3, '3329')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_stayman_four_card_major(self) -> Bid:
        """Return bid after Stayman with 4 card major."""
        if self.opener_bid_one.name == "1NT":
            if self.suit_length(self.opener_suit_two) >= 5:
                bid = self.bid_to_game(self.opener_suit_two, '3330')
            else:
                bid = self._after_stayman_level_two_four_card_major()
        else:
            bid = self._after_stayman_level_three_four_card_major()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_stayman_level_two_four_card_major(self) -> Bid:
        """Return bid after Stayman with 4 card major at two level."""
        if 11 <= self.hand_value_points(self.opener_suit_two) <= 12:
            level = 3
        else:
            level = 4
        if self.opener_bid_two.level == 3:
            level = 4
        bid = self.suit_bid(level, self.opener_suit_two, '3331', True)
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_stayman_level_three_four_card_major(self) -> Bid:
        """Return bid after Stayman with 4 card major at three level."""
        if self.suit_length(self.opener_suit_two) >= 4:
            bid = self.suit_bid(4, self.opener_suit_two, '3332')
        else:
            bid = self.nt_bid(3, '3333')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_stayman_no_four_card_major(self) -> Bid:
        """Return bid after Stayman with no 4 card major."""
        level = 3
        if 11 <= self.hcp <= 12:
            level = 2

        if level >= self.nt_level:
            bid = self.nt_bid(level, '3334')
        else:
            bid = Pass('3335')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_stayman_two_nt_opening(self) -> Bid:
        """Return bid after 2NT opening Stayman."""
        # import pdb; pdb.set_trace()
        suit = self.opener_suit_two
        if self._has_four_cards_in_openers_major_fewer_than_ten_points():
            bid = self.bid_to_game(suit, '3336')
        elif self.hcp >= 12:
            bid = Bid('6NT', '3337')
        elif self.hcp >= 4:
            bid = Bid('3NT', '3338')
        else:
            bid = Pass('3565')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_stayman_two_nt_rebid(self) -> Bid:
        """Return bid after 2NT rebid Stayman."""
        selected_suit = self._get_suit_if_five_five()
        if self.hcp >= 13 and self.stoppers_in_bid_suits and self.nt_level <= 3:
            bid = self.nt_bid(3, '3340')
        elif self._overcall_made_has_five_five(selected_suit):
            bid = self.next_level_bid(selected_suit, '3341')
        elif self.hcp >= 11 and self.is_balanced and self.nt_level <= 3:
            bid = self.nt_bid(3, '3342')
        elif (self.hcp >= 12 and self.shape[1] >= 5 and self.longest_suit.is_major and
              self.second_suit.is_major):
            if self.hearts in self.opponents_suits:
                bid_suit = self.spade_bid
            else:
                bid_suit = self.heart_bid
            bid = bid_suit(4, '3488')
        elif (self.shape[0] >= 6 and self.hcp >= 14):
            bid = self.next_level_bid(self.longest_suit, '3589')
        elif self.hcp >= 13 and self.opener_bid_two.is_nt and self.nt_level <= 3 and self.last_bid.is_pass:
            bid = self.nt_bid(3, '3602')
        elif self.hcp < 13:
            bid = Pass('3345')
        elif self.next_level(self.longest_suit) >= 4:
            bid = Pass('3608')
        else:
            bid = Pass('3572')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _response_to_blackwood(self) -> Bid:
        """Bid after 4NT."""
        bid = Blackwood(self.cards, self.board).count_aces()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_responders_blackwood(self) -> Bid:
        """Select contract after responder initiates Blackwood."""
        aces = self.aces
        opener_bid_two_name = self.opener_bid_two.name
        if (self.suit_length(self.opener_suit_one) >= 4 and
                self.shape[3] <= 2):
            slam_suit = self.opener_suit_one
        elif self.is_balanced:
            slam_suit = self.no_trumps
        else:
            slam_suit = self._suit_preference()
        if opener_bid_two_name == '5C':
            if aces == 0:
                aces = 4
        elif opener_bid_two_name == '5D':
            aces += 1
        elif opener_bid_two_name == '5H':
            aces += 2
        elif opener_bid_two_name == '5S':
            aces += 3
        if self.nt_level >= 6:
            bid = Pass('000')
        elif aces <= 2:
            bid = self.next_level_bid(slam_suit, '3350')
        elif aces == 4:
            bid = self.nt_bid(5, '3346')
        elif aces == 3:
            bid = self.suit_bid(6, slam_suit, '3347')
        # else:
        # if slam_suit == self.no_trumps:
        #     bid = Pass('3348')
            # else:
        elif aces > 4:
            bid = Pass('3349')
        else:
            bid = self.next_level_bid(slam_suit, '3574')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_suit_opening(self) -> Bid:
        """Select process after suit opening."""
        if self.opener_bid_one.name == '2C':
            bid = self._opener_bid_two_clubs()
        elif (self.opener_suit_one == self.opener_suit_two and
                self.opener_bid_two.is_suit_call):
            bid = self._opener_has_repeated_suit()
        elif (self.opener_suit_two == self.bid_one.denomination and
                self.opener_bid_two.is_suit_call):
            bid = self._opener_has_supported_responder()
        else:
            bid = self._after_suit_opening_no_match()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_bid_two_clubs(self) -> Bid:
        """Return bid after opener has bid 2C."""
        if self.opener_bid_two.name == '2NT':
            bid = self._opener_bid_two_nt_after_two_clubs()
        # elif self.hcp <= 9:
        else:
            bid = self._fewer_than_ten_points_after_two_club_opening()
        # else:
        #     bid = self.nt_bid(4, '3351')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_bid_two_nt_after_two_clubs(self) -> Bid:
        """Return bid if opener has bid 2NT after 2C."""
        if self.hcp <= 2:
            bid = Pass('3352')
        elif self.shape[1] >= 5:
            bid = self.next_level_bid(self.second_suit, '3353')
        elif self.shape[0] >= 5:
            bid = self.next_level_bid(self.longest_suit, '3354')
        elif self._four_card_major_or_better():
            bid = self.club_bid(3, '3355')
        elif self.is_semi_balanced and self.nt_level <= 3:
            bid = self.nt_bid(3, '3356')
        elif not (self.is_balanced or self.is_semi_balanced):
            bid = self.next_level_bid(self.longest_suit, '3566')
        else:
            Pass('3590')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _fewer_than_ten_points_after_two_club_opening(self) -> Bid:
        """Return bid if fewer than 10 points after 2C opening."""
        if self.suit_length(self.opener_suit_two) >= 3:
            if self.opener_suit_two.is_major:
                bid = self.bid_to_game(self.opener_suit_two, '3358')
            else:
                bid = self.next_level_bid(self.opener_suit_two, '3359')
        elif self.is_semi_balanced and self.nt_level <= 3:
            bid = self.nt_bid(3, '3360')
        elif (self.longest_suit not in self.opponents_suits and
                (self.next_level(self.longest_suit) <= 3 or
                    self.shape[0] >= 7)):
            bid = self.next_level_bid(self.longest_suit, '3361')
        elif (self.suit_holding[self.opener_suit_two] <= 1 and
              self.shape[2] >= 3 and self.hcp >= 3):
            bid = self.nt_bid(3, '3599')
        elif self.hcp <= 2 and self.suit_holding[self.opener_suit_two] <= 1:
            bid = Pass('3362')
        elif (self.opener_bid_two.is_suit_call and
              self.suit_holding[self.opener_suit_two] <= 2 and
              self.shape[1] <= 4):
            bid = self.next_level_bid(self.longest_suit, '3605')
        elif (self.opener_bid_two.is_suit_call and
              self.suit_holding[self.opener_suit_two] <= 2 and
              self.shape[1] >= 5):
            bid = self.next_level_bid(self.longest_suit, '3603')
        else:
            bid = Pass('3585')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_suit_opening_no_match(self) -> Bid:
        """Bid after suit opening no match opener/responder."""
        if self.bid_one.is_nt:
            if self.opener_bid_two.is_nt:
                bid = self._opener_nt_after_nt_response()
            else:
                bid = self._opener_changed_suit_after_nt()
        else:
            if self.opener_bid_two.is_nt:
                bid = self._opener_nt_after_suit_response()
            elif self._opener_has_has_doubled_and_five_card_suit():
                bid = self.next_level_bid(self.longest_suit, '3363')
            else:
                bid = self._three_suits_bid()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_has_repeated_suit(self) -> Bid:
        """Respond after partner has repeated suit."""
        if self.hcp <= 10 and self._has_bid_two_nt_and_opener_bids_minor():
            bid = Pass('3364')
        elif self.hcp <= 5:
            bid = Pass('3365')
        elif self._responder_jumped_support_fewer_than_twelve_points_fewer_than_five_points():
            bid = Pass('3594')
        elif self._opener_has_jumped_or_level_is_three():
            bid = self._opener_has_jumped_or_bid_at_level_three()
        elif not self.my_last_bid.is_pass:
            bid = self._no_jump_bid()
        elif self.suit_holding[self.opener_suit_one] <= 2 and self.hcp <= 9:
            bid = Pass('3366')
        elif self.suit_holding[self.opener_suit_one] <= 2:
            bid = Pass('3570')
        else:
            bid = Pass('3593')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_has_jumped_or_bid_at_level_three(self) -> Bid:
        """Return a bid if opener has jumped or bid at the three level."""
        if self.opener_suit_one == self.bid_one.denomination:
            if (self.hand_value_points(self.opener_suit_one) >= 8 and
                    not self.overcall_made):
                bid = self.next_level_bid(self.opener_suit_one, '3367', )
            else:
                bid = Pass('3368')
        elif (self.bid_one.level == 2 and
                self.suit_length(self.opener_suit_one) <= 2):
            bid = self._no_jump_bid()
        else:
            bid = self._opener_jumped()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _no_jump_bid(self) -> Bid:
        """Respond after opener has bid with no jump."""
        # if self.opener_bid_one.level > 1:
        #     bid = Pass('3369')
        if self._has_fewer_than_nine_points_and_passed_or_one_nt():
            bid = Pass('3370')
        elif self.suit_length(self.opener_suit_one) >= 3:
            bid = self._no_jump_bid_support_for_opener()
        elif self._has_six_card_suit_and_can_bid():
            bid = self._responder_long_suit()
        elif self._is_weak_and_shortage_in_openers_suit():
            bid = Pass('3371')
        elif self._opener_repeats_major_at_level_three_balanced():
            bid = self.next_nt_bid('3372')
        elif self._opener_bids_major_at_level_three_can_support():
            bid = self.suit_bid(4, self.opener_suit_two, '3373')
        elif self._has_five_four_and_opener_at_three_level():
            bid = self.next_level_bid(self.second_suit, '3374')
        elif self.five_four_or_better:
            bid = self._no_jump_bid_no_support_five_four()
        elif self.stoppers_in_bid_suits:
            bid = self._no_jump_bid_no_support_balanced()
        elif self._intermediate_balanced_cannot_rebid_suit():
            bid = self.nt_bid(3, '3375')
        elif self.longest_suit not in self.opponents_suits and self.shape[0] >= 5 and self.overcall_made:
            bid = self.next_level_bid(self.longest_suit, '3376')
        elif self.opener_suit_one == self.opener_suit_two:
            bid = Pass('3377')
        else:
            bid = self.next_nt_bid('3567')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _no_jump_bid_support_for_opener(self) -> Bid:
        """Bid with no jump and 3+ card support for partner."""
        level = self.opener_bid_two.level
        next_level = self.next_level(self.opener_suit_one)
        level_allowed = next_level <= level + 1

        if self.hcp >= 13:
            nt_level = 3
        else:
            nt_level = 2

        if self.hand_value_points(self.opener_suit_one) <= 9:
            bid = Pass('3379')
        elif self._is_weak_openers_suit_is_minor():
            bid = self.next_nt_bid('3380')
        elif self._intermediate_has_four_card_major_and_opener_in_minor():
            bid = self.next_level_bid(self.second_suit, '3381')
        elif self._strong_has_six_card_major_and_opener_in_minor():
            bid = self.bid_to_game(self.longest_suit, '3382')
        elif self._weak_has_six_card_major_and_opener_in_minor():
            bid = self.next_level_bid(self.longest_suit, '3383', raise_level=1)
        elif self.suit_length(self.partner_bid_one.denomination) >= 5:
            bid = self.bid_to_game(self.partner_bid_one.denomination, '3384')
        elif self._weak_has_stoppers_and_opener_in_minor(nt_level):
            bid = self.nt_bid(nt_level, '3385')
        elif (self.hand_value_points(self.opener_suit_one) <= 12 and
                level_allowed):
            bid = self.suit_bid(level + 1, self.opener_suit_one, '3386')
        else:
            bid = self._no_jump_bid_support_for_opener_strong()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _no_jump_bid_support_for_opener_strong(self) -> Bid:
        """Bid with no jump, string hand and 3+ card support for partner."""
        level = self.opener_bid_two.level
        if level >= 3:
            raise_level = level + 1
        else:
            raise_level = level + 2
        if self._intermediate_has_seven_card_major():
            bid = self.suit_bid(4, self.longest_suit, '3387')
        elif self._opener_in_minor_and_stoppers() and self.hcp >= 12:
            bid = self.nt_bid(3, '3388')
        elif self.next_level(self.opener_suit_one) <= raise_level:
            bid = self.suit_bid(raise_level, self.opener_suit_one, '3389')
        elif self.opponents_at_game:
            bid = Pass('3568')
        else:
            bid = Pass('3589')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _no_jump_bid_no_support_five_four(self) -> Bid:
        """Bid with no support for partner but 5/4 hand."""
        if self.hcp <= 14:
            raise_level = 0
        else:
            raise_level = 1
        if self._five_four_in_majors():
            bid = self.next_level_bid(self.second_suit, '3391', raise_level=raise_level)
        elif self.hcp <= 10:
            bid = Pass('3392')
        elif self._opener_in_minor_distributional_with_stoppers():
            bid = self.nt_bid(3, '3393')
        elif self.second_suit in self.opponents_suits and self.hcp <= 12:
            bid = self.next_nt_bid('3394')
        elif self.second_suit in self.opponents_suits and self.hcp >= 13:
            bid = self.nt_bid(3, '3395')
        elif self.hcp <= 10 and self.next_level(self.second_suit) > 2:
            bid = self.next_nt_bid('3396')
        elif self.second_suit.is_minor and self.next_level(self.second_suit) == 4:
            bid = self.next_nt_bid('3397')
        else:
            bid = self.next_level_bid(self.second_suit, '3398', 0)
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _no_jump_bid_no_support_balanced(self) -> Bid:
        """Bid with no support for partner but balanced hand."""
        if self.hcp <= 9 and self.shape[0] <= 7:
            bid = Pass('3399')
        elif self.shape[0] >= 8 and self.hcp >= 8:
            bid = self.next_level_bid(self.longest_suit, '3400')
        elif self.hcp <= 12 and self.nt_level <= 2:
            bid = self.nt_bid(2, '3401')
        elif self.hcp <= 19 and self.nt_level <= 3:
            bid = self.nt_bid(3, '3402')
        elif self.hcp >= 20 and self.stoppers_in_unbid_suits() and self.nt_level <= 4:
            bid = self.nt_bid(4, '3403')
        elif self.opponents_at_game:
            bid = Pass('3404')
        elif (self.opener_suit_one == self.opener_suit_two and
              self.opener_suit_one.is_minor and self.hcp <= 10):
            bid = Pass('3604')
        elif self.hcp >= 18:
            bid = self.nt_bid(3, '3607')
        else:
            bid = Pass('3586')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_has_supported_responder(self) -> Bid:
        """Bid after opener has supported responder's suit."""
        if self.is_jump(self.bid_one, self.opener_bid_two):
            bid = self._opener_has_supported_responder_jump()
        else:
            bid = self._opener_has_supported_responder_no_jump()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_has_supported_responder_no_jump(self) -> Bid:
        """Bid after opener has supported suit."""
        suit_to_bid = self.bid_one.denomination
        if (self.bid_one.denomination.is_minor and
                self.suit_length(self.opener_suit_one) >= 3):
            suit_to_bid = self.opener_suit_one
        level = self.next_level(suit_to_bid)

        if self.hcp >= 20:
            bid = self.nt_bid(4, '3405')
        elif suit_to_bid.is_minor and self._can_bid_four_card_major():
            suit_to_bid = self.second_suit
            bid = self.next_level_bid(suit_to_bid, '3406')
        elif self.hcp >= 19:
            bid = self.suit_bid(6, suit_to_bid, '3407')
        elif (self.hcp >= 16 and
                self.suit_length(self.opener_suit_one) >= 4 and
                self.nt_level <= 4):
            bid = self.nt_bid(4, '3408')
        elif self.hcp >= 18:
            bid = self.bid_to_game(suit_to_bid, '3409')
        elif (level <= 4 and self.hcp >= 13):
            bid = self.bid_to_game(suit_to_bid, '3410')
        elif (self.hcp + self.distribution_points >= 13 and level <= 4 and
                self.hcp >= 11):
            bid = self.suit_bid(4, suit_to_bid, '3411')
        elif self.hcp >= 9 and level <= 3:
            bid = self.suit_bid(3, suit_to_bid, '3412')
        elif self._opener_has_jumped_no_support():
            bid = self.bid_to_game(self.bid_one.denomination, '3413')
        else:
            bid = Pass('3414')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_has_supported_responder_jump(self) -> Bid:
        """Bid after opener has supported suit and jumped."""
        if self.longest_suit.is_minor and self._can_support_openers_major():
            bid = self.next_level_bid(self.opener_suit_one, '3415')
        elif (self.hcp >= 9 or
                (self.hcp >= 8 and self.suit_length(self.bid_one.denomination) >= 5)):
            bid = self.next_level_bid(self.bid_one.denomination, '3416')
        else:
            bid = Pass('3417')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_long_suit(self) -> Bid:
        """Bid with own long suit."""
        own_suit = self.longest_suit
        if self.hcp <= 9 and own_suit not in self.opponents_suits:
            bid = self.next_level_bid(own_suit, '3418', 0)
        elif self.hcp <= 12:
            bid = self._responder_long_suit_weak()
        else:
            bid = self._responder_long_suit_strong()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_long_suit_strong(self) -> Bid:
        """Bid with own long suit in strong hand."""
        if self.longest_suit in self.opponents_suits:
            bid = Pass('3419')
        elif self._own_suit_is_minor_stoppers_in_other_suits_level_three():
            bid = self.nt_bid(3, '3420')
        elif self._opponents_bid_own_suit_stoppers():
            bid = self.nt_bid(3, '3421')
        elif self._is_strong_can_show_second_suit():
            bid = self.next_level_bid(self.second_suit, '3422')
        elif self.hcp >= 20 and self.shape[0] >= 7:
            bid = self.nt_bid(4, '3423')
        elif self._has_thirteen_points_competitive():
            if self.next_level(self.longest_suit) <= 2:
                level = 2
            else:
                level = 1
            bid = self.next_level_bid(self.longest_suit, '3424', level)
        elif (self.hcp >= 13 and self.shape[0] >= 6 and
                self.longest_suit.is_major and
                self.next_level(self.longest_suit) <= 3):
            bid = self.suit_bid(3, self.longest_suit, '3425')
        elif self.hcp >= 13 and self.shape[1] >= 4 and self.second_suit not in self.opponents_suits:
            bid = self.next_level_bid(self.second_suit, '3426')
        else:
            bid = Pass('3427')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_long_suit_weak(self) -> Bid:
        """Bid with own long suit in weak hand."""
        own_suit = self.longest_suit
        if self._own_suit_is_minor_stoppers_in_other_suits_level_two():
            bid = self.nt_bid(2, '3428')
        elif self._opener_has_shown_six_card_suit():
            bid = self.next_level_bid(self.opener_suit_one, '3429')
        elif own_suit not in self.opponents_suits:
            raise_level = 1
            if (self.overcall_made or
                    (self.hcp <= 12 and self.next_level(own_suit) >= 3)):
                raise_level = 0
            bid = self.next_level_bid(own_suit, '3430', raise_level)
        elif own_suit in self.opponents_suits:
            bid = Pass('3431')
        else:
            bid = Pass('3582')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_jumped(self) -> Bid:
        """Bid after opener has jumped."""
        if self.hcp >= 20 and self.suit_length(self.opener_suit_one) >= 2:
            bid = self.nt_bid(4, '3432')
        elif self._is_strong_unbalanced_and_two_card_support_for_opener():
            bid = self.next_level_bid(self.opener_suit_one, '3433')
        elif self.five_five and self.overcaller_bid_two.is_pass:
            bid = self._opener_jumped_five_five()
        elif self.shape[0] == 6:
            bid = self._opener_jumped_six_card_suit()
        elif self.suit_length(self.opener_suit_one) >= 2:
            bid = self._opener_jumped_two_card_support()
        else:
            bid = self._opener_jumped_no_support()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_jumped_five_five(self) -> Bid:
        """Bid after opener has jumped with 5/5 hand."""
        if (self.second_suit in self.opponents_suits or
                self.bid_one.is_pass):
            bid = Pass('3434')
        else:
            suit = self._get_suit_with_five_five_after_opener_jumped()
            bid = self.next_level_bid(suit, '3435')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_jumped_six_card_suit(self) -> Bid:
        """Bid after opener has jumped with 6 card suit."""
        if self.longest_suit.is_minor and self.nt_level <= 3:
            bid = self.nt_bid(3, '3436')
        elif self.longest_suit not in self.opponents_suits:
            bid = self.next_level_bid(self.longest_suit, '3437')
        elif self.longest_suit in self.opponents_suits:
            bid = Pass('3438')
        else:
            bid = Pass('3587')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_jumped_two_card_support(self) -> Bid:
        """Bid after opener has jumped with 2+ card support."""
        if self.hand_value_points(self.opener_suit_one) <= 7:
            bid = Pass('3439')
        elif self._balanced_and_opener_bid_minor():
            bid = self.nt_bid(3, '3440')
        elif self._opener_has_jumped_and_can_support_non_competitive():
            bid = self.bid_to_game(self.opener_suit_one, '3441', True)
        elif self.support_points(self.opener_suit_one) >= 15:
            bid = self.bid_to_game(self.opener_suit_one, '3442', True)
        elif self._opener_has_jumped_and_can_support_competitive():
            bid = self.next_level_bid(self.opener_suit_one, '3443')
        elif self._can_suppport_openers_major():
            bid = self.bid_to_game(self.opener_suit_one, '3444', True)
        elif self._can_bid_second_suit_at_level_three():
            bid = self.next_level_bid(self.second_suit, '3445')
        elif self.hcp <= 10:
            bid = Pass('3446')
        else:
            bid = Pass('3569')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_jumped_no_support(self) -> Bid:
        """Bid after opener has jumped with no support."""
        if self.hcp <= 7 or self.bid_one.is_nt:
            bid = Pass('3447')
        else:
            bid = self._opener_jumped_no_support_intermediate_strong()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_jumped_no_support_intermediate_strong(self) -> Bid:
        """Bid after opener has jumped with no support good hand."""
        if self.shape[0] >= 7 and self.longest_suit not in self.opponents_suits:
            bid = self.bid_to_game(self.longest_suit, '3448')
        elif self.hcp >= 16 and self.shape[0] >= 5:
            bid = self.next_level_bid(self.bid_one.denomination, '3449')
        elif self._has_thirteen_points_and_opener_has_jumped():
            bid = self.nt_bid(4, '3450')
        elif self._has_twelve_points_and_opener_has_jumped():
            bid = self.nt_bid(3, '3451')
        elif self.hcp <= 9 and self.suit_holding[self.opener_suit_one] <= 1:
            bid = Pass('3452')
        elif (self.opener_bid_two.is_minor and
              self.suit_holding[self.opener_suit_two] <= 1 and
              self.hcp <=14):
            bid = Pass('3598')
        elif self.suit_holding[self.opener_suit_one] <= 1:
            bid = Pass('3601')
        else:
            bid = Pass('3575')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_changed_suit_after_nt(self) -> Bid:
        """Return bid after opener has changed suit after responder NT."""
        suit_to_bid = self._select_suit()
        barrier_is_broken = self.barrier_is_broken(self.opener_bid_one,
                                                   self.opener_bid_two)
        if self._weak_but_barrier_broken(suit_to_bid):
            if (self.hcp+self.distribution_points >= 9 and
                    self.suit_length(self.opener_suit_one) >= 3):
                raise_level = 1
            else:
                raise_level = 0
            bid = self.next_level_bid(suit_to_bid, '3453', raise_level=raise_level)
        elif barrier_is_broken and self.hcp >= 9:
            bid = self._opener_changed_suit_after_nt_intermediate()
        elif not self.overcall_made:
            if self.shape[0] >= 6:
                bid = self.next_level_bid(self.longest_suit, '3454')
            elif self.hcp >= 6 and self.next_level(suit_to_bid) <= 2:
                bid = self.next_level_bid(suit_to_bid, '3455')
            else:
                bid = Pass('3456')
        elif self._both_openers_suits_are_minors():
            bid = self.nt_bid(3, '3457')
        else:
            bid = self._opener_changed_suit_after_nt_overcall_major()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_changed_suit_after_nt_intermediate(self) -> Bid:
        """Return bid after opener has reversed after responder NT, 9+ points."""
        suit_to_bid = self._select_suit()
        if suit_to_bid in self.opponents_suits:
            suit_to_bid = self.opener_suit_one
        if self._no_support_own_suit_is_minor_with_stops():
            bid = self.nt_bid(3, '3458')
        elif suit_to_bid.is_no_trumps:
            bid = self.nt_bid(3, '3459')
        elif self._is_balanced_own_suit_is_minor_with_stops():
            bid = self.next_nt_bid('3460')
        elif self.next_level(suit_to_bid) <= 4:
            level = 4
            if suit_to_bid.is_minor and self.hcp >= 11:
                level = 5
            bid = self.suit_bid(level, suit_to_bid, '3461')
        elif self.opponents_at_game:
            bid = Pass('3462')
        elif (self.opener_suit_one != self.opener_suit_two and
              self.opener_bid_two.is_minor and
              self.opener_bid_two.level == 4 and
              self.suit_holding[self.opener_suit_two] >= 3
              and self.hcp >= 9):
            bid = self.bid_to_game(self.opener_suit_two, '3600')
        else:
            bid = Pass('3588')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_changed_suit_after_nt_overcall_major(self) -> Bid:
        """Return bid after opener two suits  one major and overcall."""
        trial_bid = self._opener_changed_suit_after_nt_overcall_major_trial()
        level = trial_bid.level
        own_suit = self.longest_suit
        borrowed_bid = own_suit in self.opponents_suits
        if level < 3 or self.hcp >= 10 or self.suit_length(trial_bid.denomination) >= 5:
            bid = trial_bid
        elif borrowed_bid and self.hcp >= 9:
            bid = trial_bid
        else:
            bid = Pass('3463')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_changed_suit_after_nt_overcall_major_trial(self) -> Bid:
        """Return bid after opener two suits one major and overcall."""
        suit_to_bid = self._suit_for_trial_after_opener_changes_suit()
        if self.hcp >= 12 and suit_to_bid.is_major:
            jump = 1
        else:
            jump = 0
        bid = self.next_level_bid(suit_to_bid, '3464', jump)
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_nt_after_nt_response(self) -> Bid:
        """Return bid if opener has bid NT after a NT response."""
        if self.opener_bid_two.name == '3NT':
            bid = Pass('3465')
        elif self.hcp >= 8:
            bid = self.nt_bid(3, '3466')
        elif (self.shape[0] >= 6 and
                self.longest_suit not in self.opponents_suits):
            bid = self.next_level_bid(self.longest_suit, '3467')
        else:
            bid = Pass('3468')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _three_suits_bid(self) -> Bid:
        """Return bid after opener shows third suit."""
        suit_to_bid = self._select_suit()
        barrier_is_broken = self.barrier_is_broken(self.opener_bid_one,
                                                   self.opener_bid_two)
        suit_support_points = self._suit_support_points(suit_to_bid)
        fourth_suit = self._fourth_suit()

        if barrier_is_broken and self.hcp <= 15:
            bid = self._opener_broken_barrier_weak()
        elif (self._has_fourteen_points_and_suit_is_minor(suit_to_bid) and
              self.suit_stopper(fourth_suit)):
            bid = self.nt_bid(3, '3469')
        elif self._has__strong_seven_card_suit_and_fourteen_points():
            bid = self.bid_to_game(self.longest_suit, '3470')
        elif self._has_ten_points_and_can_support_opener(suit_to_bid,
                                                         suit_support_points):
            bid = self._three_suits_bid_support_opener()
        elif suit_to_bid.is_no_trumps:
            bid = self._three_suits_and_nt_selected()
        elif self._has_eleven_points_and_three_suits_bid():
            level = 2
            if self.hcp >= 13:
                level = 3
            bid = self.nt_bid(level, '3471')
        elif (self.hcp >= 10 and
              suit_to_bid not in self.opponents_suits):
            bid = self._three_suits_bid_medium_hand()
        else:
            bid = self._three_suits_bid_weak()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _three_suits_bid_support_opener(self) -> Bid:
        """Return bid after opener shows third suit and hand supports opener."""
        suit_to_bid = self._select_suit()
        if suit_to_bid.is_minor:
            unbid_suit = self._unbid_suit()
        else:
            unbid_suit = None
        suit_support_points = self._suit_support_points(suit_to_bid)
        if self._can_support_minor_but_is_semi_balanced(suit_to_bid, suit_support_points):
            bid = self.nt_bid(2, '3472')
        elif self.hcp >= 16 and self.nt_level <= 3 and self.stoppers_in_unbid_suits():
            bid = self.nt_bid(3, '3473')
        elif self.hcp >= 16 and self.barrier_broken and self.five_four_or_better:
            bid = self.next_level_bid(self.second_suit, '3474')
        elif self._has_six_card_suit_and_opening_points():
            bid = self.suit_bid(3, self.longest_suit, '3475')
        elif 10 <= self.hcp <= 13 and not self.is_semi_balanced and suit_to_bid.is_minor:
            bid = self.suit_bid(4, suit_to_bid, '3476', True)
        elif (unbid_suit and self.hcp >= 12 and
              (self.suit_length(unbid_suit) + self.suit_points(unbid_suit)) >= 4):
            bid = self.nt_bid(3, '3477')
        elif suit_support_points >= 13 and self.next_level(suit_to_bid) <= suit_to_bid.game_level:
            bid = self.bid_to_game(suit_to_bid, '3478', True)
        elif self._is_balanced_intermediate_stoppers(suit_to_bid):
            bid = self.nt_bid(2, '3479')
        elif self.suit_length(suit_to_bid) >= 4 and self.hcp >= 10:
            bid = self.next_level_bid(suit_to_bid, '3480', 1)
        elif self._is_balanced_support_for_openers_second_suit(suit_to_bid):
            bid = self.nt_bid(2, '3481')
        elif self._suit_to_support_is_minor_and_stoppers(suit_to_bid):
            if self.hcp <= 9:
                level = 1
            elif self.hcp <= 13:
                level = 2
            else:
                level = 3
            bid = self.nt_bid(level, '3482')
        elif suit_support_points >= 11:
            bid = self.next_level_bid(suit_to_bid, '3483', raise_level=1)
        elif self._has_three_card_support_for_openers_major():
            bid = self.next_level_bid(self.opener_suit_one, '3484')
        elif self.hcp == 10 and self.is_balanced and self.nt_level <= 2:
            bid = self.nt_bid(2, '3485')
        elif self.hcp == 10:
            bid = self.next_level_bid(suit_to_bid, '3486')
        elif suit_support_points >= 10:
            if self.six_four:
                raise_level = 1
            else:
                raise_level = 0
            bid = self.next_level_bid(suit_to_bid, '3487', raise_level=raise_level)
        else:
            assert False, 'bid not assigned'
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _three_suits_bid_medium_hand(self) -> Bid:
        """Return bid after opener shows third suit, medium hand."""
        suit_to_bid = self._select_suit()
        if (self.hcp >= 16 and
                self.shape[0] >= 7 and
                self.nt_level <= 4):
            bid = self.nt_bid(4, '3488')
        level = self.next_level_bid(suit_to_bid).level
        if self._is_strong_has_stoppers():
            bid = self.nt_bid(4, '3489')
        elif (self.shape[0] >= 7 and
                self.longest_suit.is_major and
                self.opener_bid_two.level >= 2 and
                self.next_level(suit_to_bid) <= 4):
            bid = self.suit_bid(4, suit_to_bid, '3490')
        elif (self._is_distributional_and_barrier_not_broken(suit_to_bid) and
                self.shape[0] >= 8):
            bid = self.bid_to_game(self.longest_suit, '3491')
        elif self._is_distributional_and_barrier_not_broken(suit_to_bid):
            level += 1
            bid = self.suit_bid(level, suit_to_bid, '3492')
        else:
            bid = self.suit_bid(level, suit_to_bid, '3493', True)
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _three_suits_bid_weak(self) -> Bid:
        """Return bid after opener shows third suit, weak hand."""
        suit_to_bid = self._select_suit()
        if self.shape[0] >= 7:
            suit_to_bid = self.longest_suit
        elif self.shape[0] >= 6 and self.hcp == 5:
            suit_to_bid = self.longest_suit
        if self._has_biddable_five_card_major(suit_to_bid):
            bid = self.next_level_bid(self.longest_suit, '3494')
        elif self._opener_has_doubled_can_bid_suit(suit_to_bid):
            bid = self.next_level_bid(suit_to_bid, '3495')
        elif self.three_suits_bid_and_stopper() and self.suit_length(self.unbid_suit) >= 5:
            bid = self.next_nt_bid('3496')
        elif self._is_weak_can_bid_suit(suit_to_bid) and suit_to_bid == self.longest_suit:
            bid = self.next_level_bid(suit_to_bid, '3498')
        elif self._is_weak_can_bid_suit(suit_to_bid):
            bid = self.next_level_bid(suit_to_bid, '3497')
        elif self._is_weak_can_show_preference(suit_to_bid):
            bid = self._show_preference(suit_to_bid)
        elif (self.partner_last_bid.is_double and self.last_bid.is_pass and
              not self.opponents_at_game and self.cheapest_long_suit()):
            bid = self.next_level_bid(self.cheapest_long_suit(), '3499')
        elif suit_to_bid == self.opener_suit_two:
            bid = Pass('3500')
        elif self.hcp <= 5:
            bid = Pass('3571')
        elif self.hcp <= 10 and self.nt_level >= 2:
            bid = Pass('3595')
        else:
            bid = Pass('3597')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _show_preference(self, selected_suit: Suit) -> Bid:
        """Return bid when weak and no support for opener."""
        if selected_suit in self.opponents_suits:
            suit_preference = self._select_suit_support_opener()
            if suit_preference == self.opener_suit_two:
                bid = Pass('3501')
            else:
                bid = self.next_level_bid(suit_preference, '3502')
        else:
            bid = self.next_level_bid(selected_suit, '3503')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _three_suits_and_nt_selected(self) -> Bid:
        """Return bid after three suits shown and NT is selected."""
        barrier_is_broken = self.barrier_is_broken(self.opener_bid_one, self.opener_bid_two)
        level = self._three_suits_and_nt_selected_get_level(barrier_is_broken)
        if level >= self.nt_level:
            bid = self.nt_bid(level, '3504')
        elif self.suit_holding[self.opener_suit_two] < 5:
            bid = Pass('3505')
        else:
            bid = Pass('3573')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_broken_barrier_weak(self) -> Bid:
        """Return bid after opener breaks barrier with weak hand."""
        suit_to_bid = self._select_suit()
        best_major = self._best_major_fit()
        suit_preference = self._suit_preference()

        if self.hcp >= 15 and self.suit_length(self.opener_suit_one) >= 4:
            bid = self.nt_bid(4, '3506')
        elif best_major and self.hcp >= 11 and self.next_level(best_major) <= 4:
            bid = self.suit_bid(4, best_major, '3507')
        elif self._has_nine_points_and_opening_bid_is_major():
            bid = self.suit_bid(4, self.opener_suit_one, '3508')
        elif self.hcp >= 12 and self.three_suits_bid_and_stopper() and self.nt_level == 3:
            bid = self.nt_bid(3, '3509')
        elif self._has_eleven_points_five_four_no_support_for_opening_bid():
            bid = self._show_second_suit()
        elif self._has_eleven_points_five_card_suit_no_support_for_opening_bid():
            bid = self.next_level_bid(self.longest_suit, '3510')
        elif suit_to_bid.is_minor and 10 <= self.hcp <= 13 and self.is_balanced:
            bid = self.next_nt_bid('3511')
        elif (suit_to_bid.is_minor and 10 <= self.hcp <= 13 and
                suit_to_bid not in self.opponents_suits):
            level = max(4, self.next_level(suit_to_bid))
            bid = self.suit_bid(level, suit_to_bid, '3512')
        elif self._can_bid_suit_at_next_level(suit_to_bid):
            bid = self.bid_to_game(suit_to_bid, '3513')
        elif (suit_to_bid.is_minor and self.stoppers_in_bid_suits and
              self.nt_level <= 3 and self.overcall_made):
            bid = self.nt_bid(3, '3514')
        elif self.hcp >= 11 and suit_to_bid.is_minor:
            bid = self.suit_bid(5, suit_to_bid, '3576')
        elif self._nine_points_bid_up_to_level_four(suit_to_bid):
            bid = self.suit_bid(4, suit_to_bid, '3515')
        elif self._has_three_card_support_for_openers_major():
            bid = self.next_level_bid(self.opener_suit_one, '3516')
        elif (self.shape[0] >= 6 and
                HandSuit(self.longest_suit, self).honours >= 3 and
                self.longest_suit not in self.opponents_suits):
            bid = self.next_level_bid(self.longest_suit, '3517')
        elif self._eight_points_and_stoppers():
            bid = self.nt_bid(3, '3518')
        elif Bid(self.bid_history[-1]).is_value_call and self.hcp <= 9:
            bid = Pass('3519')
        elif self._opener_bid_new_suit_level_three_and_semi_balanced(suit_preference):
            bid = self.nt_bid(3, '3526')
        elif self._no_support_but_nt_possible(suit_preference):
            bid = self.nt_bid(3, '3521')
        elif self._seven_points_or_level_two_or_some_support():
            bid = self.next_level_bid(suit_preference, '3522')
        elif self.hcp <= 5 or self.hcp <= 9 and self.nt_level >= 3:
            bid = Pass('3523')
        else:
            bid = Pass('3578')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _show_second_suit(self) -> Bid:
        """Show second suit."""
        if self._fourteen_points_and_support_for_second_suit() or self.overcall_made:
            bid = self.next_level_bid(self.second_suit, '3524', raise_level=1)
        else:
            bid = self.next_level_bid(self.second_suit, '3525')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_nt_after_suit_response(self) -> Bid:
        """Respond after opener has bid NT after a suit response."""
        opener_jumped = self.is_jump(self.opener_bid_one, self.opener_bid_two)
        if self.opener_bid_two.name == '3NT':
            bid = Pass('3526')
        elif self.hcp >= 10 or (opener_jumped and self.hcp >= 7):
            bid = self._opener_nt_after_suit_response_strong()
        elif self._opener_has_rebid_one_nt_and_nt_level_is_two():
            bid = self.nt_bid(2, '3527')
        elif self._opener_has_rebid_one_nt_and_six_card_major():
            bid = self.bid_to_game(self.longest_suit, '3528')
        elif self._opener_has_rebid_one_nt_and_five_card_suit():
            bid = self.next_level_bid(self.longest_suit, '3529')
        elif self._opener_rebid_two_nt_and_five_four_and_shortage():
            bid = self.next_level_bid(self.second_suit, '3530')
        elif self._has_six_card_suit_and_level_three():
            bid = self.next_level_bid(self.longest_suit, '3531')
        elif self._cannot_support_openers_first_suit():
            bid = self.next_level_bid(self.second_suit, '3532')
        elif (self.suit_length(self.opener_suit_one) >= 6 and
                self._has_shortage()):
            bid = self.bid_to_game(self.opener_suit_one, '3533')
        elif self.nt_level >= 3 and self._has_shortage():
            bid = self.next_level_bid(self.longest_suit, '3534')
        elif self._opponents_doubled_openers_nt():
            bid = self.next_level_bid(self.longest_suit, '3535')
        # elif self.opener_bid_two.is_nt and self.nt_level < 3:
        #     bid = self.nt_bid(3, '3536')
        elif self.opener_bid_two.is_nt and self.shape[0] >= 8:
            bid = self.suit_bid(4, self.longest_suit, '3537')
        else:
            bid = Pass('3538')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_nt_after_suit_response_strong(self) -> Bid:
        """Respond, opener has bid NT after a suit response strong."""
        nt_level = self._get_nt_level_after_strong_nt()
        if self._has_seven_card_suit_and_fourteen_points():
            bid = self.nt_bid(4, '3539')
        elif self.five_five:
            bid = self._opener_nt_after_suit_response_strong_five_five()
        elif self.spades >= 6 and self.spade_suit not in self.opponents_suits:
            bid = self.bid_to_game(Denomination('S'), '3540')
        elif self.hearts >= 6 and self.heart_suit not in self.opponents_suits:
            # self.hcp >= 10 checked in calling function
            bid = self.bid_to_game(Denomination('H'), '3541')
        elif self._has_five_four_and_no_support():
            if self.hcp >= 11 and self.nt_level == 2:
                raise_level = 1
            else:
                raise_level = 0
            bid = self.next_level_bid(self.second_suit, '3542', raise_level)
        elif self._has_five_four_and_can_show_second_suit():
            bid = self.next_level_bid(self.second_suit, '3543', 1)
        elif self._can_bid_spades():
            bid = self.spade_bid(3, '3544')
        # elif (self.opener_bid_two.name == '2NT' and self.hcp >= 16
        #       and self.is_balanced and self.nt_level <= 6):
        #     bid = self.nt_bid(6, '3577')
        elif (self.opener_bid_two.name == '2NT' and
              9 <= self.hcp <= 15 and self.is_balanced and self.nt_level <= 3):
            bid = self.nt_bid(3, '3545')
        elif self._has_three_card_support_for_openers_major():
            bid = self.suit_bid(3, self.opener_suit_one, '3546')
        elif nt_level == 6 and self.stoppers_in_bid_suits:
            bid = self.nt_bid(nt_level, '3547')
        elif self.hcp >= 22:
            bid = self.nt_bid(7, '3548')
        elif self.hcp >= 17:
            bid = self.nt_bid(6, '3549')
        elif self._nt_can_support_minor():
            bid = self.nt_bid(3, '3550')
        elif self._has_five_four_and_fewer_than_ten_points():
            bid = self.next_level_bid(self.second_suit, '3551')
        elif self.nt_level <= 3 and self.stoppers_in_bid_suits:
            bid = self.nt_bid(nt_level, '3552')
        else:
            bid = Pass('3553')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_nt_after_suit_response_strong_five_five(self) -> Bid:
        """Respond, opener has bid NT after a suit response strong 5/5."""
        suit_to_bid = self._select_best_five_five()
        if suit_to_bid.is_major and self.hcp >= 10:
            raise_level = 1
        else:
            raise_level = 0
        bid = self.next_level_bid(suit_to_bid, '3554', raise_level=raise_level)
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_has_passed(self) -> Bid:
        """Rebid after opener has passed."""
        if self._has_four_card_support_at_level_three():
            bid = self.next_level_bid(self.opener_suit_one, '3555')
        elif self._has_six_card_suit_after_nt_opening():
            bid = self.next_level_bid(self.longest_suit, '3556')
        elif self.five_five_or_better:
            bid = self._bid_second_suit()
        elif self._has_strong_six_card_suit_at_level_two():
            bid = self.next_level_bid(self.longest_suit, '3557')
        elif self._is_balanced_thirteen_points():
            bid = self.nt_bid(3, '3558')
        elif (self.hcp >= 11 and self.five_four_or_better and
                self.second_suit not in self.opponents_suits):
            bid = self.next_level_bid(self.second_suit, '3559')
        elif self.hcp >= 11 and self.stoppers_in_bid_suits and self.nt_level <= 2:
            bid = self.next_nt_bid('3560')
        elif self.opener_bid_two.is_pass:
            bid = Pass('3561')
        else:
            bid = Pass('3579')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _bid_second_suit(self) -> Bid:
        """Bid second suit after opener has passed."""
        if self._can_bid_second_suit_at_level_three():
            bid = self.next_level_bid(self.second_suit, '3562')
        else:
            bid = Pass('3563')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    # Various utility functions

    def _three_suits_and_nt_selected_get_level(self, barrier_is_broken: bool) -> int:
        """Return level after NT is selected."""
        if self.hcp >= 13 or (barrier_is_broken and self.hcp >= 7):
            level = 3
        elif self.hcp >= 10:
            level = 2
        else:
            level = 1
        return level

    def _best_major_fit(self) -> Suit:
        """Return the best major fit (if any)."""
        best_major = None
        suit_one = self.opener_suit_one
        suit_two = self.opener_suit_two
        if (suit_one.is_major and
                suit_two.is_major and
                suit_one != suit_two):
            holding_one = self.suit_length(suit_one)
            holding_two = self.suit_length(suit_two)
            if holding_one <= 2 and holding_two <= 3:
                best_major = None
            elif holding_two+1 > holding_one:
                best_major = suit_two
            else:
                best_major = suit_one
        return best_major

    def _get_nt_level_after_strong_nt(self) -> int:
        """Return the appropriate NT level if opener bids nt after suit """
        nt_level = 3
        if self.opener_bid_two.name == '2NT':
            if self.hcp >= 15 and self.bid_one.level == 1:
                nt_level = 6
            # elif self.hcp >= 13 and self.bid_one.level == 1:
            #     nt_level = 4
        return nt_level

    # Suit selection functions

    def _select_suit(self) -> Suit:
        """ Return responder's selected suit following change
            of suit by opener.
        """
        if ((self.shape[0] >= 7 or self.hcp >= 11) and
                self.longest_suit.is_major and
                self.suit_length(self.opener_suit_one) <= 2 and
                self.suit_length(self.opener_suit_two) <= 3):
            selected_suit = self._select_suit_no_support()
        else:
            selected_suit = self._select_suit_support_opener()
        return selected_suit

    def _select_suit_no_support(self) -> Suit:
        """Return suit with no support for opener."""
        if self.shape[1] >= 5 and self.shape[3] <= 1:
            selected_suit = self.second_suit
        else:
            selected_suit = self.longest_suit
        if selected_suit in self.opponents_suits:
            if selected_suit == self.longest_suit:
                selected_suit = self.second_suit
            else:
                selected_suit = self.longest_suit
        return selected_suit

    def _select_suit_support_opener(self) -> Suit:
        """Return suit support for opener."""
        if (self.suit_length(self.opener_suit_one) >= 3 or
                self.suit_length(self.opener_suit_two) >= 4):
            bid_no_trumps = False
        elif self.barrier_is_broken(self.opener_bid_one, self.opener_bid_two) or self.hcp >= 10:
            bid_no_trumps = self._suitability_for_nt()
        else:
            bid_no_trumps = False
        if bid_no_trumps:
            selected_suit = self.no_trumps
        else:
            selected_suit = self._suit_preference()
        return selected_suit

    def _suit_preference(self) -> Suit:
        """Return suit preference for a bid."""
        suit_one = self.opener_suit_one
        suit_two = self.opener_suit_two
        if suit_one.is_suit:
            holding_one = self.suit_length(suit_one)
        else:
            holding_one = 0
        if suit_two.is_suit:
            holding_two = self.suit_length(suit_two)
        else:
            holding_two = 0
        if holding_one + 1 == holding_two:
            if (suit_one.is_minor and
                    suit_two.is_major and
                    (not self.is_jump(self.opener_bid_one, self.opener_bid_two) or
                     self.opener_bid_two.level == 3 or
                     (self.opener_bid_one.is_minor and self.opener_bid_two.is_major) and
                     self.suit_length(self.opener_suit_two) >= 4)):
                selected_suit = suit_two
            else:
                selected_suit = suit_one
        elif holding_one >= holding_two:
            if (suit_one.is_minor and
                    suit_two.is_major and
                    holding_two >= 4):
                selected_suit = suit_two
            elif (suit_one.is_minor and
                    suit_two.is_major and
                    self.opener_bid_two.level == 3 and
                    holding_two >= 3):
                selected_suit = suit_two
            else:
                selected_suit = suit_one
        else:
            selected_suit = suit_two
        if not suit_one.is_suit:
            selected_suit = suit_two
        if not suit_two.is_suit:
            selected_suit = suit_one
        return selected_suit

    def _suits_not_bid_by_opener(self) -> list[Suit]:
        """Return a list of suits not bid by opener."""
        suit_list = []
        for suit in self.suits:
            if (suit != self.opener_suit_one and
                    suit != self.opener_suit_two):
                suit_list.append(suit)
        return suit_list

    def _get_suit_if_five_five(self) -> Suit:
        """Return selected suit."""
        first_suit = self.longest_suit
        second_suit = self.second_suit
        if first_suit.is_major:
            suit = first_suit
        else:
            suit = second_suit
        return suit

    def _get_suit_with_five_five_after_opener_jumped(self) -> Suit:
        """Return the suit to bid with 5/5."""
        if self.bid_one.denomination == self.longest_suit:
            suit = self.second_suit
        else:
            suit = self.longest_suit

        if suit in self.opponents_suits:
            if suit == self.longest_suit:
                suit = self.second_suit
            else:
                suit = self.longest_suit
        return suit

    def _suit_for_trial_after_opener_changes_suit(self) -> Suit:
        """Return a suit for trial bid after opener changed suit."""
        suit_to_bid = self._suit_preference()
        if (self.five_card_major_or_better and
                self.hcp >= 10 or
                (self.hcp >= 8 and self.shape[0] >= 6)):
            if (self.hearts >= 5 and
                    self.heart_suit not in self.opponents_suits):
                suit_to_bid = self.heart_suit
            elif (self.spades >= 5 and
                    self.spade_suit not in self.opponents_suits):
                suit_to_bid = self.spade_suit
        return suit_to_bid

    def _select_best_five_five(self) -> Suit:
        """Return the best suit for a 5/5 or better hand."""
        suits = []
        for suit in self.suits:
            if self.suit_length(suit) >= 5 and suit not in self.opponents_suits:
                suits.append(suit)
        suit = suits[0]
        return suit

    def _unbid_suit(self) -> Suit | None:
        """Return the 4th (unbid) suit (if any)"""
        suits = [self.spade_suit, self.heart_suit, self.diamond_suit, self.club_suit]
        calls = [self.opener_bid_one, self.responder_bid_one, self.opener_bid_two]
        for call in calls:
            if call.is_suit_call:
                suits.remove(call.denomination)
            else:
                return None
        if len(suits) == 1:
            unbid_suit = suits[0]
        else:
            unbid_suit = None
        return unbid_suit

    def _fourth_suit(self) -> Suit | None:
        """Return the suit not bid by opener and responder."""
        suits = [suit for suit in SUITS.values()]
        if self.opener_suit_one in suits:
            suits.remove(self.opener_suit_one)
        if self.opener_suit_two in suits:
            suits.remove(self.opener_suit_two)
        if self.responder_bid_one.denomination in suits:
            suits.remove(self.responder_bid_one.denomination)
        if len(suits) == 1:
            return suits[0]
        return None

    # Various boolean functions

    def _suit_support_points(self, suit_to_bid: Suit) -> bool:
        """Return suit_support_points: a measure of support strength."""
        if suit_to_bid.is_suit:
            suit_support_points = self.hand_value_points(suit_to_bid)
            suit_holding = self.suit_length(suit_to_bid)
            if suit_holding >= 4:
                suit_support_points += suit_holding - 4  # add 1 for any length over 4
        else:
            suit_support_points = 0
        return suit_support_points

    def _suitability_for_nt(self) -> bool:
        """ Return True if  a strong 5 card suit or a 4 card suit with stoppers."""
        if self.nt_level > 3:
            return False
        for suit in self._suits_not_bid_by_opener():
            quality = HandSuit(suit, self).suit_quality()
            if not (self.suit_length(suit) >= 5 or
                    (self.suit_length(suit) == 4 and
                        quality >= 1.5) or
                    self.has_stopper(suit) or
                    self.barrier_is_broken(self.opener_bid_one, self.opener_bid_two)):
                return False
        return True

    def _weak_two_opening(self) -> bool:
        """Return True if opener has bid weak two."""
        return (self.opener_bid_one.level >= 2 and
                self.opener_bid_one.is_suit_call and
                self.opener_bid_one.name != '2C')

    def _has_six_card_suit_and_opener_passed(self) -> bool:
        """Return True if opener has passed and responder has 6 card suit."""
        return (self.opener_bid_two.is_pass and
                self.shape[0] >= 6 and
                self.hcp >= 10 and
                self.next_level(self.longest_suit) <= 2 and
                self.longest_suit not in self.opponents_suits)

    def _game_has_been_bid_by_opposition(self) -> bool:
        """Return True if game has been bid."""
        return (self.overcaller_bid_one.is_game or
                self.advancer_bid_one.is_game or
                self.overcaller_bid_two.is_game)

    def _opener_at_game_but_can_show_preference(self) -> bool:
        """Return True if Opener at game level and can rebid own suit."""
        return (self.opener_bid_two.is_game and
                self.opener_bid_two.is_suit_call and
                self.opener_suit_one != self.opener_suit_two and
                self.longest_suit.rank < self.opener_suit_two.rank)

    def _has_fifteen_points_and_opener_has_rebid_three_nt(self) -> bool:
        """Return True if opener has rebid 3NT and hand hs 15+ points."""
        return (self.opener_bid_one.is_suit_call and
                self.opener_bid_two.name == '3NT' and
                self.bid_one.level != 3 and
                self.hcp >= 15)

    def _has_fourteen_with_openers_twenty_three_in_nt(self) -> bool:
        """Return True if opener has 23+ points, rebid 3NT and hand has 14+."""
        return (self.opener_bid_one.name == '2C' and
                self.opener_bid_two.name == '3NT' and
                self.hcp >= 14)

    def _has_twelve_with_openers_nineteen_in_nt(self) -> bool:
        """Return True if opener rebids 3NT after suit and 12+."""
        return (self.opener_bid_one.is_suit_call and
                self.opener_bid_two.name == '3NT' and
                self.bid_one.level == 1 and
                self.hcp >= 12)

    def _has_eighteen_with_openers_nineteen_in_nt(self) -> bool:
        """Return True if opener rebids 3NT after suit and 18+."""
        return (self.opener_bid_one.is_suit_call and
                self.opener_bid_two.name == '3NT' and
                self.bid_one.level == 1 and
                self.hcp >= 18)

    def _has_six_card_suit_with_openers_nineteen_in_nt(self) -> bool:
        """Return True if opener rebids 3NT after suit and 6 card suit."""
        return (self.opener_bid_two.name == '3NT' and
                self.my_last_bid.level <= 2 and
                self.shape[0] >= 6 and
                self.longest_suit not in self.opponents_suits and
                self.longest_suit.is_major)

    def _thirteen_points_support_and_opener_in_game_in_major(self) -> bool:
        """Return True if opener at game in major, 14+ points with support."""
        return (self.opener_bid_two.level == 4 and
                not self.opener_bid_one.name == '1NT' and
                self.opener_suit_two.is_major and
                self.hcp >= 13 and
                (self.suit_length(self.opener_suit_two) >= 3 or
                 self.suit_points(self.opener_suit_two) >= 4))

    def _opener_has_passed_can_compete(self) -> bool:
        """Return True if opener has passed and can compete."""
        return (self.opener_bid_two.is_pass and
                self.suit_length(self.opener_suit_one) >= 2 and
                self.overcall_made)

    def _has_sixteen_and_six_card_suit(self) -> bool:
        """Return True with 16+ points and a six card suit."""
        return (self.shape[0] >= 6 and
                self.hcp >= 16 and
                self.longest_suit not in self.opponents_suits)

    def _has_sixteen_and_three_card_support(self) -> bool:
        """Return True with 16+ points and a 3 card support."""
        return (self.hcp >= 16 and
                self.suit_length(self.opener_suit_one) >= 3 and
                not self.bidding_above_game)

    def _has_seventeen_and_three_card_support_can_bid_game(self) -> bool:
        """Return True with 17+ points, 3 card support and can bid game."""
        return (self.hcp >= 17 and
                self.opener_bid_one.is_major and
                self.suit_length(self.opener_suit_one) >= 3 and
                self.next_level(self.opener_suit_one) <= 4)

    def _can_rebid_openers_suit(self) -> bool:
        """Return True if possible to rebid openers suit."""
        trial_bid = self.next_level_bid(self.opener_suit_one, '3564')
        return (trial_bid.level <= 3 or
                (trial_bid.level <= 4 and not self.overcall_made) or
                (trial_bid.level <= 4 and self.hcp >= 12) and
                self.suit_holding[self.opener_suit_one] >= 2)

    def _opener_has_responded_to_stayman(self) -> bool:
        """Return True if responder's previous bid was Stayman."""
        return ((self.opener_bid_one.name == '1NT' and
                self.bid_one.name == '2C') or
                (self.opener_bid_one.name == '2NT' and
                 self.bid_one.name == '3C'))

    def _opener_has_bid_major_at_three_level_thirteen_points(self) -> bool:
        """Return True if opener has bid a major at 3 level and 13+ points."""
        return (self.opener_bid_two.level == 3 and
                self.opener_suit_two.is_major and
                self.hcp >= 13)

    def _has_six_card_suit_ten_points_and_opener_support(self) -> bool:
        """Return True six card suit, 10 points and opener's support."""
        return (self.hcp >= 10 and
                self.shape[0] >= 6 and
                self.opener_suit_two == self.bid_one.denomination)

    def _opener_bids_hearts_but_fewer_than_four_hearts(self) -> bool:
        """Return True if opener has bid hearts, not spades (stayman)."""
        return (self.suit_length(self.opener_suit_two) <= 4 and
                self.opener_suit_two == self.heart_suit and
                self.spade_suit not in self.opponents_suits)

    def _has_four_cards_in_openers_major_fewer_than_ten_points(self) -> bool:
        """Return True with fewer than 10 points and suit is 4+ card major."""
        return (self.opener_suit_two.is_major and
                self.suit_length(self.opener_suit_two) >= 4 and
                self.hcp <= 10)

    def _overcall_made_has_five_five(self, suit: Suit) -> bool:
        """Return True if overcall and 5/5."""
        return (self.overcall_made and
                self.five_five and
                suit not in self.opponents_suits)

    def _opener_has_has_doubled_and_five_card_suit(self) -> bool:
        """Return True if opener's rebid is double and 5 card suit."""
        return (self.opener_bid_two.is_double and
                self.suit_length(self.opener_suit_one) <= 1 and
                self.shape[0] >= 5 and
                self.longest_suit not in self.opponents_suits)

    def _has_bid_two_nt_and_opener_bids_minor(self) -> bool:
        """Return True if bid 2NT and opener bids minor."""
        return (self.bid_one.name == '2NT' and
                self.opener_suit_two.is_minor and
                (self.opener_bid_two.level < 2 or
                 self.hcp <= 11))

    def _responder_jumped_support_fewer_than_twelve_points_fewer_than_five_points(self) -> bool:
        """Return True if responder has jumped, opener support fewer than 12 pts."""
        suit = self.bid_one.denomination
        return (self.is_jump(self.opener_bid_one, self.bid_one) and
                suit == self.opener_suit_one and
                suit.is_minor and
                self. hcp <= 12)

    def _opener_has_jumped_or_level_is_three(self) -> bool:
        """Return True if opener has jumped."""
        opener_jumped = (self.is_jump(self.opener_bid_one, self.opener_bid_two) and
                         not self.overcall_made)
        responder_has_jumped = self.is_jump(self.opener_bid_one, self.bid_one)
        return ((opener_jumped and
                not self.overcall_made and
                not responder_has_jumped) or
                self.opener_bid_two.level >= 3)

    def _has_fewer_than_nine_points_and_passed_or_one_nt(self) -> bool:
        """Return True if weak and no suit."""
        return (self.hcp <= 9 and
                (self.bid_one.name == '1NT' or
                 self.bid_one.is_pass))

    def _has_six_card_suit_and_can_bid(self) -> bool:
        """Return True if six card suit and can bid"""
        return (self.shape[0] >= 6 and
                (self.next_level(self.longest_suit) <= 2 or
                 self.hcp >= 10))

    def _opener_bids_major_at_level_three_can_support(self) -> bool:
        """Return True if opener bids major at level 3 and can support."""
        return (self.opener_bid_two.level == 3 and
                self.suit_length(self.opener_suit_two) >= 2 and
                self.opener_suit_two.is_major)

    def _is_weak_and_shortage_in_openers_suit(self) -> bool:
        """Return True with singleton or void in opener's repeated suit."""
        return (self.opener_suit_one == self.opener_suit_two and
                not self.is_jump(self.my_last_bid, self.opener_bid_two) and
                self.suit_length(self.opener_suit_one) <= 1 and
                self.hcp <= 12 and
                self.nt_level >= 3)

    def _has_five_four_and_opener_at_three_level(self) -> bool:
        """Return True if opener at level 3 and hand has 5/4."""
        return (self.opener_bid_two.level == 3 and
                self.five_four and
                self.next_level(self.second_suit) <= 3 and
                self.second_suit not in self.opponents_suits)

    def _is_weak_openers_suit_is_minor(self) -> bool:
        """Return True if weak and opener's suit is a minor."""
        return (self.opener_suit_one.is_minor and
                10 <= self.hcp <= 12 and
                self.is_balanced and
                self.stoppers_in_bid_suits)

    def _intermediate_has_four_card_major_and_opener_in_minor(self) -> bool:
        """Return True if weak and opener in minor and 4 card major."""
        return (self.opener_suit_one.is_minor and
                10 <= self.hcp <= 12 and
                self.shape[1] >= 4 and
                self.second_suit.is_major and
                self.second_suit not in self.opponents_suits)

    def _strong_has_six_card_major_and_opener_in_minor(self) -> bool:
        """Return True if opener in minor and 6 card major."""
        return (self.opener_suit_one.is_minor and
                self.hcp >= 15 and
                self.shape[0] >= 6 and
                self.longest_suit.is_major and
                self.longest_suit not in self.opponents_suits)

    def _weak_has_six_card_major_and_opener_in_minor(self) -> bool:
        """Return True if opener in minor and 6 card major."""
        return (self.opener_suit_one.is_minor and
                self.hcp >= 10 and
                self.shape[0] >= 6 and
                self.longest_suit.is_major and
                self.longest_suit not in self.opponents_suits)

    def _weak_has_stoppers_and_opener_in_minor(self, nt_level) -> bool:
        """Return True if opener in minor and stoppers."""
        return (self.opener_suit_one.is_minor and
                self.hcp >= 10 and
                self.stoppers_in_bid_suits and
                self.nt_level <= nt_level)

    def _intermediate_has_seven_card_major(self) -> bool:
        """Return True with 7  card major and fewer than 17 points."""
        return (self.shape[0] >= 7 and
                self.longest_suit.is_major and
                self.hcp <= 16)

    def _opener_in_minor_and_stoppers(self) -> bool:
        """Return True if opener has bid minor and hand has stoppers."""
        return (self.opener_suit_one.is_minor and
                self.stoppers_in_unbid_suits() and
                self.stoppers_in_bid_suits and
                self.nt_level <= 3)

    def _opener_in_minor_distributional_with_stoppers(self) -> bool:
        """Return True if opener in minor, distributional with stoppers."""
        return (self.hcp >= 13 and
                self.opener_suit_one.is_minor and
                self.stoppers_in_bid_suits and
                self.shape[1] <= 4 and
                self.nt_level <= 3)

    def _can_bid_four_card_major(self) -> bool:
        """Return True if suit_to_bid is a minor and has 4 card major."""
        return (self.five_four and
                self.second_suit.is_major and
                self.second_suit not in self. opponents_suits)

    def _opener_has_jumped_no_support(self) -> bool:
        """Return True if opener_has_jumped and no support."""
        return (self.is_jump(self.opener_bid_one, self.bid_one) and
                self.opener_suit_one != self.bid_one.denomination and
                not self.overcaller_bid_one.is_value_call)

    def _own_suit_is_minor_stoppers_in_other_suits_level_three(self) -> bool:
        """Return True if own suit is minor but stoppers in other suits."""
        return (self.longest_suit.is_minor and
                self.stoppers_in_other_suits(self.opener_suit_one) and
                self.nt_level <= 3)

    def _opponents_bid_own_suit_stoppers(self) -> bool:
        """Return True if opponents_bid own suit and stoppers."""
        return (self.longest_suit in self.opponents_suits and
                self.stoppers_in_bid_suits and
                self.nt_level <= 3)

    def _has_thirteen_points_competitive(self) -> bool:
        """Return True if 13+ points and competitive."""
        return (self.hcp >= 13 and
                not self.overcall_made and
                self.next_level(self.longest_suit) <= 4)

    def _own_suit_is_minor_stoppers_in_other_suits_level_two(self) -> bool:
        """Return True if own suit is minor and stoppers."""
        return (self.longest_suit.is_minor and
                self.nt_level <= 2 and
                self.stoppers_in_other_suits(self.opener_suit_one))

    def _balanced_and_opener_bid_minor(self) -> bool:
        """Return True if balanced and opener bid minor"""
        return (self.opener_suit_one.is_minor and
                self.stoppers_in_bid_suits and
                self.is_balanced and
                self.nt_level <= 3)

    def _opener_has_jumped_and_can_support_non_competitive(self) -> bool:
        """Return True if opener has jumped and 2 card support card suit."""
        return (self.hand_value_points(self.opener_suit_one) >= 9 and
                not self.competitive_auction and
                (self.is_jump(self.opener_bid_one, self.opener_bid_two) and
                 not self.overcaller_bid_one.is_value_call))

    def _opener_has_jumped_and_can_support_competitive(self) -> bool:
        """Return True if opener has jumped and 3 card support card suit."""
        return (self.hcp >= 12 and
                self.hand_value_points(self.opener_suit_one) >= 10 and
                self.competitive_auction and
                not self.stoppers_in_bid_suits and
                (self.is_jump(self.opener_bid_one, self.opener_bid_two) and
                 self.overcaller_bid_one.is_value_call))

    def _has_thirteen_points_and_opener_has_jumped(self) -> bool:
        """Return True if hcp >= 13 and opener has jumped."""
        return (self.hcp >= 13 and
                self.is_jump(self.bid_one, self.opener_bid_two) and
                self.nt_level <= 4)

    def _has_twelve_points_and_opener_has_jumped(self) -> bool:
        """Return True if hcp >= 12 and opener has jumped."""
        return ((self.hcp >= 12 or self.is_jump(self.bid_one, self.opener_bid_two)) and
                self.nt_level <= 3 and
                self.stoppers_in_bid_suits)

    def _weak_but_barrier_broken(self, suit: Suit) -> bool:
        """Return True if weak and barrier broken."""
        barrier_is_broken = self.barrier_is_broken(self.opener_bid_one,
                                                   self.opener_bid_two)
        return (barrier_is_broken and
                6 <= self.hcp <= 8 and
                self.next_level(suit) <= 3 and
                suit not in self.opponents_suits)

    def _no_support_own_suit_is_minor_with_stops(self) -> bool:
        """Return True if _suit is minor and stops."""
        suit_to_bid = self._select_suit()
        return (self.nt_level <= 3 and
                ((suit_to_bid.is_minor and
                 self.stoppers_in_bid_suits and
                 self.suit_length(self.opener_suit_two) <= 3) or
                 suit_to_bid in self.opponents_suits))

    def _is_balanced_own_suit_is_minor_with_stops(self) -> bool:
        """Return True if own suit is minor, balanced and stops."""
        suit_to_bid = self._select_suit()
        return (self.is_balanced and
                suit_to_bid.is_minor and
                self.stoppers_in_bid_suits and
                self.nt_level <= 3)

    def _both_openers_suits_are_minors(self) -> bool:
        """Return True if both opener's suits are minor."""
        return (self.opener_suit_one.is_minor and
                self.opener_suit_two.is_minor and
                self.stoppers_in_bid_suits and
                self.hcp >= 13)

    def _can_support_opener(self, suit_to_bid: Suit) -> bool:
        """Return True if suit is one of opener's suits."""
        return (suit_to_bid == self.opener_suit_one or
                suit_to_bid == self.opener_suit_two)

    def _has_fourteen_points_and_suit_is_minor(self, suit_to_bid: Suit) -> bool:
        """Return True if suit is minor and 14+ points."""
        return (self.hcp >= 14 and
                self.three_suits_bid_and_stopper() and
                suit_to_bid.is_minor and
                self.nt_level <= 3)

    def _has__strong_seven_card_suit_and_fourteen_points(self) -> bool:
        """Return True with a strong 7 card suit and 14 points."""
        return (self.shape[0] >= 7 and
                self. hcp >= 14 and
                self.suit_points(self.longest_suit) >= 8)

    def _has_ten_points_and_can_support_opener(self, suit: Suit, support_points: int) -> bool:
        """Return True with 10+points and can support opener."""
        return (self._can_support_opener(suit) and
                (support_points >= 10 or
                 self.suit_length(suit) >= 4 and
                 self.hcp >= 10))

    def _has_eleven_points_and_three_suits_bid(self) -> bool:
        """Return True with 11+ points and three suits bid."""
        return (self.hcp >= 11 and
                self.three_suits_bid_and_stopper() and
                self.is_semi_balanced and
                self.nt_level <= 2)

    def _can_support_minor_but_is_semi_balanced(self, suit: Suit, support_points: int) -> bool:
        """Return True if can support minor and semi_balanced."""
        return (support_points >= 13 and
                suit.is_minor and
                self.is_semi_balanced and
                self.stoppers_in_bid_suits and
                self.nt_level <= 2 and
                self.shape[3] >= 2)

    def _is_balanced_support_for_openers_second_suit(self, suit_to_bid: Suit) -> bool:
        """Return True if suit is opener's second and is balanced."""
        return (suit_to_bid == self.opener_suit_two and
                self.suit_length(suit_to_bid) <= 3 and
                self.is_balanced and
                self.stoppers_in_bid_suits and
                self.nt_level <= 2)

    def _has_three_card_support_for_openers_major(self) -> bool:
        """Return True if 3 card support for opener's major."""
        return (self.opener_suit_one != self.opener_suit_two and
                self.opener_suit_one.is_major and
                self.suit_length(self.opener_suit_one) >= 3
                and self.next_level(self.opener_suit_one) <= 3)

    def _is_strong_has_stoppers(self) -> bool:
        """Return True if very strong with stoppers."""
        return (self.is_jump(self.bid_one, self.opener_bid_two) and
                self.hcp >= 16 and
                self.stoppers_in_unbid_suits() and
                self.nt_level <= 4)

    def _is_distributional_and_barrier_not_broken(self, suit_to_bid: Suit) -> bool:
        """Return True if distributional and barrier not broken."""
        trial_bid = self.next_level_bid(suit_to_bid)
        barrier_is_broken = self.barrier_is_broken(self.opener_bid_one, self.opener_bid_two)
        return (not trial_bid.is_game and
                self.five_five_or_better or
                (self.suit_length(suit_to_bid) < 7 and
                 self.shape[0] >= 6 and not barrier_is_broken) or
                (self.shape[0] >= 6 and
                 self.hcp >= 10) and
                trial_bid.level <= 2)

    def _has_biddable_five_card_major(self, suit_to_bid: Suit) -> bool:
        """Return True with biddable major."""
        return (5 <= self.hcp <= 9 and
                suit_to_bid.is_minor and
                self.longest_suit.is_major and
                self.suit_points(self.longest_suit) >= 5 and
                not self.competitive_auction and
                self.longest_suit not in self.opponents_suits)

    def _opener_has_doubled_can_bid_suit(self, suit_to_bid: Suit) -> bool:
        """Return True if weak hand passes suit test."""
        return (self.opener_bid_two.is_double and
                Bid(self.bid_history[-1]).is_pass and
                (self.next_level_bid(suit_to_bid).level <= 2 or
                 self.hcp >= 8) and
                (self.hcp >= 6 or self.suit_length(suit_to_bid) >= 4) and
                suit_to_bid not in self.opponents_suits)

    def _is_weak_can_bid_suit(self, suit_to_bid: Suit) -> bool:
        """Return True if weak hand passes suit test."""
        return ((self.next_level_bid(suit_to_bid).level <= 2 or
                self.hcp >= 8) and
                (self.hcp >= 6 or self.suit_length(suit_to_bid) >= 4) and
                suit_to_bid not in self.opponents_suits)

    def _is_weak_can_show_preference(self, suit_to_bid: Suit) -> bool:
        """Return True if hand can make suit preference."""
        return (Bid(self.bid_history[-1]).is_pass and
                self.next_level(suit_to_bid) <= 2 and
                self.opener_suit_two != suit_to_bid)

    def _has_nine_points_and_opening_bid_is_major(self) -> bool:
        """Return True if opening bid is major and 11+ points."""
        return (self.opener_suit_one != self.opener_suit_two and
                self.opener_suit_one.is_major and
                self.hcp >= 9 and
                self.suit_length(self.opener_suit_one) >= 3 and
                self.next_level(self.opener_suit_one) <= 4)

    def _has_eleven_points_five_four_no_support_for_opening_bid(self) -> bool:
        """Return True with 11 +points, no support for opening bid and 5/4."""
        return (self.opener_suit_one != self.opener_suit_two and
                self.five_four_or_better and
                self.suit_length(self.opener_suit_one) <= 3 and
                self.hcp >= 11 and
                self.second_suit not in self.opponents_suits)

    def _has_eleven_points_five_card_suit_no_support_for_opening_bid(self) -> bool:
        """Return True with 11 +points, no support for opening bid and semi_balanced."""
        return (self.opener_suit_one != self.opener_suit_two and
                self.is_semi_balanced and
                self.shape[0] >= 5 and
                self.suit_length(self.opener_suit_one) <= 3 and
                self.hcp >= 11 and
                self.longest_suit not in self.opponents_suits)

    def _can_bid_suit_at_next_level(self, suit_to_bid: Suit) -> bool:
        """Return True with 12 points or 9 points and major"""
        return ((self.hcp >= 12 or
                 (self.hcp >= 9 and suit_to_bid.is_major)) and
                suit_to_bid not in self.opponents_suits)

    def _nine_points_bid_up_to_level_four(self, suit_to_bid: Suit) -> bool:
        """Return True if greater than 9 points and level <= 4."""
        return (self.hcp >= 9 and
                suit_to_bid.is_suit and
                suit_to_bid not in self.opponents_suits and
                self.next_level(suit_to_bid) <= 4)

    def _eight_points_and_stoppers(self) -> bool:
        """Return True if 8+ points and stoppers."""
        return (self.hcp >= 9 and
                self.stoppers_in_bid_suits and
                self.nt_level <= 3)

    def _seven_points_or_level_two_or_some_support(self) -> bool:
        """Return True if some possibility to bid."""
        return ((self.hcp >= 7 or
                 self.opener_bid_two.level <= 2 or
                 self.suit_length(self.opener_suit_one) >= 2))

    def _fourteen_points_and_support_for_second_suit(self) -> bool:
        """Return True if 14+ points and support for second suit."""
        trial_bid = self.next_level_bid(self.second_suit, raise_level=1)
        return (self.opener_suit_two == self.second_suit and
                self.hcp <= 14 and
                (not trial_bid.is_game or
                 self.is_jump(self.opener_bid_one, self.opener_bid_two)))

    def _opener_has_rebid_one_nt_and_nt_level_is_two(self) -> bool:
        """Return True if opener bid 1NT with 9+ points."""
        return (self.opener_bid_two.name == '1NT' and
                self.nt_level == 2 and
                self.shape[0] <= 5 and
                self.hcp == 9 and
                self.nt_level <= 2)

    def _opener_has_rebid_one_nt_and_six_card_major(self) -> bool:
        """Return True if opener bid 1NT with 9+ points and six card major."""
        return (self.opener_bid_two.name == '1NT' and
                self.hcp == 9 and
                self.shape[0] >= 6 and
                self.longest_suit.is_major and
                self.longest_suit not in self.opponents_suits)

    def _opener_has_rebid_one_nt_and_five_card_suit(self) -> bool:
        """Return True if opener bid 1NT with 9+ points."""
        return (self.opener_bid_two.name == '1NT' and
                self.hcp == 9 and
                self.shape[0] >= 5 and
                self.longest_suit not in self.opponents_suits)

    def _opener_rebid_two_nt_and_five_four_and_shortage(self) -> bool:
        """Return True if opener rebids 2NT and 5/4."""
        return (self.opener_bid_two.name == '2NT' and
                self.hcp >= 6 and
                not self._has_bid_four_card_major_at_one_level() and
                self.five_four_or_better and
                self.suit_length(self.opener_suit_one) <= 1 and
                self.second_suit not in self.opponents_suits)

    def _has_bid_four_card_major_at_one_level(self) -> bool:
        """Return True if a weak hand has bid 4 card major at one level."""
        return (self.hcp <= 6 and
                self.bid_one.is_major and
                self.bid_one.denomination != self.longest_suit)

    def _has_six_card_suit_and_level_three(self) -> bool:
        """Return True if six card suit and next level <= 3."""
        return (4 <= self.hcp <= 7 and
                self.shape[0] >= 6 and
                self.longest_suit not in self.opponents_suits and
                self.second_suit not in self.opponents_suits and
                self.next_level(self.longest_suit) <= 3)

    def _has_shortage(self) -> bool:
        """Return True if has shortage and level <= 3."""
        return (self.hcp >= 5 and
                self.shape[3] <= 1 and
                self.shape[0] >= 5 and
                self.next_level(self.longest_suit) <= 3 and
                self.longest_suit not in self.opponents_suits and
                not self._has_bid_four_card_major_at_one_level())

    def _opponents_doubled_openers_nt(self) -> bool:
        """Return True if opponents have doubled openers NT bid."""
        return (self.hcp >= 5 and
                self.opponents_have_doubled and
                self.longest_suit not in self.opponents_suits and
                self.shape[0] >= 5)

    def _has_seven_card_suit_and_fourteen_points(self) -> bool:
        """Return True if 7 card suit and 14+ points."""
        return (self.opener_bid_two.name == '2NT' and
                self.shape[0] >= 7 and
                self.hcp >= 14)

    def _has_five_four_and_no_support(self) -> bool:
        """Return True if 5/4 and no support."""
        return (self.five_four_or_better and
                self.hcp >= 14 and
                self.suit_length(self.opener_suit_one) <= 2 and
                self.second_suit not in self.opponents_suits)

    def _has_five_four_and_fewer_than_ten_points(self) -> bool:
        """Return True if 5/4 and fewer than 10 points."""
        return (self.hcp <= 9 and
                self.five_four_or_better and
                not self.bid_one.is_pass and
                self.second_suit not in self.opponents_suits)

    def _can_bid_spades(self) -> bool:
        """Return True if 5+ spades and level <= 3."""
        return (self.spades >= 5 and
                self.my_last_bid.denomination != self.spade_suit and
                self.next_level(self.spade_suit) <= 3 and
                self.spade_suit not in self.opponents_suits)

    def _has_four_card_support_at_level_three(self) -> bool:
        """Return True if has 4 card support at level 3."""
        return (self.opener_bid_one.is_suit_call and
                self.suit_length(self.opener_suit_one) >= 4 and
                self.hand_value_points(self.opener_suit_one) >= 10 and
                self.next_level(self.opener_suit_one) <= 3)

    def _has_six_card_suit_after_nt_opening(self) -> bool:
        """Return True if opening bid is nt and has 6 card suit."""
        return (self.opener_bid_one.is_nt and
                self.shape[0] >= 6 and
                not self.overcaller_bid_one.is_double and
                self.longest_suit not in self.opponents_suits and
                self.next_level(self.longest_suit) <= 3 and
                self.hcp >= 6)

    def _has_strong_six_card_suit_at_level_two(self) -> bool:
        """Return True if strong 6 card suit at level 2."""
        return (self.shape[0] >= 6 and
                self.suit_points(self.longest_suit) >= 7 and
                self.next_level(self.longest_suit) <= 2 and
                self.longest_suit not in self.opponents_suits)

    def _is_balanced_thirteen_points(self) -> bool:
        """Return True if is balanced with 13+ points."""
        return (self.hcp >= 13 and
                # self.is_balanced and
                self.stoppers_in_bid_suits and
                self.nt_level <= 3)

    def _can_bid_second_suit_at_level_three(self) -> bool:
        """Return True if can bid second suit at level 3."""
        return (((self.hcp >= 7 and
                  (self.suit_length(self.second_suit) >= 6 or
                   self.next_level_bid(self.second_suit).level <= 2) or
                  self.hcp >= 12) or

                (self.shape[1] >= 4 and
                 self.hcp >= 6 and
                 self.next_level(self.second_suit) <= 3)) and

                self.second_suit not in self.opponents_suits)

    def _is_strong_unbalanced_and_two_card_support_for_opener(self) -> bool:
        """Return True if strong_unbalanced and 2 card support for opener."""
        return (self.hcp >= 16 and
                self.suit_length(self.opener_suit_one) >= 2 and
                not self.is_balanced)

    def _suit_to_support_is_minor_and_stoppers(self, suit_to_bid: Suit) -> bool:
        """Return True if suit is minor and stoppers."""
        if self.hcp <= 9:
            level = 1
        elif self.hcp <= 13:
            level = 2
        else:
            level = 3
        return (suit_to_bid.is_minor and
                # self.is_balanced and
                self.stoppers_in_unbid_suits() and
                self.nt_level <= level)

    def _opener_bid_new_suit_level_three_and_semi_balanced(self, suit_preference: Suit) -> bool:
        """Return True if opener has bid new suit at level 3 and semi balanced."""
        return (suit_preference.is_minor and
                suit_preference == self.opener_suit_two and
                self.hcp >= 6 and
                self.opener_bid_two.level == 3 and
                self.stoppers_in_bid_suits and
                self.is_semi_balanced and
                self.nt_level <= 3)

    def _opener_repeats_major_at_level_three_balanced(self) -> bool:
        """Return True if opener repeats major at 3 level and balanced."""
        return (self.is_balanced and
                self.opener_bid_one.is_major and
                self.opener_bid_two.level == 3 and
                self.opener_suit_one == self.opener_suit_two and
                self.suit_length(self.opener_suit_two) <= 3 and
                self.stoppers_in_bid_suits and
                self.nt_level <= 3)

    def _can_support_openers_major(self) -> bool:
        """Return True if can support opener's major."""
        return (self.opener_bid_one.is_major and
                self.suit_length(self.opener_suit_one) >= 3 and
                not self.opener_bid_two.is_game)

    def _intermediate_balanced_cannot_rebid_suit(self) -> bool:
        """Return True if intermediate and balanced."""
        return (self.hcp >= 15 and
                self.is_balanced and
                (self.longest_suit.is_minor or
                 self.shape[0] == 4) and
                self.nt_level <= 3)

    def _opener_has_shown_six_card_suit(self) -> bool:
        """Return True if opener has shown a six card suit."""
        return (self.opener_suit_one == self.opener_suit_two and
                self.opener_bid_two.level == 3 and
                self.suit_length(self.opener_suit_one) >= 2 and
                self.longest_suit.is_minor)

    def _is_strong_can_show_second_suit(self) -> bool:
        """Return True if strong and can show second suit."""
        return (self.hcp >= 16 and
                self.shape[1] >= 4 and
                self.next_level(self.second_suit) <= 4 and
                self.second_suit not in self. opponents_suits)

    def _cannot_support_openers_first_suit(self) -> bool:
        """Return True if can support opener's first suit."""
        return (self.shape[1] >= 5 and
                self.suit_length(self.opener_suit_one) <= 4 and
                self.second_suit not in self.opponents_suits)

    def _no_support_but_nt_possible(self, suit_preference: Suit) -> bool:
        """Return True if no support but nt possible."""
        support_points = (self.support_points(self.opener_suit_one) +
                          self.support_points(self.opener_suit_two))
        return (self.hcp >= 7 and
                self.suit_length(suit_preference) <= 1 and
                self.nt_level <= 3 and
                support_points >= 4 and
                self.stoppers_in_bid_suits)

    def _has_five_four_and_can_show_second_suit(self) -> bool:
        """Return True if has 5/4 and can show second suit."""
        return (self.five_four and
                10 <= self.hcp <= 15 and
                self.next_level(self.second_suit) <= 2 and
                self.second_suit not in self.opponents_suits)

    def _support_for_openers_major_after_nt_opening(self) -> bool:
        """Return True if support for opener's major."""
        return (self.opener_bid_two.is_suit_call and
                self.hcp >= 12 and
                self.suit_length(self.opener_suit_two) >= 3 and
                self.opener_suit_two.is_major)

    def _is_balanced_intermediate_stoppers(self, suit_to_bid: Suit) -> bool:
        """Return True if balanced with 10 to 12 points and stoppers."""
        return (self.is_balanced and
                10 <= self.hcp <= 12 and
                self.stoppers_in_unbid_suits() and
                suit_to_bid.is_minor and self.nt_level <= 2)

    def _nt_can_support_minor(self) -> bool:
        """Return True if longest suit is openers opening minor."""
        return (self.opener_bid_two.name == '2NT' and
                self.opener_bid_one.is_minor and
                self.is_semi_balanced and
                self.nt_level <= 3 and
                self.longest_suit == self.opener_suit_one)

    def _has_six_card_suit_and_opening_points(self) -> bool:
        """Return True if long suit and opening values."""
        return (self.hcp >= 12 and
                self.shape[0] >= 6 and
                self.next_level(self.longest_suit) <= 3 and
                self.longest_suit not in self.opponents_suits)

    def _five_four_in_majors(self) -> bool:
        """Return True if 5/4 in the majors."""
        return (self.longest_suit.is_major and
                self.second_suit.is_major and
                self.five_four_or_better and
                self.second_suit not in self.opponents_suits and
                self.next_level(self.second_suit) <= 2)

    def _can_suppport_openers_major(self) -> bool:
        return (self.opener_suit_one == self.opener_suit_two and
                self.opener_suit_one.is_major and
                self.opener_bid_two.level == 3 and
                self.suit_length(self.opener_suit_one) >= 2 and
                self.hcp >= 11)

    def _four_card_major_or_better(self) -> bool:
        return (self.is_semi_balanced and
                self.nt_level <= 3 and
                self.four_card_major_or_better and
                self.next_level(self.club_suit) <= 3)
