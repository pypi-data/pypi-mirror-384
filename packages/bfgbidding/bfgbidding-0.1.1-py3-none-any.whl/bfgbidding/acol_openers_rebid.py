""" Bid for Game
    Acol OpenersReBid module
"""

import inspect
from bridgeobjects import Suit
from .bidding import Bid, Pass, Double
from .hand import Hand
from .blackwood import Blackwood

inspection = inspect.currentframe


class OpenersReBid(Hand):
    """BfG OpenersReBid class."""
    def __init__(self, hand_cards, board):
        super(OpenersReBid, self).__init__(hand_cards, board)
        self.trace = 0

    def suggested_bid(self) -> Bid:
        """Direct control to relevant method and return a Bid object."""
        if (self.responder_bid_one.name == '3NT' and
                self.shape[0] <= 5 and
                self.hcp <= 17):
            bid = Pass('1201')
        elif self.bid_one.is_nt:
            bid = self._rebid_after_nt_opening()
        elif self.responder_bid_one.is_pass:
            bid = self._responder_has_passed()
        elif self.responder_bid_one.name == '4NT':
            bid = Blackwood(self.cards, self.board).count_aces()
        elif self.bid_one.name == '2C':
            bid = self._rebid_after_two_club_opening()
        elif (self.bid_one.level == 2 and
              self.bid_one.is_suit_call):
            bid = self._rebid_after_weak_two()
        elif (self.overcall_made and
              self.responder_bid_one.level == 3):
            bid = self._responder_at_three_overcall()
        elif self.responder_bid_one.is_double:
            bid = self._responder_has_doubled()
        else:
            bid = self._rebid_after_suit_opening()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_has_passed(self) -> Bid:
        """Bid after responder has passed."""
        if self.overcall_made and self.bid_one.level == 1:
            bid = self._responder_pass_overcall()
        elif self.bid_history[-3:] == ['P', 'P', 'P']:
            bid = Pass('1204')
        else:
            if self.bid_one.name != '2C':
                bid = Pass('1432')
            else:
                bid = Pass('1442')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_after_nt_opening(self) -> Bid:
        """Rebid after NT opening."""
        if self.bid_one.name == '1NT':
            bid = self._rebid_after_one_nt_opening()
        elif self.bid_one.name == '2NT':
            bid = self._rebid_after_two_nt_opening()
        elif self.bid_one.name == '3NT':
            bid = Pass('0000')
        else:
            assert False, 'Bid not defined'
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_after_one_nt_opening(self) -> Bid:
        """Rebid after 1NT opening."""
        if self.responder_bid_one.is_game:
            bid = Pass('1207')
        elif self.responder_bid_one.name == 'NT':
            bid = self._after_two_nt_response()
        elif self.responder_bid_one.name == '2NT':
            bid = self._after_two_nt_response()
        elif self.overcaller_bid_one.is_double:
            bid = self._one_nt_is_doubled()
        elif self.responder_bid_one.name == '2C':
            bid = self._after_stayman_two_clubs()
        elif self.responder_bid_one.level == 2:
            bid = self._after_one_nt_at_level_two()
        elif self.responder_bid_one.level == 3:
            bid = self._after_one_nt_at_level_three()
        else:
            bid = Pass('1208')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_one_nt_at_level_two(self) -> Bid:
        """Rebid after 1NT opening, responder at level 2."""
        if self._three_card_support_for_responder_overcall_made():
            bid = self.next_level_bid(self.responder_bid_one.denomination, '1209')
        elif self._four_card_support_for_responder_overcall_made():
            bid = self.next_level_bid(self.responder_bid_one.denomination, '1210')
        else:
            bid = Pass('1211')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_one_nt_at_level_three(self) -> Bid:
        """Rebid after 1NT opening, responder at level 3."""
        if (self.responder_bid_one.name == '3H' or
                self.responder_bid_one.name == '3S'):
            bid = self._after_three_of_major_response()
        elif (self.five_card_major and
              self.longest_suit not in self.opponents_suits):
            bid = self.next_level_bid(self.longest_suit, '1212')
        elif self.nt_level <= 3 and self.stoppers_in_bid_suits:
            bid = self.nt_bid(3, '1213')
        elif self.longest_suit not in self.opponents_suits:
            bid = self.next_level_bid(self.longest_suit, '1214')
        else:
            bid = Pass('1219')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _one_nt_is_doubled(self) -> Bid:
        """Rebid after 1NT has been doubled."""
        if Bid(self.bid_history[-1]).is_value_call:
            bid = Pass('1219')
        elif self.responder_bid_one.is_value_call:
            bid = Pass('1217')
        else:
            bid = Pass('1218')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_stayman_two_clubs(self) -> Bid:
        """Rebid after Stayman 2C."""
        if self.overcaller_bid_one.is_double:
            bid = Pass('1219')
        elif self.nt_level >= 3:
            bid = Pass('1220')
        elif (self.hearts >= 4 and
              self.next_level(self.heart_suit) <= 2):
            bid = self.heart_bid(2, '1221')
        elif (self.spades >= 4 and
              self.next_level(self.spade_suit) <= 2):
            bid = self.spade_bid(2, '1222')
        elif self.next_level(self.diamond_suit) <= 2:
            bid = self.diamond_bid(2, '1223')
        elif self.opener_bid_one.name != '1NT' or self.stoppers_in_bid_suits:
            bid = self.nt_bid(2, '1224')
        else:
            bid = Pass('1375')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_stayman_three_clubs(self) -> Bid:
        """Rebid after Stayman."""
        # if self.overcaller_bid_one.is_double:
        #     bid = Pass('1226')
        if (self.overcall_made and self.nt_level > 3 and
                not self.overcaller_bid_one.is_double):
            bid = Pass('1227')
        elif (self.hearts >= 4 and
              self.next_level(self.heart_suit) <= 3):
            bid = self.heart_bid(3, '1228')
        elif (self.spades >= 4 and
              self.next_level(self.spade_suit) <= 3):
            bid = self.spade_bid(3, '1229')
        elif self.next_level(self.diamond_suit) <= 3:
            bid = self.diamond_bid(3, '1230')
        elif self.opponents_have_bid:
            bid = Pass('1448')
        else:
            bid = Pass('1447')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_after_two_nt_opening(self) -> Bid:
        """Rebid after 2NT opening."""
        if self.responder_bid_one.name == '3NT':
            bid = Pass('1232')
        elif self.bid_one.name == '2NT' and self.responder_bid_one.name == '4NT':
            if self.hcp == 22:
                bid = self.nt_bid(6, '1233')
            else:
                bid = Pass('1234')
        elif self.responder_bid_one.name == '3C':
            bid = self._after_stayman_three_clubs()
        elif (self.suit_length(self.responder_bid_one.denomination) >= 3 and
                not self.bidding_above_game):
            bid = self.bid_to_game(self.responder_bid_one.denomination, '1235')
        elif (self.responder_bid_one.is_suit_call and
                self.nt_level <= 3):
            bid = self.nt_bid(3, '1236')
        else:
            bid = Pass('1428')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_pass_overcall(self) -> Bid:
        """Rebid after an overcall and responder has passed."""
        (first_suit, second_suit) = self._get_best_suits()
        level = self.next_level(first_suit)
        if self.hcp >= 19:
            bid = self._respond_with_power(first_suit, second_suit)
        elif self._is_strong_with_five_five(second_suit):
            bid = self.next_level_bid(second_suit, '1239')
        elif self._strong_with_second_suit(level):
            bid = self.next_level_bid(second_suit, '1240')
        elif self._six_card_suit_weak():
            bid = self.next_level_bid(first_suit, '1241')
        elif self._is_strong_with_five_four(second_suit):
            bid = self.next_level_bid(second_suit, '1242')
        elif self._repeatable_five_card_suit():
            if self.hcp >= 18 and self.shape[0] >= 6 and self.overcaller_in_second_seat:
                raise_level = 1
            else:
                raise_level = 0
            bid = self.next_level_bid(first_suit, '1243', raise_level=raise_level)
        elif self._strong_and_balanced():
            bid = self.next_nt_bid('1244')
        elif self.hcp >= 16 and self.shape[0] >= 6:
            suit = self._select_suit_if_six_four()
            bid = self.next_level_bid(suit, '1245')
        else:
            bid = self._responder_pass_overcall_weak()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_pass_overcall_weak(self) -> Bid:
        """Rebid after an overcall and responder has passed weakish hand."""
        first_suit = self.longest_suit
        if self._weak_five_four():
            bid = self._weak_five_four_bid()
        elif self._weak_six_cards():
            bid = self.next_level_bid(first_suit, '1246')
        elif self.five_five and self.nt_level <= 3:
            bid = self._five_five_rebid()
        elif self._can_rebid_five_card_suit_at_two_level():
            bid = self.next_level_bid(self.longest_suit, '1247')
        elif self._can_rebid_seven_card_suit_at_three_level():
            bid = self.next_level_bid(self.longest_suit, '1248')
        else:
            bid = Pass('1249')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _weak_five_four_bid(self) -> Bid:
        """Return bid if weak but biddable 5/4."""
        barrier_will_be_broken = self.barrier_is_broken(self.bid_one,
                                                        self.next_level_bid(self.second_suit))
        will_be_jump_bid = self.is_jump(self.bid_one,
                                        self.next_level_bid(self.longest_suit))
        if will_be_jump_bid:
            bid = Pass('1250')
        elif barrier_will_be_broken:
            bid = self.next_level_bid(self.longest_suit, '1251')
        else:
            bid = self.next_level_bid(self.second_suit, '1252')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _five_five_rebid(self) -> Bid:
        """Bid with 5/5 hand"""
        suit = self._other_five_card_suit()
        if self._overcaller_doubled_and_advancer_bid():
            bid = Pass('1253')
        elif self.next_level(suit) > 3:
            bid = Pass('1254')
        elif suit == self.bid_one.denomination and self.hcp <= 13:
            bid = Pass('1255')
        elif suit not in self.opponents_suits and self.hcp >= 12:
            bid = self.next_level_bid(suit, '1256')
        else:
            bid = Pass('1258')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _respond_with_power(self, first_suit: Suit, second_suit: Suit) -> Bid:
        """Rebid after an overcall and responder has passed 19+ points."""
        if self.six_four:
            bid = self._powerful_six_four_bid(first_suit, second_suit)
        elif self.five_four_or_better:
            if second_suit not in self.opponents_suits:
                suit = second_suit
            else:
                suit = first_suit
            bid = self._powerful_five_four_bid(suit)
        elif self.stoppers_in_bid_suits and self.nt_level <= 3:
            bid = self.next_nt_bid('1259')
        else:
            bid = Double('1260')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _powerful_six_four_bid(self, first_suit: Suit, second_suit: Suit) -> Bid:
        """Bid powerful hand with 6/4."""
        first_suit_points = self.suit_points(first_suit)
        second_suit_points = self.suit_points(second_suit)
        if first_suit_points > second_suit_points+1:
            suit = first_suit
        else:
            suit = second_suit
        if suit in self.opponents_suits:
            if suit == first_suit:
                suit = second_suit
            else:
                suit = first_suit
        if (self.next_level(suit) <= 2 and
                (suit == self.opener_suit_one or
                 suit.rank < self.opener_suit_one.rank)):
            raise_level = 1
        else:
            raise_level = 0
        bid = self.next_level_bid(suit, '1261', raise_level)
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _powerful_five_four_bid(self, second_suit: Suit) -> Bid:
        """Bid powerful hand with 5/4."""
        suit = second_suit
        raise_level = 0
        trial_bid = self.next_level_bid(suit, '1433', raise_level)
        level = trial_bid.level
        if ((trial_bid.level <= 3 and
             self.responder_bid_one.is_value_call and
             not self.overcall_made) or
                self.hcp >= 22):
            level = 3
        next_level = self.next_level(suit)
        level = max(next_level, level)
        bid = self.suit_bid(level, suit, '1263')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_after_two_club_opening(self) -> Bid:
        """Bid after a two club opening."""
        if self.is_balanced:
            bid = self._balanced_after_two_clubs()
        else:
            bid = self._rebid_no_support()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _balanced_after_two_clubs(self) -> Bid:
        """Bid with a balanced hand after two club opening."""
        if self.responder_bid_one.name == '2NT':
            bid = self.nt_bid(3, '1429')
        else:
            bid = self._balanced_two_clubs_responder_with_values()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _balanced_two_clubs_responder_with_values(self) -> Bid:
        """Bid with a balanced hand after two club opening with support."""
        responders_suit = self.responder_bid_one.denomination
        if self.hcp >= 28:
            bid = self.nt_bid(4, '1265')
        elif self.responder_bid_one.is_major and self.suit_length(responders_suit) >= 3:
            bid = self.next_level_bid(responders_suit, '1266')
        elif ((self.hcp >= 25 or self.responder_bid_one.level == 3) and
              self.nt_level <= 3):
            bid = self.nt_bid(3, '1316')
        elif self.nt_level <= 2:
            bid = self.nt_bid(2, '1268')
        elif (self.overcaller_bid_one.is_suit_call and
                self.is_semi_balanced and self.stoppers_in_bid_suits):
            bid = self.nt_bid(3, '1431')
        else:
            bid = Pass('1269')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_after_weak_two(self) -> Bid:
        """Rebid after a weak two opening."""
        if self.responder_bid_one.denomination == self.bid_one.denomination:
            bid = Pass('1270')
        else:
            bid = self._rebid_after_suit_opening()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_two_nt_response(self) -> Bid:
        """Rebid after 2NT response from responder."""
        if self.five_card_major and self.longest_suit not in self.opponents_suits:
            bid = self.next_level_bid(self.longest_suit, '1271')
        elif self.nt_level <= 3:
            bid = self._after_two_nt_response_bid_nt()
        else:
            bid = Pass('1272')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_two_nt_response_bid_nt(self) -> Bid:
        """Rebid after 2NT response from responder, bid NT."""
        if (self.hcp == 13 and (self.shape[0] == 5 or
                                self.tens_and_nines >= 4)):
            bid = self.nt_bid(3, '1273')
        elif self.hcp == 14:
            bid = self.nt_bid(3, '1274')
        else:
            bid = Pass('1275')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_three_of_major_response(self) -> Bid:
        """Rebid after 3 major response."""
        suit = self.responder_bid_one.denomination
        level = self.next_level(suit)
        if self.responder_bid_one.name == '3H' and self.hearts >= 3 and level <= 4:
            bid = self.heart_bid(4, '1276')
        elif self._can_rebid_spades(level):
            bid = self.spade_bid(4, '1277')
        elif self.nt_level <= 3:
            bid = self.nt_bid(3, '1278')
        elif self.nt_level >= 4:
            bid = Pass('1434')
        else:
            bid = Pass('1445')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_after_suit_opening(self) -> Bid:
        """Rebid after suit opening."""
        if self.responder_bid_one.is_nt:
            bid = self._rebid_after_nt_response()
        elif self._responder_shows_support_or_can_support_responder():
            bid = self._after_suit_opening_support()
        else:
            bid = self._rebid_no_support()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _after_suit_opening_support(self) -> Bid:
        """Rebid after suit opening with support."""
        if self.responder_bid_one.is_minor and self.is_balanced:
            bid = self._rebid_no_support()
        else:
            bid = self._rebid_with_support()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_after_nt_response(self) -> Bid:
        """Rebid after NT response."""
        if self._responder_has_bid_nt_game_over_minor():
            bid = Pass('1281')
        elif self._is_shapely_intermediate_hand():
            bid = self._rebid_no_support()
        else:
            bid = self._support_nt()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _support_nt(self) -> Bid:
        """Support NT bid from partner."""
        if self.responder_bid_one.name == '1NT':
            bid = self._support_one_nt()
        elif self.responder_bid_one.name == '2NT':
            bid = self._support_two_nt()
        elif self.responder_bid_one.name == '3NT':
            bid = Pass('1282')
        else:
            bid = Pass('1435')  # TODO Should not reach
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _support_one_nt(self) -> Bid:
        """Respond to 1NT bid from partner."""
        old_level = self.responder_bid_one.level
        level = self.quantitative_raise(self.hcp, old_level, [16, 19], 3)
        if self.hcp >= 16 and self.nt_level <= level:
            bid = self.nt_bid(level, '1284')
        elif self.shape[0] >= 5 and (self.last_bid.is_pass or self.shape[0] >= 6):
            bid = self._rebid_no_support()
        elif self.hcp >= 13 and self.overcall_made:
            bid = self._rebid_no_support()
        elif self.is_balanced:
            bid = Pass('1285')
        else:
            bid = Pass('1286')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _support_two_nt(self) -> Bid:
        """Support 2NT bid from partner."""
        if self.hcp >= 15 and self.nt_level <= 3:
            bid = self.nt_bid(3, '1287')
        else:
            bid = Pass('1288')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_with_support(self) -> Bid:
        """Rebid after suit decided."""
        if self.bid_one.is_suit_call:
            change_suit = (self.responder_bid_one.denomination != self.bid_one.denomination and
                           self.responder_bid_one.denomination.is_suit and
                           self.bid_one.denomination.is_suit)
        else:
            change_suit = None
        if change_suit:
            bid = self._opener_can_support_responder()
        else:
            bid = self._rebid_support_no_suit_changes()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_support_no_suit_changes(self) -> Bid:
        """Rebid responder supports opener."""
        if self.responder_bid_one.level == 4:
            if (self.hcp >= 19 or
                    (self.hcp >= 17 and self.bid_one.denomination.is_major)):
                if self.nt_level <= 4:
                    bid = self.nt_bid(4, '1289')
                else:
                    bid = self.next_level_bid(self.responder_bid_one.denomination, '1290')
            elif self.hcp >= 16:
                bid = self.next_level_bid(self.responder_bid_one.denomination, '1291')
            else:
                bid = Pass('1292')
        elif self.responder_bid_one.level >= 3:
            bid = self._support_at_level_three()
        elif self.responder_bid_one.level >= 2:
            bid = self._support_at_level_two()
        else:
            bid = Pass('1436')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _support_at_level_three(self) -> Bid:
        """Rebid with support and no suit changes at level 3."""
        next_level = self.next_level(self.responder_bid_one.denomination)
        if (self.responder_bid_one.denomination.is_major and self.hcp >= 14 and
                next_level <= 4):
            bid = self.bid_to_game(self.responder_bid_one.denomination, '1294')
        elif (self.responder_bid_one.denomination.is_minor and self.hcp >= 16 and
              next_level <= 5):
            bid = self.bid_to_game(self.responder_bid_one.denomination, '1295')
        else:
            bid = Pass('1296')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _support_at_level_two(self) -> Bid:
        """Rebid with support and no suit changes at level 2."""
        agreed_suit = self.my_last_bid.denomination
        next_level = self.next_level(agreed_suit)
        game_bid = self.bid_to_game(agreed_suit)
        if self.hcp >= 19 and next_level <= game_bid.level:
            bid = self.bid_to_game(agreed_suit, '1297')
        elif self._has_six_card_minor_and_eighteen_points():
            bid = self.nt_bid(3, '1298')
        elif self.hcp >= 16 and next_level <= 4:
            bid = self.next_level_bid(agreed_suit, '1299')
        elif self.overcall_made and self.hcp >= 15 and next_level <= 3:
            bid = self.next_level_bid(agreed_suit, '1300')
        elif self.shape[0] >= 7:
            bid = self.next_level_bid(agreed_suit, '1301')
        elif self.hcp >= 14 and self.shape[0] >= 5 and not self.right_hand_bid.is_pass:
            bid = self.next_level_bid(agreed_suit, '1302')
        elif self.shape[0] >= 6 and self.shape[1] >= 5:
            bid = self.next_level_bid(self.longest_suit, '1303')
        else:
            bid = Pass('1304')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_can_support_responder(self) -> Bid:
        """Return bid when opener supports responder."""
        suit_to_bid = self._get_suit_support_for_responder()
        level = self._get_level_with_support(suit_to_bid)
        next_level = self.next_level_bid(suit_to_bid).level
        level = max(level, next_level)
        responder_has_jumped = (self.is_jump(self.bid_one, self.responder_bid_one))

        if self.hcp >= 16 and responder_has_jumped and self.overcaller_bid_one.is_pass:
            bid = self._opener_can_support_responder_strong(suit_to_bid)
        elif suit_to_bid.is_no_trumps:
            bid = Pass('1305')
        elif self.suit_length(suit_to_bid) <= 3:
            if self.responder_bid_one.level == 2 and self.hcp >= 14:
                bid = self.next_level_bid(suit_to_bid, '1306', raise_level=1)
            else:
                bid = self.next_level_bid(suit_to_bid, '1307')
        elif self._is_unbalanced_with_sixteen_points():
            bid = self._medium_unbalanced_hand()
        elif level >= next_level:
            bid = self.suit_bid(level, suit_to_bid, '1308', use_shortage_points=True)
        else:
            bid = Pass('1437')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _medium_unbalanced_hand(self) -> Bid:
        """Return bid with 16+ points and unbalanced."""
        if self.overcall_made:
            raise_level = 0
        else:
            raise_level = 1
        if self._can_support_nineteen_points():
            bid = self.bid_to_game(self.second_suit, '1310')
        elif self._can_support_seventeen_points_and_void():
            bid = self.bid_to_game(self.responder_bid_one.denomination, '1311')
        elif self._fffo_strong_four_card_support():
            bid = self.bid_to_game(self.responder_bid_one.denomination, '1312')
        elif self._no_biddable_second_suit_and_support_for_partner():
            bid = self.bid_to_game(self.responder_bid_one.denomination, '1313')
        elif self.second_suit == self.responder_bid_one.denomination:
            bid = self.next_level_bid(self.second_suit, '1316', raise_level=raise_level)
        else:
            bid = self.next_level_bid(self.second_suit, '1315', raise_level=raise_level)
            # if bid.level > self.game_level(self.second_suit):
            #     bid = Double('9999')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _opener_can_support_responder_strong(self, suit_to_bid):
        """Return bid when opener supports responder and 16+ points."""
        if self.hcp >= 16 and suit_to_bid.is_major:
            if self.responder_bid_one.level == 3:
                bid = self.nt_bid(4, '1317')
            else:
                bid = self.nt_bid(2, '1354')
        else:
            bid = self.next_level_bid(suit_to_bid, '1319')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_no_support(self) -> Bid:
        """Rebid with no responder support."""
        trial_bid = self._five_four_rebids()
        if self.bid_one.name == '2C':
            bid = trial_bid
        elif self.is_balanced:
            bid = self._no_support_balanced()
        elif self._has_strong_minor_responder_has_jumped():
            bid = self.nt_bid(4, '1430')
        elif self.shape[0] >= 7:
            bid = self._single_suited_rebids()
        elif self.five_five:
            bid = self._no_support_five_five()
        elif self._competitive_auction_weak_with_minor() and trial_bid.level >= 3:
            bid = Pass('1321')
        # elif self._competitive_auction_with_support_for_responder():
        #     bid = self._rebid_partners_major()
        elif self.five_four or self.five_five_or_better:
            bid = self._five_four_rebids()
        elif self.shape[0] >= 6:
            bid = self._single_suited_rebids()
        elif self.shape == [4, 4, 4, 1]:
            bid = self._four_four_four_one_bid()
        else:
            bid = Pass('1438')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _no_support_five_five(self) -> Bid:
        """Rebid with no responder support and 5/5 hand."""
        suit_to_bid = self._get_suit_no_support_five_five()
        raise_level = 1
        level = min(self.next_level(suit_to_bid, raise_level=raise_level), 3)

        if self._suit_is_major_and_eighteen_points(suit_to_bid):
            if self.responder_bid_one.is_nt:
                bid = self.suit_bid(4, suit_to_bid, '1324')
            else:
                bid = self.suit_bid(level, suit_to_bid, '1325')
        elif self.next_level(suit_to_bid) <= 3 and self.hcp >= 16:
            bid = self.suit_bid(level, suit_to_bid, '1326')
        elif self._five_in_opponents_suits():
            bid = Pass('1327')
        elif (self.responder_bid_one.name != '2NT' and
                (self.next_level(suit_to_bid) <= 2 or
                 self.hcp >= 15 or
                 self.overcaller_bid_one.denomination == self.advancer_bid_one.denomination)):
            bid = self.next_level_bid(suit_to_bid, '1328')
        else:
            bid = Pass('1329')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _no_support_balanced(self) -> Bid:
        """Bid with no support and balanced hand."""
        level = self.next_level(self.bid_one.denomination)
        if self.hcp >= 19:
            bid = self._bid_with_19_points()
        elif self.hcp >= 15 or level > 2:
            bid = self._invitational_bid()
        else:
            bid = self.next_level_bid(self.bid_one.denomination, '1332')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _bid_with_19_points(self) -> Bid:
        """Return bid with a 19 point hand."""
        unbid_major = self.unbid_four_card_major()
        if self._powerful_and_has_four_cards_in_unbid_major(unbid_major):
            bid = self.next_level_bid(unbid_major, '1333', raise_level=1)
        elif self._responder_support_with_jump():
            bid = self.nt_bid(3, '1334')
        elif (self.hcp >= 17 and self.is_jump(self.bid_one,
                                              self.responder_bid_one) and
                self.nt_level <= 6):
            bid = self.nt_bid(6, '1335')
        elif self.nt_level <= 3:
            bid = self.nt_bid(3, '1336')
        else:
            bid = Pass('1337')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _invitational_bid(self) -> Bid:
        """Return bid with 15+ points or partner has 10+ points."""
        if self.stoppers_in_bid_suits:
            bid = self._rebid_balanced_hand()
        elif self.shape[1] >= 4 and self.hcp >= 16 and self.second_suit not in self.opponents_suits:
            bid = self.next_level_bid(self.second_suit, '1338')
        elif self.shape[0] < 5:
            bid = self._opener_can_support_responder()
        else:
            bid = self._single_suited_rebids()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _five_four_rebids(self) -> Bid:
        """Rebid with 5/4 hands."""
        responder_jumped = self.jump_bid_made(self.responder_bid_one)
        suit_to_bid = self._get_suit_with_five_four()
        test_bid = self.next_level_bid(suit_to_bid)
        cannot_show_second_suit = self.barrier_is_broken(self.bid_one, test_bid)
        if self._weak_and_able_to_repeat_suit(cannot_show_second_suit, responder_jumped):
            suit_to_bid = self.bid_one.denomination

        if self.hcp >= 16:
            bid = self._five_four_strong(suit_to_bid)
        else:
            bid = self._five_four_weak(suit_to_bid, cannot_show_second_suit)
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _five_four_strong(self, suit_to_bid):
        """Bid with strong hand."""
        if self.bid_one.name == '2C':
            bid = self._rebid_after_two_clubs()
        elif self.five_five:
            suit_to_bid = self.longest_suit
            if self.hcp >= 16:
                raise_level = 1
            else:
                raise_level = 0
            bid = self.next_level_bid(suit_to_bid, '1439', raise_level)
        else:
            bid = self._five_four_strong_balanced(suit_to_bid)
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _five_four_strong_balanced(self, suit_to_bid: Suit) -> Bid:
        """Bid with strong 5/4 hand."""
        test_bid = self.next_level_bid(suit_to_bid)
        if self._five_four_strong_test_nt(test_bid):
            bid = self.nt_bid(3)
        elif self._can_repeat_suit_and_seventeen_points(suit_to_bid):
            bid = self._five_four_strong_nt()
        elif self._has_five_four_and_sixteen_points(suit_to_bid):
            second_suit = self._get_second_suit_for_opener()
            bid = self.next_level_bid(second_suit, '1342')
        else:
            raise_level = self._raise_level_with_five_four_strong(suit_to_bid, test_bid)
            if (self.next_level(suit_to_bid, raise_level) > 3 or
                    (self.responder_bid_one.name == '1NT' and self.hcp <= 16)):
                raise_level = 0
            bid = self.next_level_bid(suit_to_bid, '1343', raise_level)
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _five_four_strong_nt(self) -> Bid:
        """Bid with strong 5/4 hand try NT."""
        if self.hcp >= 19 and self.nt_level <= 3:
            bid = self.nt_bid(3, '1344')
        # elif self.(_can_bid_three_nt):
        #     bid = self.nt_bid(3, '1345')
        elif self._can_bid_two_nt():
            bid = self.nt_bid(2, '1346')
        # elif self.nt_level <= 1:
        #     bid = self.nt_bid(1, '1347')
        elif self.nt_level <= 3:
            if self.second_suit in self.opponents_suits:
                suit_to_bid = self.longest_suit
            else:
                suit_to_bid = self.second_suit
            bid = self.next_level_bid(suit_to_bid, '1348')
        elif self.nt_level >= 4:
            bid = Pass('1440')
        else:
            bid = Pass('1446')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_after_two_clubs(self) -> Bid:
        """Return bid after a 2C opening."""
        if self.is_semi_balanced and self.hcp >= 25 and self.nt_level <= 3:
            bid = self.nt_bid(3, '1349')
        # elif self.is_balanced:
        #     bid = self.next_nt_bid('1350')
        # elif self.responder_bid_one.name == '2D' and self.longest_suit == self.diamond_suit:
        #     bid = Pass('1351')
        elif self.responder_bid_one.name == '2D':
            bid = self.next_level_bid(self.longest_suit, '1352')
        elif self.suit_length(self.responder_bid_one.denomination) >= 3:
            if (self.hcp + self.suit_length(self.responder_bid_one.denomination) >= 26 and
                    self.nt_level <= 4):
                bid = self.nt_bid(4, '1353')
            else:
                bid = self.bid_to_game(self.responder_bid_one.denomination, '1354')
        elif self.longest_suit.is_minor and self.responder_bid_one.denomination.is_minor:
            bid = self.next_nt_bid('1355')
        else:
            bid = self.next_level_bid(self.longest_suit, '1356')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _five_four_weak(self, suit, cannot_show_second_suit: bool) -> Bid:
        """Bid with weak 5/4 hand."""
        suit_to_bid = self._five_four_weak_suit(suit, cannot_show_second_suit)
        level = self.next_level(suit)
        if self._weak_five_four_with_weak_suit(suit_to_bid):
            bid = Pass('1357')
        elif self._weak_five_four_consider_bid(level):
            bid = self._five_four_weak_bid(suit_to_bid, cannot_show_second_suit)
        elif self._can_bid_at_appropriate_level(suit_to_bid, level):
            bid = self.next_level_bid(suit_to_bid, '1358')
        elif self.bid_history[-1] == 'P':
            bid = self.next_level_bid(self.longest_suit, '1362')
        else:
            bid = Pass('1360')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _five_four_weak_bid(self, suit_to_bid, cannot_show_second_suit: bool) -> Bid:
        """Return bid if a sound bid is possible."""
        overcall = Bid(self.bid_history[-1])
        trial_bid = self.next_level_bid(suit_to_bid)
        if trial_bid.level >= 3 or (not overcall.is_value_call):
            bid = self._five_four_weak_invitational(suit_to_bid, cannot_show_second_suit)
        elif self.hcp <= 11:
            bid = Pass('1362')
        elif self.hcp <= 12 and cannot_show_second_suit:
            bid = Pass('1363')
        else:
            bid = self.next_level_bid(suit_to_bid, '1364')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _five_four_weak_invitational(self, suit_to_bid: Suit, cannot_show_second_suit: bool) -> Bid:
        """Return bid with 5/4 hand and next level is 3."""
        if self.bid_one.level == 2:
            bid = Pass('1365')
        elif self.next_level(suit_to_bid) <= 2 and self.shape[0] >= 6:
            if self.shape[0] >= 7 and self.hcp >= 13:
                raise_level = 1
            else:
                raise_level = 0
            bid = self.next_level_bid(suit_to_bid, '1366', raise_level=raise_level)
        elif self._weak_after_one_nt_and_barrier_broken(cannot_show_second_suit):
            bid = Pass('1367')
        elif self._six_four_responder_at_level_two():
            bid = self.next_level_bid(self.second_suit, '1368')
        elif self._weak_overcall_responder_level_one() and cannot_show_second_suit:
            bid = Pass('1369')
        elif self._can_bid_second_suit_after_nt():
            bid = self.next_level_bid(self.second_suit, '1370')
        elif self.hcp <= 12 and cannot_show_second_suit:
            bid = self.next_level_bid(self.bid_one.denomination, '1371')
        elif self._strong_or_can_bid_at_level_two(suit_to_bid):
            bid = self.next_level_bid(suit_to_bid, '1372')
        elif self._strong_five_four_or_better():
            bid = self.next_level_bid(self.second_suit, '1375')
        else:
            bid = Pass('1376')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _single_suited_rebids(self) -> Bid:
        """Return bid with single suited hands."""
        if self.hcp >= 18 or self.shape[0] >= 8:
            bid = self._single_suited_rebids_strong()
        elif self.hcp >= 16:
            bid = self._single_suited_intermediate()
        else:
            bid = self._single_suited_rebids_weak()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _single_suited_rebids_strong(self) -> Bid:
        """Return bid with strong single suited hands."""
        suit = self.longest_suit
        level = self.next_level(suit)
        if suit.is_major:
            bid = self._single_suited_strong_major(suit, level)
        else:
            level = self.next_level(suit)
            level = max(3, level)
            bid = self.suit_bid(level, suit, '1377')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _single_suited_strong_major(self, suit: Suit, level: int) -> Bid:
        """Return bid with strong single major suited hands."""
        level = max(4, level)
        if self.shape[0] <= 5 and self.nt_level <= 3:
            bid = self.nt_bid(3, '1378')
        elif level <= 5:
            bid = self.suit_bid(level, suit, '1379')
        else:
            bid = Pass('1380')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _single_suited_intermediate(self) -> Bid:
        """Return bid with intermediate single suited hands."""
        if self.hcp == 19:
            nt_level = 3
        elif self.hcp >= 17 or self.nt_level == 2:
            nt_level = 2
        else:
            nt_level = 1
        if self._is_strong_with_seven_card_major():
            bid = self.bid_to_game(self.longest_suit, '1381')
        elif self._is_strong_six_four_with_major():
            bid = self.next_level_bid(self.second_suit, '1382')
        elif self.shape[0] <= 5 and self.longest_suit.is_minor and self.nt_level <= nt_level:
            bid = self.nt_bid(nt_level, '1383')
        else:
            if self._weak_with_overcall_or_next_level_three():
                raise_level = 0
            else:
                raise_level = 1
            bid = self.next_level_bid(self.longest_suit, '1384', raise_level)
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _single_suited_rebids_weak(self) -> Bid:
        """Return bid with weak single suited hands."""
        if ((self.overcall_made == self.overcaller_position['fourth_seat']) and
                not self.responders_support):
            bid = self._single_suited_weak_competitive()
        else:
            bid = self._single_suited_uncontested()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _single_suited_uncontested(self) -> Bid:
        """Return bid with weak single suited hands in uncontested auction."""
        if self.responder_bid_one.is_game:
            bid = Pass('1385')
        elif self._has_six_card_major_and_responder_bid_one_nt():
            bid = self.suit_bid(2, self.longest_suit, '1387')
        elif self._has_six_card_major_and_responder_bid_two_nt():
            if ((self.shape[0] >= 7 and self.next_level(self.longest_suit) <= 3) or
                    (self.shape[0] == 6 and self.hcp >= 14 and
                     self.next_level(self.longest_suit) <= 4)):
                level = 4
            else:
                level = self.next_level(self.longest_suit)
            bid = self.suit_bid(level, self.longest_suit, '1388')
        elif self.responder_bid_one.name == '1NT' and self.hcp <= 15 and self.shape[0] <= 5:
            bid = Pass('1389')
        elif self.shape[0] >= 6 and self.longest_suit.is_major and self.hcp >= 12:
            if self.shape[0] >= 7 and self.hcp >= 13 and self.next_level(self.longest_suit) <= 2:
                raise_level = 1
            else:
                raise_level = 0
            bid = self.next_level_bid(self.longest_suit, '1390', raise_level)
        elif self._can_bid_three_nt():
            bid = self.next_nt_bid('1391')
        elif (self.responder_bid_one.level >= 3 and
              self.suit_length(self.responder_bid_one.denomination) >= 3):
            bid = self.next_level_bid(self.responder_bid_one.denomination, '1392')
        elif self.hcp <= 9:
            bid = Pass('1393')
        else:
            bid = self.next_level_bid(self.longest_suit, '1394')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _single_suited_weak_competitive(self) -> Bid:
        """Return bid with weak single suited hands in competitive auction."""
        if self._is_strong_with_solid_seven_card_suit():
            bid = self.next_level_bid(self.longest_suit, '1395')
        elif self._has_five_card_suit_fifteen_points_level_two():
            bid = self.next_level_bid(self.longest_suit, '1396')
        elif self._has_seven_card_suit_and_weak():
            bid = self.next_level_bid(self.longest_suit, '1397')
        elif self.shape[0] >= 6 and self.next_level(self.longest_suit) <= 2:
            bid = self.next_level_bid(self.longest_suit, '1398')
        elif self._has_six_card_suit_responder_at_level_two():
            bid = self.next_level_bid(self.longest_suit, '1399')
        else:
            bid = Pass('1400')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _four_four_four_one_bid(self) -> Bid:
        """Rebid with 4441 hands."""
        singleton_suit = self.suit_shape[3]
        if self.responder_bid_one.denomination == singleton_suit:
            bid = self._fffo_partner_bids_singleton()
        else:
            bid = self._rebid_with_support()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _fffo_partner_bids_singleton(self) -> Bid:
        """Rebid with 4441 hands after partner bids singleton suit."""
        suit = self._select_suit_for_four_four_four_one()
        if self.responder_bid_one.level == 1:
            level = self.quantitative_raise(self.hcp, 0, [15, 17, 19], 3)
        else:
            level = self.quantitative_raise(self.hcp, 0, [12, 13, 15], 3)
        test_bid = self.next_level_bid(suit, '1401', False)
        if self._has_fifteen_points_and_level_is_one(level):
            bid = self.nt_bid(level, '1402')
        elif self._barrier_would_break_and_fewer_that_sixteen(suit, test_bid):
            bid = Pass('1403')
        else:
            bid = test_bid
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _rebid_balanced_hand(self) -> Bid:
        """Return bid with a balanced hand."""
        bid_level = self._balanced_bid_level()
        if self._strong_can_bid_nt(bid_level):
            comment = ['1405', '1406', '1407'][bid_level - 1]
            bid = self.nt_bid(bid_level, comment)
        # elif self._no_fit_fifteen_points_responder_level_two():
        #     bid = self.nt_bid(3, '1408')
        elif (self.hcp >= 15 and self.is_balanced and
              self.stoppers_in_unbid_suits() and self.nt_level == 1):
            bid = self.nt_bid(1, '1409')
        else:
            bid = Pass('1410')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_at_three_overcall(self) -> Bid:
        """Return bid after responder jumped to 3 level after an overcall."""
        if self.responder_bid_one.name == '3NT':
            bid = self._responder_at_three_nt_overcall()
        else:
            bid = self._at_three_overcall_suit()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _at_three_overcall_suit(self) -> Bid:
        """Return bid after responder jumped to 3 of a suit after overcall."""
        if self.bid_one.denomination == self.responder_bid_one.denomination:
            bid = self._at_three_overcall_support()
        elif self._is_balanced_or_no_fit_with_responder():
            bid = self.nt_bid(3, '1411')
        else:
            bid = self._at_three_overcall_no_support()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_at_three_nt_overcall(self) -> Bid:
        """Return bid after responder has jumped to 3NT after an overcall."""
        if self.hcp >= 18 and self.nt_level <= 4:
            bid = self.nt_bid(4, '1412')
        elif self._has_six_card_major_and_can_bid_game():
            bid = self.suit_bid(4, self.longest_suit, '1413')
        else:
            bid = Pass('1414')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _at_three_overcall_support(self) -> Bid:
        """Return bid with 3 level support after an overcall."""
        if self.hcp >= 14:
            bid = self._overcall_support_strong()
        else:
            bid = Pass('1415')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _overcall_support_strong(self) -> Bid:
        """Return bid with 3 level support after overcall with strong hand."""
        hvp = self.support_points(self.bid_one.denomination)
        if self.bid_one.denomination.is_minor and hvp >= 18:
            bid = self._at_three_overcall_support_minor()
        elif self._is_balanced_minor_suit_can_bid_nt_game():
            bid = self.nt_bid(3, '1416')
        elif self.next_level(self.bid_one.denomination) <= 4:
            bid = self.suit_bid(4, self.bid_one.denomination, '1417')
        else:
            bid = Pass('1418')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _at_three_overcall_support_minor(self) -> Bid:
        """Return bid with 3 level support after overcall with strong minor."""
        if self._is_balanced_can_bid_nt_game():
            bid = self.nt_bid(3, '1419')
        elif self.next_level(self.bid_one.denomination) <= 5:
            bid = self.suit_bid(5, self.bid_one.denomination, '1420')
        else:
            bid = Pass('1421')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _at_three_overcall_no_support(self) -> Bid:
        """Return bid with no support, responder at 3 after overcall."""
        if self._has_six_card_major_and_can_bid_at_three_level():
            bid = self.suit_bid(3, self.bid_one.denomination, '1422')
        else:
            bid = self._overcall_no_support_minor()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _overcall_no_support_minor(self) -> Bid:
        """Return bid with no support, minor suit, after overcall."""
        responders_suit = self.responder_bid_one.denomination
        next_level = self.next_level(responders_suit)
        level = '4'
        if responders_suit.is_minor and self.hcp >= 15:
            level = '5'
        if (self.five_five and
                self.second_suit not in self.opponents_suits):
            bid = self.next_level_bid(self.second_suit, '1423')
        elif int(level) >= next_level:
            bid = self.suit_bid(level, responders_suit, '1424')
        else:
            bid = Pass('1441')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _responder_has_doubled(self) -> Bid:
        """Return bid after responder has doubled."""
        if (self.suit_length(self.second_suit) >= 4 and
                self.second_suit not in self.opponents_suits):
            bid = self.next_level_bid(self.second_suit, '1426')
        else:
            bid = self.next_level_bid(self.longest_suit, '1427')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    # Various utility functions

    def _get_second_suit_for_opener(self) -> Suit:
        """Return suit to bid after overcall."""
        if self.shape == [5, 4, 4, 0]:
            if self.second_suit not in self.opponents_suits:
                suit = self.second_suit
            elif self.third_suit not in self.opponents_suits:
                suit = self.third_suit
            else:
                suit = self.longest_suit
        elif self.second_suit in self.opponents_suits:
            suit = self.longest_suit
        else:
            suit = self.second_suit
        return suit

    def _get_level_with_support(self, suit) -> int:
        """Return appropriate level with partner support."""
        # use distribution points
        hand_value_points = (self.hcp +
                             self.support_shape_points(suit))
        point_list = [13, 17, 19]
        if suit.is_major:
            game = 4
        else:
            game = 5
        # quantitative_raise with point_list = [13, 16, 19]
        # means single raise if points between 13 and 15
        # jump  with points between 16 and 18 etc.
        level = self.quantitative_raise(hand_value_points,
                                        self.responder_bid_one.level,
                                        point_list, game)
        return level

    def _get_suit_support_for_responder(self) -> Suit:
        """Return suit if opener can support responder."""
        suit_to_bid = self.responder_bid_one.denomination
        if self.responder_bid_one.is_double:
            if self.shape[0] >= 6:
                suit_to_bid = self.longest_suit
            else:
                suit_to_bid = self.second_suit
        return suit_to_bid

    def _get_suit_no_support_five_five(self) -> Suit:
        """Return the suit to bid if no support and hand is 5/5."""
        suit_to_bid = self._other_five_card_suit()
        barrier_is_broken = self.barrier_is_broken(self.bid_one,
                                                   self.next_level_bid(suit_to_bid))

        can_break_barrier = (self.hcp >= 15 or
                             (self.hcp >= 14 and self.responder_bid_one.is_nt))
        if barrier_is_broken and not can_break_barrier:
            suit_to_bid = self.bid_one.denomination
        return suit_to_bid

    def _get_best_suits(self) -> tuple[Suit]:
        """Return the *ordered* first and second suits."""
        first_suit = self.longest_suit
        second_suit = self.second_suit
        if self.five_five:
            first_suit = self.bid_one.denomination
            second_suit = self._other_five_card_suit()
        return (first_suit, second_suit)

    def _select_suit_if_six_four(self) -> Suit:
        """Return selected suit with 6/4 shape."""
        suit = self.longest_suit
        if self.shape[1] >= 4:
            if self.second_suit not in self.opponents_suits:
                second_suit = self.second_suit
                suit = self.cheaper_suit(suit, second_suit)
        return suit

    def _other_five_card_suit(self) -> Suit:
        """Return unbid 5 card suit in 5/5 hands."""
        suit_one = self.bid_one.denomination
        if suit_one == self.longest_suit:
            suit = self.second_suit
            if suit in self.opponents_suits:
                suit = self.longest_suit
        else:
            suit = self.longest_suit
            if suit in self.opponents_suits:
                suit = self.second_suit
        return suit

    def _raise_level_with_five_four_strong(self, suit_to_bid: Suit, test_bid: Bid) -> int:
        """Return the raise level with a strong 5/4 hand."""
        if self.hcp >= 19:
            raise_level = 1
        elif self.hcp < 16:
            raise_level = 0
        elif test_bid.level > 3:
            raise_level = 0
        elif suit_to_bid == self.bid_one.denomination:
            raise_level = 0
        elif suit_to_bid.rank > self.bid_one.denomination.rank:
            raise_level = 0
        else:
            raise_level = 1
        return raise_level

    def _five_four_weak_suit(self, suit: Suit, cannot_show_second_suit: bool) -> Suit:
        """Return selected suit for weak 5/4 hands."""
        if suit < self.bid_one.denomination or not cannot_show_second_suit:
            suit_to_bid = suit
        elif self.bid_one.denomination == self.club_suit and suit == self.spade_suit:
            suit_to_bid = self.spade_suit
        else:
            suit_to_bid = self.bid_one.denomination
        return suit_to_bid

    def _get_suit_with_five_four(self) -> Suit:
        """Return suit with 5/4 hands."""
        if self.bid_one.denomination == self.longest_suit:
            suit = self.second_suit
            if self.shape[1] == 4 and self.shape[2] == 4:
                suit = self.cheaper_suit(self.ordered_holding[1][1],
                                         self.ordered_holding[2][1])
            if not self.can_bid_suit(suit):
                suit = self.longest_suit
        else:
            suit = self.longest_suit
            if suit in self.opponents_suits:
                suit = self.second_suit
        return suit

    def _cheapest_four_card_suit(self) -> Suit | None:
        """Return the cheapest 4 card suit."""
        suits = []
        for suit in self.suits:
            if self.suit_length(suit) == 4:
                suits.append(suit)
        cheapest = None
        for suit in suits:
            if cheapest:
                if suit < cheapest:
                    cheapest = suit
            else:
                cheapest = suit
        return cheapest

    def _balanced_bid_level(self) -> int:
        """Return bid level for balanced rebids."""
        bid_level = 0
        if self.nt_level == 1:
            if self.hcp >= 19:
                bid_level = 3
            elif self.hcp >= 17:
                bid_level = 2
            else:
                bid_level = 1
        elif self.nt_level == 2:
            if self._has_seventeen_points_and_no_support_from_responder():
                bid_level = 3
            elif self.hcp >= 18 and self.responder_bid_one.level == 2:
                bid_level = 3
            else:
                bid_level = 2
        if bid_level == 0 and self._balanced_jump():
            bid_level = 3
        return bid_level

    def _select_suit_for_four_four_four_one(self) -> Suit:
        """Select suit with 4441 hands after partner bids singleton suit."""
        singleton_suit = self.suit_shape[3]
        rank = singleton_suit.rank
        rank = (rank+1) % 4
        if self.suits[rank] in self.opponents_suits:
            rank = (rank+1) % 4
            if rank == self.bid_one.denomination.rank:
                rank = (rank+1) % 4
        suit = self.suits[rank]
        return suit

    # Various boolean tests

    def _balanced_jump(self) -> bool:
        """Return True if there has been a jump bid."""
        if self.overcaller_bid_one.is_value_call:
            return self.is_jump(self.overcaller_bid_one, self.responder_bid_one)
        return self.is_jump(self.bid_one, self.responder_bid_one)

    def _weak_and_able_to_repeat_suit(self, cannot_show_second_suit: bool, responder_jumped: bool) -> bool:
        """Return True if weak and able to repeat suit"""
        return (cannot_show_second_suit and
                self.hcp <= 14 and
                not responder_jumped and
                (not self.overcall_made or
                 self.shape[0] >= 6))

    def _has_strong_minor_responder_has_jumped(self) -> bool:
        """Return True with strong hand after partner jumps and no major."""
        return (self.hcp >= 16 and
                self.is_jump(self.bid_one, self.responder_bid_one) and
                self.bid_one.denomination.is_minor and
                self.responder_bid_one.denomination.is_minor and
                not self.overcaller_bid_one.is_value_call)

    def _competitive_auction_weak_with_minor(self) -> bool:
        """Return True if competitive auction, no support and minor."""
        return ((self.advancer_bid_one.is_value_call or
                 self.overcaller_bid_one.is_nt) and
                self.bid_one.denomination.is_minor and
                self.hcp <= 13 and
                self.shape[0] <= 5)

    def _competitive_auction_with_support_for_responder(self) -> bool:
        """Return True if competitive auction and support for partner's major."""
        return ((self.overcaller_bid_one.is_value_call or
                 self.advancer_bid_one.is_value_call) and
                self.responder_bid_one.denomination.is_major and
                self.responder_bid_one.level >= 2 and
                self.suit_length(self.responder_bid_one.denomination) >= 3)

    def _responder_has_bid_nt_game_over_minor(self) -> bool:
        """Return True of responder bid 3NT over a minor."""
        return (self.responder_bid_one.name == '3NT' and
                self.bid_one.denomination.is_minor)

    def _is_shapely_intermediate_hand(self) -> bool:
        """Return True if two suits and 14+ points."""
        return (self.shape[0] + self.shape[1] >= 9 and
                (self.responder_bid_one.name != '1NT' or
                 self.hcp >= 14))

    def _repeatable_five_card_suit(self) -> bool:
        """Return True if weak with repeatable five card suit."""
        first_suit = self.longest_suit
        level = self.next_level(first_suit)
        return (self.hcp >= 16 and
                self.shape[0] >= 5 and level <= 2 and
                self.suit_points(first_suit) >= 5)

    def _weak_five_four(self) -> bool:
        """Return True if weak but biddable 5/4."""
        second_suit = self.second_suit
        return (self.hcp >= 12 and
                self.five_four and
                second_suit not in self.opponents_suits)

    def _three_card_support_for_responder_overcall_made(self) -> bool:
        """Return True with support for responder and overcall made."""
        return (self.overcall_made and
                not self.overcaller_bid_one.is_double and
                self.hcp == 14 and
                self.suit_length(self.responder_bid_one.denomination) >= 3)

    def _four_card_support_for_responder_overcall_made(self) -> bool:
        """Return True with support for responder and overcall made."""
        return (self.hcp == 13 and
                self.suit_length(self.responder_bid_one.denomination) >= 4 and
                self.overcall_made and
                not self.overcaller_bid_one.is_double)

    def _strong_with_second_suit(self, level: bool) -> bool:
        """Return True if strong and has biddable second suit."""
        second_suit = self.second_suit
        return (self.hcp >= 16 and
                self.five_four and
                (self.shape[0] <= 5 or
                 self.suit_points(second_suit) >= 6) and
                second_suit != self.overcaller_bid_one.denomination and
                second_suit != self.advancer_bid_one.denomination and
                self.overcaller_bid_one.denomination == self.advancer_bid_one.denomination and
                level <= 3)

    def _is_strong_with_five_five(self, second_suit: Suit) -> bool:
        """"Return True with 16 points and two five card suits."""
        return (self.hcp >= 16 and
                self.five_five_or_better and
                second_suit not in self.opponents_suits)

    def _is_strong_with_five_four(self, second_suit: Suit) -> bool:
        """"Return True with 16 points and five/four."""
        opening_next_level = self.next_level(self.my_last_bid.denomination)
        return (self.hcp >= 16 and
                self.five_four and
                self.next_level(second_suit) <= opening_next_level and
                self.next_level(second_suit) <= 3 and
                second_suit not in self.opponents_suits)

    def _six_card_suit_weak(self) -> bool:
        """Return True if weak with six card suit."""
        first_suit = self.longest_suit
        level = self.next_level(first_suit)
        return (self.shape[0] >= 6 and
                12 <= self.hcp <= 15 and
                level <= 3 and
                (level <= 2 or
                self.suit_points(first_suit) >= 5) and
                Bid(self.bid_history[-1]).is_pass)

    def _strong_and_balanced(self) -> bool:
        """Return True if strong, balanced and got stoppers."""
        return (self.hcp >= 17 and
                self.is_balanced and
                self.stoppers_in_bid_suits and
                not self.overcaller_bid_one.is_nt and
                (self.responder_bid_one.is_value_call or
                 self.nt_level <= 1))

    def _weak_six_cards(self) -> bool:
        """Return True if weak with six card suit."""
        return (self.hcp >= 12 and
                self.shape[0] >= 6 and
                self.suit_points(self.longest_suit) >= 5 and
                self.longest_suit not in self.opponents_suits and
                self.next_level(self.longest_suit) <= 3)

    def _can_rebid_five_card_suit_at_two_level(self) -> bool:
        """Return True if 5 card suit can be rebid."""
        return (self.shape[0] == 5 and
                self.hcp >= 12 and
                self.next_level(self.longest_suit) <= 2 and
                not self.bid_one.is_nt and
                not self.overcaller_bid_one.is_nt)

    def _can_rebid_seven_card_suit_at_three_level(self) -> bool:
        """Return True if 7 card suit can be rebid."""
        return (self.shape[0] >= 7 and
                self.next_level(self.longest_suit) <= 3)

    def _overcaller_doubled_and_advancer_bid(self) -> bool:
        """Return True if overcaller has doubled and advancer has bid."""
        return (self.overcaller_bid_one.is_double and
                not self.advancer_bid_one.is_pass and
                self.hcp <= 15)

    def _can_rebid_spades(self, level: int) -> bool:
        """Return True if opener can rebid spades."""
        if self.next_level(self.spade_suit) > 4:
            return False
        if self.responder_bid_one.name == '3S' and self.spades >= 3:
            return True
        elif (self.spades >= 2 and
              self.advancer_bid_one.is_value_call and
              self.spade_suit not in self.opponents_suits and
              level <= 4):
            return True
        return False

    def _responder_shows_support_or_can_support_responder(self) -> bool:
        """Return True if responder has shown support."""
        return (self.responder_bid_one.denomination == self.bid_one.denomination or
                self.suit_length(self.responder_bid_one.denomination) >= 4 or
                (self.responder_bid_one.level == 2 and
                 self.responder_bid_one.is_major and
                 self.suit_length(self.responder_bid_one.denomination) >= 3))

    def _can_support_responders_major(self) -> bool:
        """Return True can support responder's major."""
        return (self.responder_bid_one.level >= 2 and
                self.suit_length(self.responder_bid_one.denomination) >= 3 and
                self.responder_bid_one.denomination.is_major and
                self.overcall_made)

    def _has_six_card_minor_and_eighteen_points(self) -> bool:
        """Return True with 18 points and six card suit."""
        return (self.hcp >= 18 and
                self.responder_bid_one.denomination.is_minor and
                self.shape[0] >= 6 and
                self.stoppers_in_bid_suits and
                self.stoppers_in_unbid_suits() and
                self.nt_level <= 3)

    def _is_unbalanced_with_sixteen_points(self) -> bool:
        """Return True if 16+ points and unbalanced."""
        return (self.hcp >= 16 and
                not self.is_balanced and
                self .second_suit not in self.opponents_suits)

    def _can_support_nineteen_points(self) -> bool:
        """Return True if 19+ points and support for responder."""
        return (self.hcp >= 19 and
                self.responder_bid_one.denomination == self.second_suit and
                self.game_level(self.second_suit) >= self.next_level(self.second_suit))

    def _can_support_seventeen_points_and_void(self) -> bool:
        """Return True if 17+ points and support for responder and a void."""
        return (self.hcp >= 17 and
                self.responder_bid_one.denomination == self.second_suit and
                self.shape[3] == 0 and
                self.game_level(self.second_suit) >= self.next_level(self.second_suit))

    def _suit_is_major_and_eighteen_points(self, suit_to_bid: Suit) -> bool:
        """Return True if 18+ points and level <= 3."""
        return (self.next_level(suit_to_bid) <= 3 and
                suit_to_bid.is_major and
                self.hcp >= 18)

    def _responder_support_with_jump(self) -> bool:
        """Return True if responder supports and has jumped."""
        return (self.responder_bid_one.denomination == self.bid_one.denomination and
                self.is_jump(self.bid_one, self.responder_bid_one) and
                self.nt_level <= 3)

    def _can_repeat_suit_and_seventeen_points(self, suit_to_bid: Suit) -> bool:
        """Return True if can repeat opening suit and 17+ points."""
        return (suit_to_bid == self.bid_one.denomination and
                self.hcp >= 17 and
                self.stoppers_in_bid_suits)

    def _has_five_four_and_sixteen_points(self, suit_to_bid: Suit) -> bool:
        """Return True if 5/4 and 16+ points."""
        return (suit_to_bid == self.bid_one.denomination and
                self.hcp >= 16 and
                self.five_four_or_better)

    def _five_four_strong_test_nt(self, test_bid: Bid) -> bool:
        """Return True if NT bid is allowed."""
        responder_jumped = self.jump_bid_made(self.responder_bid_one)
        return (test_bid.level == 3 and
                self.nt_level <= 3 and
                self.shape[0] < 6 and
                self.is_balanced and
                self.stoppers_in_bid_suits and
                not responder_jumped)

    def _weak_five_four_with_weak_suit(self, suit_to_bid: Suit) -> bool:
        """Return True if suit too weak to rebid."""
        value_one = (suit_to_bid == self.bid_one.denomination and
                     self.overcall_made and
                     not self.responder_bid_one.is_value_call and
                     self.suit_points(suit_to_bid) <= 4)
        value_two = (suit_to_bid == self.bid_one.denomination and
                     (self.overcaller_bid_one.is_nt or
                      self.advancer_bid_one.is_nt) and
                     self.suit_points(suit_to_bid) <= 4)
        return (value_one or value_two and
                (self.responder_bid_one.is_pass or
                 self.bid_history[-2] != 'P'))

    def _can_bid_at_appropriate_level(self, suit_to_bid: Suit, level: int) -> bool:
        """Return True if possible to bid at appropriate level."""
        return (level <= 2 or
                ((self.hcp >= 13 or
                  suit_to_bid == self.bid_one.denomination) and
                 self.responder_bid_one.level == 2))

    def _weak_five_four_consider_bid(self, level: int) -> bool:
        """Return True if a sound bid is possible for weak 5/4."""
        return (level <= 2 or self.shape[0] >= 6 or
                (self.responder_bid_one.is_nt and level <= 3) or
                not self.overcall_made or
                (self.jump_bid_made(self.responder_bid_one) and
                self.responder_bid_one.denomination != self.bid_one.denomination))

    def _weak_after_one_nt_and_barrier_broken(self, cannot_show_second_suit: bool) -> bool:
        """Return True if barrier broken after responder bids 1NT."""
        return (self.hcp <= 15 and
                cannot_show_second_suit and
                self.responder_bid_one.name == '1NT')

    def _six_four_responder_at_level_two(self) -> bool:
        """"Return True if 6/4 and responder at level 2."""
        return (self.six_four and
                self.responder_bid_one.level == 2 and
                self.levels_to_bid(self.bid_one,
                                   self.next_level_bid(self.second_suit)) <= 2 and
                self.second_suit not in self.opponents_suits)

    def _strong_or_can_bid_at_level_two(self, suit_to_bid: Suit) -> bool:
        """Return True if can bid at level 2 or strong."""
        return (self.next_level(suit_to_bid) <= 2 or
                self.hcp >= 16 or
                (self.overcall_made and
                 self.suit_length(self.overcaller_bid_one.denomination) == 0))

    def _strong_five_four_or_better(self) -> bool:
        """Return True if strong and 5/4 or better."""
        return (self.hcp >= 15 and
                self.five_four_or_better and
                self.second_suit not in self.opponents_suits)

    def _is_strong_with_seven_card_major(self) -> bool:
        """Return True if strong with seven card major."""
        return (self.hcp >= 16 and
                self.shape[0] >= 7 and
                self.longest_suit.is_major and
                self.next_level(self.longest_suit) <= self.longest_suit.game_level)

    def _is_strong_six_four_with_major(self) -> bool:
        """Return True if strong with six card major."""
        return (self.hcp >= 16 and
                self.second_suit.is_major and
                self.second_suit not in self.opponents_suits and
                self.shape[1] >= 4)

    def _weak_with_overcall_or_next_level_three(self) -> bool:
        """Return True if overcall or next level greater than 2."""
        return ((self.overcall_made and
                 self.hcp <= 15) or
                self.next_level(self.longest_suit) > 2)

    def _has_minor_can_support_responders_major(self) -> bool:
        """Return True if suit is a minor and can support responder's major."""
        return (self.longest_suit.is_minor and
                self.responder_bid_one.denomination.is_major and
                self.suit_length(self.responder_bid_one.denomination) >= 4)

    def _has_six_card_major_and_responder_bid_two_nt(self) -> bool:
        """Return True if six card major after responder bids NT."""
        return (self.responder_bid_one.name == '2NT' and
                self.shape[0] >= 6 and
                self.longest_suit.is_major)

    def _is_strong_with_solid_seven_card_suit(self) -> bool:
        """Return True if strong with solid 7 card suit."""
        return (self.hcp >= 15 and
                self.shape[0] >= 7 and
                self.solid_suit_honours(self.longest_suit))

    def _has_five_card_suit_fifteen_points_level_two(self) -> bool:
        """Return True if intermediate with 5 card suit."""
        return (self.hcp >= 15 and
                self.shape[0] >= 5 and
                self.next_level(self.longest_suit) <= 2)

    def _has_seven_card_suit_and_weak(self) -> bool:
        """Return True if weak with 7 card suit."""
        return (self.hcp >= 11 and
                self.shape[0] >= 7 and
                self.next_level(self.longest_suit) <= 3)

    def _has_six_card_suit_responder_at_level_two(self) -> bool:
        """Return True if 6 card suit and responder at level 2."""
        return (self.shape[0] >= 6 and
                self.responder_bid_one.level >= 2 and
                self.next_level(self.longest_suit) <= 3)

    def _has_fifteen_points_and_level_is_one(self, level: int) -> bool:
        """Return True if 15+ points and level is 1."""
        return self.hcp >= 15 and level >= self.nt_level

    def _barrier_would_break_and_fewer_that_sixteen(self, suit: Suit, test_bid: Bid) -> bool:
        """Return True if barrier broken and fewer than 16 points."""
        cannot_show_second_suit = (self.barrier_is_broken(self.bid_one, test_bid) and
                                   not self.is_jump(self.bid_one, self.responder_bid_one))
        return ((self.hcp <= 16 and cannot_show_second_suit) or suit in self.opponents_suits)

    def _strong_can_bid_nt(self, bid_level: int) -> bool:
        """Return True if it appropriate to bid NT."""
        return (0 <= bid_level <= 3 and
                bid_level >= self.nt_level and
                (not self._weak_partner() or self.hcp >= 18))

    def _no_fit_fifteen_points_responder_level_two(self) -> bool:
        """Return True with 15+points and no fit and responder at level 2."""
        return (self.responder_bid_one.denomination != self.bid_one.denomination and
                self.responder_bid_one.level >= 2 and
                self.hcp >= 15 and
                self.stoppers_in_bid_suits and
                self.nt_level <= 3)

    def _has_seventeen_points_and_no_support_from_responder(self) -> bool:
        """Return True with 17+ points and no support."""
        return (self.hcp >= 17 and
                self.bid_one.denomination != self.responder_bid_one.denomination and
                not self.overcall_made)

    def _is_balanced_or_no_fit_with_responder(self) -> bool:
        """Return True if balanced or no fit with responder."""
        return ((self.is_balanced or
                 self.suit_length(self.responder_bid_one.denomination) <= 2) and
                self.stoppers_in_bid_suits and
                self.nt_level <= 3)

    def _weak_partner(self) -> bool:
        """Return True if partner has indicated a weak hand."""
        return (self.responder_bid_one.level == 1 and
                (self.overcaller_bid_one.level == 2 or
                 self.overcaller_bid_one.is_double or
                 self.advancer_bid_one.is_nt or
                 self.advancer_bid_one.level == 2) or
                (self._responder_bids_openers_suit_at_lowest_level() and
                 self.hcp < 17))

    def _responder_bids_openers_suit_at_lowest_level(self) -> bool:
        """Return True if responder bids opener's suit at lowest level."""
        return (self.my_last_bid.denomination == self.responder_bid_one.denomination and
                self.my_last_bid.level+1 == self.responder_bid_one.level)

    def _has_six_card_major_and_can_bid_game(self) -> bool:
        """Return True with 6 card major and below game level."""
        return (self.shape[0] >= 6 and
                self.longest_suit.is_major and
                self.next_level(self.longest_suit) <= 4)

    def _has_six_card_major_and_can_bid_at_three_level(self) -> bool:
        """Return True with 6 card major and can_bid_at 3 level."""
        return (self.shape[0] >= 6 and
                self.longest_suit.is_major and
                self.next_level(self.bid_one.denomination) <= 3)

    def _is_balanced_minor_suit_can_bid_nt_game(self) -> bool:
        """Return True if suit is manor, balanced and can bid 3NT."""
        return (self.bid_one.denomination.is_minor and
                self._is_balanced_can_bid_nt_game())

    def _is_balanced_can_bid_nt_game(self) -> bool:
        return (self.is_balanced and
                self.stoppers_in_bid_suits and
                self.nt_level <= 3)

    def _can_bid_two_nt(self) -> bool:
        """Return True if can bid 2NT."""
        return ((self.hcp >= 17 or self.nt_level == 2) and
                self.nt_level <= 2 and
                self.stoppers_in_bid_suits)

    def _powerful_and_has_four_cards_in_unbid_major(self, unbid_major: Suit) -> bool:
        """Return True if powerful hand with 4 card unbid major."""
        return (unbid_major is not None and
                unbid_major not in self.opponents_suits and
                (self.five_four_or_better or
                 self.my_last_bid.is_minor))

    def _weak_overcall_responder_level_one(self) -> bool:
        """Return True if weak and responder has bid at level 1."""
        return (self.hcp <= 12 and
                self.overcall_made and
                self.responder_bid_one.level == 1)

    def _fffo_strong_four_card_support(self) -> bool:
        """Return True if strong and can support partner suit."""
        return (self.responder_bid_one.level == 2 and
                self.shape == [4, 4, 4, 1] and
                self.suit_length(self.responder_bid_one.denomination) >= 4 and
                self.hcp >= 17)

    def _can_bid_three_nt(self) -> bool:
        """Return True if can support NTs."""
        return (self.responder_bid_one.is_nt and
                self.shape[0] >= 5 and
                self.nt_level <= 3 and
                self.stoppers_in_bid_suits and
                self.hcp >= 12)

    def _no_biddable_second_suit_and_support_for_partner(self) -> bool:
        """Return True if Support for responder and second suit not biddable major."""
        suit = self.responder_bid_one.denomination
        return (self.responder_bid_one.level >= 2 and
                self.hcp >= 16 and
                self.suit_length(suit) >= 4 and
                self.next_level(suit) <= suit.game_level and
                not (self.second_suit.is_major and self.shape[1] >= 4))

    def _can_bid_second_suit_after_nt(self) -> bool:
        """Return True if can bid second suit after a 2NT response."""
        return (self.five_four and
                self.partner_bid_one.name == '2NT' and
                self.second_suit.rank < self.longest_suit.rank and
                self.second_suit not in self.opponents_suits)

    def _has_six_card_major_and_responder_bid_one_nt(self) -> bool:
        """Return True with 6 card major and responder bid 1NT."""
        return (self.hcp >= 15 and
                self.shape[0] >= 6 and
                self.longest_suit.is_major and
                self.responder_bid_one.name == '1NT')

    def _five_in_opponents_suits(self) -> bool:
        """Return True if hand has five cards in opponents suits."""
        for suit in self.opponents_suits:
            if self.suit_holding[suit] >= 5:
                return True
        return False
