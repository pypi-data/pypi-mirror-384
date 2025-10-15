"""
    Bid for Game
    Acol opening bid module
"""
import inspect
from bridgeobjects import Board, Card
from .bidding import Bid, Pass, HandSuit
from .hand import Hand

inspection = inspect.currentframe


class OpeningBid(Hand):
    """BfG OpeningBid class."""
    def __init__(self, hand_cards: list[Card], board: Board):
        super(OpeningBid, self).__init__(hand_cards, board)
        self.trace = 0

    def suggested_bid(self) -> Bid:
        """Directs control to relevant method and return a Bid."""
        if self.hcp >= 23:
            bid = self.club_bid(2, '1001')
        elif self.is_balanced or (self.is_semi_balanced and 20 <= self.hcp <= 22):
            bid = self._balanced_openings()
        elif self._can_open_normally():
            bid = self._unbalanced_openings()
        elif self.shape[0] >= 6:
            bid = self._weak_opening_bid()
        else:
            bid = Pass('1002')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _can_open_normally(self) -> Bid:
        """Return True if hand suitable for opening bid."""
        if self.hcp >= 12:
            value = True
        elif (self.hcp == 11 and (self.shape[0] >= 6 or self.five_five) or
              (self.five_four and
               self.suit_points(self.longest_suit) + self.suit_points(self.second_suit) >= 11)):
            value = True
        else:
            value = False
        return value

    def _balanced_openings(self) -> Bid:
        """Return bid for balanced hands."""
        if 12 <= self.hcp <= 14:
            bid = self._weak_balanced_bid()
        elif 14 <= self.hcp < 20:
            bid = self._unbalanced_openings()
        elif 20 <= self.hcp <= 22:
            bid = self.nt_bid(2, '1003')
        else:
            bid = Pass('1004')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _weak_balanced_bid(self) -> Bid:
        """Return bid for weak (12-14) balanced hands."""
        if self._five_card_major_with_seven_suit_points():
            bid = self._unbalanced_openings()
        else:
            bid = self.nt_bid(1, '1005')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _unbalanced_openings(self) -> Bid:
        """ return bid for unbalanced hands."""
        # points checked before entry to here
        if self.shape[0] >= 8 and self.hcp <= 14:
            bid = self._weak_eight_card_suits_bid()
        elif self.shape[0] >= 5:
            bid = self._bid_with_five_card_suit()
        elif self.shape == [4, 4, 4, 1]:
            bid = self._four_four_four_one_bid()
        else:
            bid = self._four_card_suits()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _weak_eight_card_suits_bid(self) -> Bid:
        """Return bid for 8+ card suits and fewer than 15 points."""
        suit = self.longest_suit
        if suit.is_major:
            game_level = 4
        else:
            game_level = 5
        level = self.shape[0] - 4
        level = min(level, game_level)
        if self.longest_suit.is_minor and self.shape[1] >= 4:
            bid = self.suit_bid(1, self.longest_suit, '1006')
        else:
            bid = self.suit_bid(level, suit, '1007')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _four_card_suits(self) -> Bid:
        """Return bid with two four card suits."""
        if self.spades == 4:
            bid = self._four_spades()
        elif self.hearts == 4:
            bid = self.heart_bid(1, '1008')
        elif self.diamonds == 4:
            bid = self._four_diamonds()
        else:
            bid = self.club_bid(1, '1009')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _four_spades(self) -> Bid:
        """Return bid if hand has 4 spades."""
        if self.hearts == 4:
            bid = self.heart_bid(1, '1010')
        elif self.diamonds == 4:
            bid = self.spade_bid(1, '1011')
        elif self.clubs == 4:
            bid = self.club_bid(1, '1012')
        else:
            bid = self.spade_bid(1, '1013')  # 4,3,3,3
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _four_diamonds(self) -> Bid:
        """Return bid if hand has 4 diamonds (and possibly 4 clubs)."""
        if self.clubs == 4:
            bid = self.club_bid(1, '1014')
        else:
            bid = self.diamond_bid(1, '1015')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _bid_with_five_card_suit(self) -> Bid:
        """Return bid with a five card suit."""
        if not self.equal_long_suits:
            if self.is_balanced and self.hcp <= 14:
                bid = self.suit_bid(1, self.longest_suit, '1016')
            else:
                bid = self.suit_bid(1, self.longest_suit, '1017')
            if self.hcp <= 11 and self.shape[0] == 5 and self.shape[1] == 4:
                bid.call_id = '1018'
            elif self.hcp <= 11:
                bid.call_id = '1019'
        else:
            bid = self._five_five_hands_bid()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _five_five_hands_bid(self) -> Bid:
        """Return bid for five/five hands."""
        if self.spades >= 5 and self.clubs >= 5:
            bid = self.club_bid(1, '1020')
        elif self.spades >= 5:
            bid = self.spade_bid(1, '1021')
        elif self.hearts >= 5:
            bid = self.heart_bid(1, '1022')
        elif self.diamonds >= 5:
            bid = self.diamond_bid(1, '1023')
        else:
            assert False, 'Bid not defined'
        if self.hcp <= 11:
            bid.call_id = '1024'
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _four_four_four_one_bid(self) -> Bid:
        """Return bid for 4441 hands."""
        if self.clubs == 1:
            bid = self.heart_bid(1, '1025')
        elif self.diamonds == 1:
            bid = self.club_bid(1, '1026')
        elif self.hearts == 1:
            bid = self.diamond_bid(1, '1027')
        elif self.spades == 1:
            bid = self.heart_bid(1, '1028')
        else:
            assert False, 'Bid not defined'
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _weak_opening_bid(self) -> Bid:
        """Return bid for weak opening hands."""
        if self.seven_six:
            return self._weak_seven_six_bid()
        elif self.six_six:
            return self._weak_six_six_bid()
        else:
            bid = self._select_weak_bid()
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _select_weak_bid(self) -> Bid:
        """Return weak bids."""
        if self.hcp >= 6 and self.shape[0] == 6 and self.longest_suit != self.club_suit:
            bid = self._weak_two_bid()
        elif self.shape[0] >= 7:
            bid = self._weak_three_bid()
        else:
            bid = Pass('1029')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _weak_two_bid(self) -> Bid:
        """Return weak two bid."""
        suit = self.longest_suit
        suit_quality = HandSuit(suit, self).suit_quality()
        if suit != self.club_suit and suit_quality >= 0:
            bid = self.suit_bid(2, suit, '1030')
        else:
            bid = Pass('1031')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _weak_three_bid(self) -> Bid:
        """Return weak three bid."""
        suit = self.longest_suit
        suit_quality = HandSuit(suit, self).suit_quality()
        if self.hcp <= 9 and suit_quality >= 0.5:
            bid = self.suit_bid(3, suit, '1032')
        else:
            bid = Pass('1033')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _weak_six_six_bid(self) -> Bid:
        """Return bid for  weak hand with two six card suits."""
        if self.hcp < 6:
            bid = Pass('1034')
        elif self.spades == 6:
            bid = self.spade_bid(2, '1036')
        elif self.hearts == 6:
            bid = self.heart_bid(2, '1036')
        elif self.diamonds == 6:
            bid = self.diamond_bid(2, '1037')
        else:
            bid = Pass('1038')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _weak_seven_six_bid(self) -> Bid:
        bid = self.suit_bid(3, self.longest_suit, '1039')
        self.tracer(__name__, inspection(), bid, self.trace)
        return bid

    def _five_card_major_with_seven_suit_points(self) -> Bid:
        """Returns True if hand has 5 card major with 7 points in that suit."""
        for suit in (self.spade_suit, self.heart_suit):
            if (self.cards_in_suit(suit) == 5 and
                    self.suit_points(suit) >= 7):
                return True
        return False
