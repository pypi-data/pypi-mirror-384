""" Bid for Game Hand module."""
import os
from termcolor import cprint
from pathlib import Path
import json
import inspect

from bridgeobjects import (Board, Hand, Card, Call, Suit, NoTrumps,
                           SUIT_NAMES, CALLS, SUITS, Denomination)
from .bidding import Bid
from .utils import NamedBids


MODULE_COLOUR = 'blue'

MODULE_TRACE = 'batch_tests/data//module_trace.txt'
TRACE_FILE = 'trace.txt'
TRACE_PATH = Path(os.getcwd(), TRACE_FILE)
trace_set = False
trace_value = False


class Hand(Hand):
    """A sub class of bridgeobjects Hand, to enable bidding."""
    overcaller_position = {'none': 0, 'second_seat': 1, 'fourth_seat': 2}

    spade_suit, heart_suit, diamond_suit, club_suit = SUITS['S'], SUITS['H'], SUITS['D'], SUITS['C']

    def __init__(self, hand_cards: list[Card] = None, board: Board = None, *args, **kwargs):
        super().__init__(hand_cards, *args, **kwargs)
        (self.board, self.bid_history, self.overcaller) = self._setup_board(board)
        self.suits = [SUITS[name] for name in 'CDHS']
        self.no_trumps = NoTrumps()
        self._losers = None

        self.holding_partner_one = 0
        self.unplayed_cards = [card for card in self.cards]

        utils = NamedBids(self, self.bid_history)
        self.opener_bid_one = utils.opener_bid_one
        self.opener_bid_two = utils.opener_bid_two
        self.opener_bid_three = utils.opener_bid_three
        self.responder_bid_one = utils.responder_bid_one
        self.responder_bid_two = utils.responder_bid_two
        self.responder_bid_three = utils.responder_bid_three
        self.overcaller_bid_one = utils.overcaller_bid_one
        self.overcaller_bid_two = utils.overcaller_bid_two
        self.overcallers_last_bid = utils.overcallers_last_bid
        self.advancer_bid_one = utils.advancer_bid_one
        self.advancer_bid_two = utils.advancer_bid_two
        self.previous_bid = utils.previous_bid
        self.last_bid = utils.last_bid
        self.right_hand_bid = utils.right_hand_bid
        self.my_last_bid = utils.my_last_bid
        self.partner_bid_one = utils.partner_bid_one
        self.partner_bid_two = utils.partner_bid_two
        self.partner_penultimate_bid = utils.partner_penultimate_bid
        self.partner_last_bid = utils.partner_last_bid
        self.bid_one = utils.bid_one
        self.bid_two = utils.bid_two
        self.bid_three = utils.bid_three

        self.responders_support = utils.responders_support
        self.overcaller_has_jumped = utils.overcaller_has_jumped
        self.bid_after_stayman = utils.bid_after_stayman
        self.overcaller_in_second_seat = utils.overcaller_in_second_seat
        self.overcaller_in_fourth_seat = utils.overcaller_in_fourth_seat

        self.opener_suit_one = self.opener_bid_one.denomination
        self.opener_suit_two = self.opener_bid_two.denomination
        self.opener_suit_three = self.opener_bid_three.denomination
        self.suit_one = utils.suit_one
        self.overcaller_suit_one = utils.overcaller_suit_one
        self.advancer_suit_one = utils.advancer_suit_one
        self.advancer_suit_two = utils.advancer_suit_two
        self.holding_partner_one = utils.holding_partner_one

        (self.trace_module, self.last_hand) = self._get_trace_module()

    @staticmethod
    def _setup_board(board: Board | None) -> tuple[Board, list[Call], bool]:
        """Initialse the board."""
        if not board:
            board = Board()
            board.active_bid_history = []
        bid_history = []
        overcaller = False
        bid_history = board.active_bid_history
        if len(bid_history) % 2 != 0:
            overcaller = True
        return (board, bid_history, overcaller)

    def to_json(self) -> str:
        """Return object as json string property."""
        json_str = json.dumps({
            'cards': [card.name for card in self.cards],
            'unplayed_cards': [card.name for card in self.unplayed_cards],
        })
        return json_str

    def from_json(self, json_str: str) -> None:
        """Populate the attributes from the json string."""
        hand_dict = json.loads(json_str)
        self.cards = [Card(name) for name in hand_dict['cards']]
        self.unplayed_cards = [Card(name) for name in hand_dict['unplayed_cards']]

    @property
    def nt_level(self) -> int:
        """Return the level of no trumps"""
        return self.next_nt_bid().level

    @property
    def losers(self) -> int:
        """Return the number of losers in the Hand."""
        if not self._losers:
            self._losers = self._get_losers()
        return self._losers

    def _get_losers(self) -> int:
        """Calculate and return the number of losers in the Hand."""
        losers = 0
        for suit in SUIT_NAMES:
            cards = [card for card in self.cards_by_suit[suit]]
            honour_count = 0
            for card in cards:
                if card.value >= 12:
                    honour_count += 1
                elif card.value == 11:
                    if self.suit_points(suit) > 2:
                        honour_count += 1
            count = min(3, len(cards))
            losers += count - honour_count
        return losers

    def is_insufficient_bid(self, test_bid) -> bool:
        """Return True if the bid is insufficient."""
        last_bid = None
        for last_bid in self.bid_history[::-1]:
            if Bid(last_bid).is_value_call:
                break
        last_bid_index = CALLS.index(last_bid)
        test_bid_index = CALLS.index(test_bid.name)
        if test_bid_index <= last_bid_index:
            return True
        return False

    @property
    def singleton_honour(self) -> bool:
        """Return True if hand has singleton K or Q."""
        return self._singleton_honour()

    def _singleton_honour(self) -> bool:
        """Return True if hand has singleton K or Q."""
        if self.shape[3] == 1:
            for suit_name in SUIT_NAMES:
                suit = Suit(suit_name)
                if self.suit_length(suit) == 1:
                    for card in self.cards:
                        if card.suit == suit:
                            if card.rank in 'KQ':
                                return True
        return False

    @property
    def opponents_have_bid(self) -> bool:
        """Return True if the opponents have made a bid."""
        return self._opponents_have_bid()

    def _opponents_have_bid(self) -> bool:
        """Return True if the opponents have made a bid."""
        for bid in self.bid_history[1::2]:
            if Bid(bid).is_value_call:
                return True
        return False

    @property
    def competitive_auction(self) -> bool:
        """Return True if the last bid is not Pass or Double."""
        return self._competitive_auction()

    def _competitive_auction(self):
        """Return True if the last bid is not Pass or Double."""
        value = False
        if len(self.bid_history) >= 1:
            value = Bid(self.bid_history[-1]).is_value_call
        if len(self.bid_history) >= 3:
            value = value or Bid(self.bid_history[-3]).is_value_call
        if len(self.bid_history) >= 5:
            value = value or Bid(self.bid_history[-5]).is_value_call
        return value

    @staticmethod
    def _is_value_call_or_double(bid: Bid) -> bool:
        """Return True if is value call or double."""
        call = Bid(bid)
        value = call.is_value_call or call.is_double
        return value

    @property
    def opponents_have_doubled(self) -> bool:
        """Return True if opponents have doubled with no further bid from them."""
        return self._opponents_have_doubled()

    def _opponents_have_doubled(self) -> bool:
        """Return True if opponents have doubled with no further bid from them."""
        if len(self.bid_history) >= 1:
            if Bid(self.bid_history[-1]).is_double:
                return True
            elif len(self.bid_history) >= 3:
                if (Bid(self.bid_history[-3]).is_double and
                        Bid(self.bid_history[-1]).is_pass):
                    return True
        return False

    @property
    def partner_has_passed(self) -> bool:
        """Return True of partner passed on first round."""
        return self._partner_has_passed()

    def _partner_has_passed(self) -> bool:
        """Return True of partner passed on first round."""
        value = False
        if len(self.bid_history) >= 5:
            if Bid(self.bid_history[-5]).is_pass:
                value = True
        return value

    def _bid_after_stayman(self) -> bool:
        """Return True if responder has bid Clubs after NT opening."""
        if (self.opener_bid_one.is_nt and
                self.responder_bid_one.denomination == self.club_suit):
            return True
        return False

# TODO: sort out use of shortage points
    def suit_bid(self, level: int,
                 suit: Suit,
                 comment: str = '0000',
                 use_shortage_points: bool = False) -> Bid:
        """Return a bid in the suit at the given level."""
        return Bid(self._call_name(level, suit.name), comment, use_shortage_points)

    def heart_bid(self,
                  level: int,
                  comment: str = '0000',
                  use_shortage_points: bool = False) -> Bid:
        """Return a bid in Hearts at the given level."""
        return Bid(self._call_name(level, 'H'), comment, use_shortage_points)

    def spade_bid(self,
                  level: int,
                  comment: str = '0000',
                  use_shortage_points: bool = False) -> Bid:
        """Return a bid in Spades at the given level."""
        return Bid(self._call_name(level, 'S'), comment, use_shortage_points)

    def club_bid(self,
                 level: int,
                 comment: str = '0000',
                 use_shortage_points: bool = False) -> Bid:
        """Return a bid in Clubs at the given level."""
        return Bid(self._call_name(level, 'C'), comment, use_shortage_points)

    def diamond_bid(self,
                    level: int,
                    comment: str = '0000',
                    use_shortage_points: bool = False) -> Bid:
        """Return a bid in Diamonds at the given level."""
        return Bid(self._call_name(level, 'D'), comment, use_shortage_points)

    def nt_bid(self,
               level: int,
               comment: str = '0000',
               use_shortage_points: bool = False) -> Bid:
        """Return a bid in NT at the given level."""
        return Bid(self._call_name(level, 'NT'), comment, use_shortage_points)

    def barrier_is_broken(self, first_bid: Bid, second_bid: Bid) -> bool:
        """Return True if second_bid breaks the barrier relative to bid_one."""
        level_one = first_bid.level
        barrier = Bid(self._call_name(level_one+1, first_bid.denomination.name))
        return self._higher_bid(barrier, second_bid)

    def cheapest_long_suit(self) -> Suit | None:
        """Return the longest suit or cheapest of equal length suits to bid."""
        if self.shape[0] > self.shape[1] and self.longest_suit not in self.opponents_suits:
            return self.longest_suit

        max_length = self.shape[1]
        last_bid_denomination = self._last_denomination_called()
        extended_suit_list = self._get_extended_suit_list()

        # find the starting index in the extended suit list
        index = extended_suit_list.index(last_bid_denomination)

        # find the level of NT in the middle of the extended suit list
        nt_level = self.nt_level
        while index < len(extended_suit_list) - 1 and index < 8:
            index += 1
            if index >= 4:
                # if we're in the second half, increment the level by 1.
                # I.e. we have past NT and onto the next level
                level = nt_level + 1
            else:
                level = nt_level

            # test the next suit
            suit = extended_suit_list[index]
            if (self.suit_length(suit) == max_length and
                    self.next_level(suit) == level and
                    suit not in self.opponents_suits):
                return suit
        return None

    def _last_denomination_called(self) -> Denomination:
        """Return the denomination of the last value call."""
        for bid in self.bid_history[::-1]:
            call = Bid(bid)
            if call.is_suit_call:
                return call.denomination
        assert False, 'Last denomination called with no value call in history'

    @staticmethod
    def _get_extended_suit_list() -> list[str]:
        """Return an extended list of sorted of suits, e.g. [C, D, H, S, C, D, H, S]."""
        extended_suit_list = [Suit(name) for name in SUIT_NAMES]
        extended_suit_list.sort(key=lambda x: x.rank)

        # get a double suit list, e.g. [C, D, H, S, C, D, H, S]
        extended_suit_list.extend(extended_suit_list)
        return extended_suit_list

    @staticmethod
    def _higher_bid(first_bid: Bid, second_bid: Bid) -> bool:
        """Return True if first_bid is the lower."""
        level_one = first_bid.level
        level_two = second_bid.level
        if level_two > level_one:
            return True
        else:
            if level_one == level_two:
                if first_bid.denomination < second_bid.denomination:
                    return True
        return False

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

    def jump_bid_made(self, test_bid: Bid) -> bool:
        """Test bid against bid-history and return True if test_bid is a jump over last relevant bid."""
        second_bid = None
        for bid in self.bid_history[::-1]:
            if bid != 'P' and bid != 'D' and bid != 'R':
                second_bid = Bid(bid)
                break
        jump_level = test_bid.level - second_bid.level
        if jump_level > 1:
            return True
        elif jump_level == 1 and second_bid.denomination < test_bid.denomination:
            return True
        return False

    def levels_to_bid(self, bid_one: Bid, bid_two: Bid) -> int:
        """
        Return the number of 'steps' between bid_one and bid_two.

        e.g.

        1C to 3H is 3 steps: (1C, 2C 3C, 3H) but
        1S to 3H is 2 steps: (1S, 2S, 3H).
        """
        steps = 0
        while bid_one < bid_two:
            bid_one = self.suit_bid(bid_one.level+1, bid_one.denomination)
            steps += 1
        return steps

    @property
    def overcall_made(self) -> bool:
        """Return 1 if an overcall has been made by 2nd and not by 4th seat.
        Return 2 if overcall has been made in 4th seat.
        """
        return self._overcall_made()

    def _overcall_made(self) -> bool:
        """Return 1 if an overcall has been made by 2nd and not by 4th seat.
        Return 2 if overcall has been made in 4th seat.
        """
        bid_history = self.bid_history
        for bid in bid_history[1::2]:
            if not Bid(bid).is_pass:
                if Bid(bid_history[-1]).is_value_call and len(bid_history) > 2:
                    return self.overcaller_position['fourth_seat']
                return self.overcaller_position['second_seat']
        return self.overcaller_position['none']

    @property
    def opponents_at_game(self) -> bool:
        """Return True if opponents at game level."""
        return self._opponents_at_game()

    def _opponents_at_game(self):
        """Return True if opponents at game level."""
        if len(self.bid_history) >= 3:
            if (Bid(self.bid_history[-3]).is_game or
                    Bid(self.bid_history[-1]).is_game):
                return True
        elif len(self.bid_history) >= 1:
            if Bid(self.bid_history[-1]).is_game:
                return True
        return False

    @property
    def bidding_above_game(self) -> bool:
        """Return True if the bidding is at or above game level."""
        return self._bidding_above_game()

    def _bidding_above_game(self):
        """Return True if the bidding is at or above game level."""
        for bid in self.bid_history[::1]:
            if Bid(bid).is_game:
                return True
        return False

    @property
    def can_double(self) -> bool:
        """Return True if double is legal."""
        return self._can_double()

    def _can_double(self) -> bool:
        if self.bid_history[-1] != 'P' or self.bid_history[-1] != 'P':
            return True
        return False

    @property
    def partner_doubled_game(self) -> bool:
        """Return True if partner has doubled at or above game level."""
        return self._partner_doubled_game()

    def _partner_doubled_game(self) -> bool:
        """Return True if partner has doubled at or above game level."""
        if 'D' in self.bid_history:
            index = self.bid_history.index('D')
            bids = [Bid(bid) for bid in self.bid_history[index::-1]]
            for bid in bids:
                if bid.is_value_call:
                    return bid.is_game
        return False

    def double_level(self) -> int:
        """Return the level at which the DOUBLE was made."""
        level = 0
        index = self.bid_history.index('D')
        bids = [Bid(bid) for bid in self.bid_history[index::-1]]
        for bid in bids:
            if bid.is_value_call:
                level = bid.level
                break
        return level

    @property
    def opponents_suits(self) -> list[Suit]:
        """Return a list of all opponent's bid suits."""
        return self._opponents_suits()

    def _opponents_suits(self) -> list[Suit]:
        """Return a list of all opponent's bid suits."""
        opponents_suits = []
        start = 1
        if self.overcaller:
            start = 0
        for bid in self.bid_history[start::2]:
            call = Bid(bid)
            if call.is_suit_call:
                opponents_suits.append(Suit(call.denomination.name))
        return opponents_suits

    def partner_bids_at_lowest_level(self) -> bool:
        """Return True if partner has not jumped."""
        double_index = None
        for index, bid in enumerate(self.bid_history):
            if Bid(bid).is_double:
                double_index = index
                break

        value = False
        partners_bid = Bid(self.bid_history[double_index+2])
        for bid in list(reversed(self.bid_history))[double_index+1::2]:
            if Bid(bid).is_value_call:
                # noinspection PyTypeChecker
                value = self.is_jump(Bid(bid), partners_bid)
        return value

    def openers_agreed_suit(self) -> Suit:
        """Return a suit agreed by opener."""
        suit = None
        if len(self.bid_history) >= 5:
            opponents_bid_one = Bid(self.bid_history[0], '')
            opponents_bid_two = Bid(self.bid_history[2], '')
            opponents_bid_three = Bid(self.bid_history[4], '')
            if ((opponents_bid_one.denomination == opponents_bid_two.denomination) or
                    (opponents_bid_two.denomination == opponents_bid_three.denomination)):
                suit = opponents_bid_two.denomination
            if opponents_bid_one.is_double and opponents_bid_two.is_suit_call:
                suit = opponents_bid_two.denomination
        return suit

    def cheaper_suit(self, suit_one: Suit, suit_two: Suit) -> Suit:
        """Return the cheaper of two suits based on bid history."""
        suits = [suit_one, suit_two]
        suit = self.cheapest_suit(suits)
        return suit

    def next_four_card_suit(self) -> Suit:
        """Return the cheapest four card suit."""
        suits = []
        for suit in self.suits_by_length:
            if self.suit_length(suit) == 4:
                suits.append(suit)
        suit = self.cheapest_suit(suits)
        return suit

    def cheapest_suit(self, suits: list[Suit]) -> Suit:
        """Return the cheapest suit based on bid history."""
        suit_names = [(suit.name, suit.rank) for suit in suits]
        sorted_suits = sorted(suit_names, key=lambda tup: tup[1])
        suits = [Suit(suit[0]) for suit in sorted_suits]
        last_rank = self._last_bid_rank()
        if not suits:
            return None
        for suit in suits:
            if suit.rank > last_rank:
                break
        else:
            suit = suits[0]
        return suit

    def _last_bid_rank(self) -> int:
        """Return the rank of the last value bid."""
        bid = None
        for bid in self.bid_history[::-1]:
            if Call(bid).is_value_call:
                break
        last_rank = Call(bid).denomination.rank
        if last_rank == 4:
            last_rank = -1
        return last_rank

    @staticmethod
    def game_level(suit: Suit) -> int:
        """Return the level of game in the suit."""
        if suit.is_major:
            level = 4
        elif suit.is_minor:
            level = 5
        else:
            level = 3
        return level

    def bid_to_game(self,
                    denomination: Denomination,
                    comment: str = '0000',
                    use_distribution_points: bool = False) -> Bid | None:
        """Return game level bid in given denomination"""
        if denomination.is_nt:
            return Bid('3NT', comment, use_distribution_points)
        elif denomination.is_major:
            return Bid(self._call_name(4,  denomination.name), comment, use_distribution_points)
        elif denomination.is_minor:
            return Bid(self._call_name(5,  denomination.name), comment, use_distribution_points)
        return None

    @property
    def stoppers_in_bid_suits(self) -> bool:
        """Return True if hand contains stoppers in all opponent's bid suits."""
        return self._stoppers_in_bid_suits()

    @property
    def poor_stoppers_in_bid_suits(self) -> bool:
        """Return True if hand contains stoppers (including ten) in all opponent's bid suits."""
        return self._stoppers_in_bid_suits(lowest_card='T')

    def _stoppers_in_bid_suits(self, lowest_card='J'):
        """Return True if hand contains stoppers in all opponent's bid suits."""
        for suit in self.opponents_suits:
            if not self.suit_stopper(suit, lowest_card):
                return False
        return True

    def suit_stopper(self, suit: Suit, lowest_card: str = 'J') -> bool:
        """Return True if the hand contains a stopper in 'suit'."""
        if not suit:
            return False
        if not suit.is_suit:
            return False

        suit_holding = self.suit_holding
        if suit_holding[suit] >= 5:
            return True

        poor_stopper = False
        ace_stopper = Card('A', suit.name) in self.cards
        king_stopper = (Card('K', suit.name) in self.cards and suit_holding[suit] >= 2)
        queen_stopper = (Card('Q', suit.name) in self.cards and suit_holding[suit] >= 3)
        jack_stopper = (Card('J', suit.name) in self.cards and suit_holding[suit] >= 4)
        if lowest_card == 'T':
            poor_stopper = (Card('T', suit.name) in self.cards and suit_holding[suit] >= 4)
        if ace_stopper or king_stopper or queen_stopper or jack_stopper or poor_stopper:
            return True
        return False

    @property
    def unbid_suit(self) -> Suit:
        """Return the unbid _suit (if any) or None."""
        return self._unbid_suit()

    def _unbid_suit(self) -> Suit:
        """Return the unbid _suit (if any) or None."""
        suits = [suit for suit in self.suits]
        for bid in self.bid_history:
            bid_suit = Bid(bid).denomination
            if bid_suit in suits:
                suits.remove(bid_suit)
        if len(suits) == 1:
            return suits[0]
        return None

    def stoppers_in_unbid_suits(self) -> bool:
        """Return True if hand contains stoppers in all opponent's unbid suits."""
        bid_suits = []
        for bid in self.bid_history:
            bid_suit = Bid(bid).denomination
            if bid_suit.is_suit:
                bid_suits.append(bid_suit)
        for suit in self.suits:
            if suit not in bid_suits:
                if not self.suit_stopper(suit):
                    return False
        return True

    def stoppers_in_other_suits(self, suit) -> bool:
        """Return True if hand has stoppers in all suits except suit."""
        for test_suit in self.suits:
            if test_suit != suit:
                if not self.suit_stopper(test_suit):
                    return False
        return True

    def four_in_bid_suits(self, lowest_card='J') -> bool:
        """Return True if hand contains stoppers or 4 cards in all
            opponent's bid suits.
        """
        for suit in self.opponents_suits:
            if (not self.suit_stopper(suit, lowest_card) and
                    self.suit_holding[suit] <= 3):
                return False
        return True

    def three_suits_bid_and_stopper(self) -> bool:
        """Returns True if three suits bid and
                hand has an stopper in the unbid suit"""
        suits_bid = [False, False, False, False]
        for bid_name in self.bid_history[::2]:
            bid = Bid(bid_name)
            if bid.is_suit_call:
                suits_bid[bid.denomination.rank] = True
                suits_bid[bid.denomination.rank] = True
        if suits_bid.count(True) == 3:
            for index, suit_bid in enumerate(suits_bid):
                if not suit_bid:
                    suit = self.suits[index]
                    if self.suit_stopper(suit):
                        return True
                    if self.suit_points(suit) >= 1 and self.suit_holding[suit] >= 3:
                        return True
        return False

    def can_bid_suit(self, suit) -> bool:
        """Return False if suit is in opponents bids."""
        for bid in self.bid_history[::-1][::2]:
            if Bid(bid).is_suit_call:
                if suit == Bid(bid).denomination:
                    return False
        return True

    def has_stopper(self, suit) -> bool:
        """Return self.suit_stopper."""
        return self.suit_stopper(suit)

    def next_level(self, suit: Suit, raise_level: int = 0) -> bool:
        """Return the next next level for a suit bid."""
        level = self.next_level_bid(suit, '000', raise_level).level
        return level

    def current_bid_level(self) -> int:
        """Return the level of the latest quantitative bid."""
        bid = self._get_last_bid()
        return bid.level

    def next_level_bid(self,
                       suit: Suit,
                       comment: str = '0000',
                       raise_level: int = 0) -> int:
        """Return the lowest possible bid in suit."""
        last_bid = self._get_last_bid()
        level = self._get_Level_of_last_bid(last_bid)
        level += raise_level
        if last_bid.is_nt:
            level += 1
        elif suit and suit.is_suit:
            if last_bid.denomination >= suit:
                level += 1
        if level > 7:
            level = 7
        new_bid = Bid(self._call_name(level, suit.name), comment)
        return new_bid

    def _get_Level_of_last_bid(self, last_bid: Bid) -> int:
        """Return the level of the last bid."""
        if last_bid is None:
            return 1
        return last_bid.level

    def _get_last_bid(self) -> Bid | None:
        """Return last quantitative bid from history."""
        for bid_level in self.bid_history[::-1]:
            if bid_level != 'P' and bid_level != 'D' and bid_level != 'R':
                return Bid(bid_level, '0000')
        return None

    def next_nt_bid(self, comment: str = '0000', raise_level: int = 0) -> Bid:
        """Return the lowest possible bid in no trumps."""
        denomination = self.no_trumps
        bid = self.next_level_bid(denomination, comment, raise_level)
        return bid

    def responder_weak_bid(self) -> bool:
        """Responder has shown preference at  the lowest level."""
        overcallers_last_bid = Call(self.bid_history[-3])
        return (overcallers_last_bid.is_pass and
                self.partner_bid_one.is_pass and
                (self.partner_last_bid.denomination == self.opener_suit_one or
                 self.partner_last_bid.denomination == self.opener_suit_two) and
                not self.is_jump(self.opener_bid_two, self.partner_last_bid))

    def advancer_preference(self, call_id: str = '0000') -> Bid:
        """Respond after a 3 level bid make suit preference."""
        suit_one = self.overcaller_bid_one.denomination
        suit_two = self.overcaller_bid_two.denomination
        if self.overcaller_bid_one.is_double:
            suit_one = self.overcaller_bid_two.denomination
            suit_two = self.overcaller_bid_three.denomination

        if suit_one.is_major and self.suit_length(suit_one) >= 3:
            suit = suit_one
        elif self.suit_holding[suit_one] + 1 >= self.suit_holding[suit_two]:
            suit = suit_one
        else:
            suit = suit_two

        raise_level = 0
        if self.hcp >= 8 and self.next_level(suit) <= 3:
            raise_level = 1
        bid = self.next_level_bid(suit, call_id, raise_level=raise_level)
        self.tracer(__name__, inspect.currentframe(), bid, self.trace)
        return bid

    def unbid_four_card_major(self) -> Suit | None:
        """Return an unbid four card major or None."""
        bid_suits = [Bid(bid).denomination for bid in self.bid_history if Bid(bid).is_suit_call]
        if (self.hearts >= 4 and self.heart_suit not in bid_suits):
            return self.heart_suit
        elif (self.spades >= 4 and self.spade_suit not in bid_suits):
            return self.spade_suit
        return None

    @staticmethod
    def quantitative_raise(points: int, base_level: int,
                           point_list: list[int], maximum_level: int = 5) -> int:
        """
            Return a bid based on a quantitative raise.
            max raise is the number of elements in pointlist 1, 2,3 or 4
            scan the (reversed) points list until the points in
            the hand exceeds the level
            This shows whether it is a 3,2 or 1 raise etc.

            e.g.
            level = self.quantitative_raise(points, 1, [6, 10, 13, 16], 5)
            if points = 11 this raises level = 1+2 = 3.
        """
        maximum_raise = len(point_list)
        point_list = list(reversed(point_list))
        raise_level = 0
        for index, item in enumerate(point_list):
            if points >= item:
                raise_level = base_level + maximum_raise - index
                break
        if raise_level > maximum_level:
            raise_level = maximum_level
        return raise_level

    def hand_value_points(self, bid_suit: Suit) -> int:
        """Return the hand value points for the given suit."""
        hand_value_points = (self.hcp + self.support_shape_points(bid_suit))
        return hand_value_points

    def support_points(self, bidders_suit: Suit) -> int:
        """
        Calculate the sum of high card points and distribution points
        based on support_shape_points.
        """
        return self.high_card_points + self.support_shape_points(bidders_suit)

    def support_shape_points(self, bidders_suit: Suit) -> int:
        """
        Calculate the distribution points based on
        3 for a void, 2 for a singleton and 1 for a doubleton.
        """
        points = 0
        if bidders_suit.is_suit:
            if self._suit_support(bidders_suit):
                for index in range(4):
                    if self.shape[index] < 3:
                        points += 3 - self.shape[index]
        return points

    def _suit_support(self, bid_suit: Suit) -> bool:
        """Return True if the hand contains at least 3 of bid_suit."""
        if self.suit_holding[bid_suit] >= 3:
            return True
        return False

    @property
    def ordered_holding(self) -> list[list[int]]:
        """Returns suits and holdings in decreasing order of holding
            e.g. [[5, 1], [4, 0], [3, 2], [1, 3]].
        """
        holding = ([[self._spades, self.spade_suit],
                    [self._hearts, self.heart_suit],
                    [self._diamonds, self.diamond_suit],
                    [self._clubs, self.club_suit]])
        holding.sort(reverse=True)
        return holding

    def long_suit(self, minimum_holding: int) -> Suit | None:
        """Return the first suit with minimum_holding number of cards."""
        suit = None
        if self.spades >= minimum_holding:
            suit = self.spade_suit
        elif self.hearts >= minimum_holding:
            suit = self.heart_suit
        elif self.diamonds >= minimum_holding:
            suit = self.diamond_suit
        elif self.clubs >= minimum_holding:
            suit = self.club_suit
        return suit

    @property
    def suit_shape(self) -> list[int]:
        """Return a list of suits in decreasing order by holding."""
        shape = []
        for suit in self.ordered_holding:
            shape.append(suit[1])
        return shape

    @staticmethod
    def higher_ranking_suit(suit_one: Suit, suit_two: Suit) -> Suit:
        """Return the higher ranking of two suits."""
        if suit_one > suit_two:
            return suit_one
        return suit_two

    def has_sequence(self, suit) -> bool:
        """Return True if hand contains a three card sequence starting with
            an honour."""
        sequences = ['AKQ', 'KQJ', 'QJT', 'JT9', 'T98']
        cards = [card for card in self.cards if card.suit == suit]
        if len(cards) >= 3:
            for index, card in enumerate(cards[2:]):
                triple = cards[index].rank + cards[index+1].rank + card.rank
                if triple in sequences:
                    return True
        return False

    def suit_length(self, suit: Suit) -> int:
        """Return the length of a suit or a dummy value."""
        if suit.is_suit:
            return self.suit_holding[suit]
        return -999

    @staticmethod
    def _call_name(level, suit: Suit) -> str:
        """Return a call name form level and suit."""
        call_name = ''.join([str(level), suit])
        return call_name

    def double_allowed(self):
        bid_history = (['P', 'P', 'P'] + self.bid_history)[-3:]
        if bid_history[-1] in 'D' :
            return False
        if (bid_history[-3] in 'P' and
                bid_history[-2] in 'P' and
                bid_history[-1] in 'P'):
            return False
        if (bid_history[-3] not in 'P' and
                bid_history[-2] in 'P' and
                bid_history[-1] in 'P'):
            return True
        if (bid_history[-3] in 'P' and
                bid_history[-2] not in 'P' and
                bid_history[-1] in 'P'):
            return False
        if (bid_history[-2] not in 'P' and
                bid_history[-1] in 'P'):
            return False
        return True

    def redouble_allowed(self):
        bid_history = (['P', 'P', 'P'] + self.bid_history)[-3:]
        if bid_history[-1] == 'D':
            return True
        if (bid_history[-3] == 'D' and
                bid_history[-2] == 'P' and
                bid_history[-1]) == 'P':
            return True
        return False

    def tracer(self,
               module: str,
               get_frame: object,
               trace_value: str = '',
               display: bool = False,
               trace_message: str = '') -> None:
        """Print function trace information."""
        display_all = 1
        suppress_all = 0
        (source_file, display_file) = self._get_source_and_display(module)
        (call_id, call_name) = self._get_call_id_and_call_name(trace_value)

        if (not (display or display_all or self.force_trace(), display_file)
                or suppress_all):
            return
        hand = self.__str__()
        if hand != self.last_hand:
            if self.last_hand:
                print('')
            cprint(f'{hand}, {self.hcp}, {self.shape} {self.hcp=}', MODULE_COLOUR)
            self._set_trace_hand()
            self.last_hand = hand

        line_number = get_frame.f_lineno
        function = get_frame.f_code.co_name
        if trace_message:
            trace_message = ''.join([', ', trace_message])

        output_list = [
            f'{line_number:03d}',
            f'{call_id=}',
            source_file,
            f'{function:.<40}',
            f'{call_name}{trace_message}'
        ]
        print(', '.join(output_list))

    def force_trace(self) -> str | bool:
        try:
            with open(TRACE_PATH, 'r') as f_trace:
                trace_text = f_trace.read()
                if trace_text:
                    trace_value = True
                    return trace_value
        except FileNotFoundError:
            pass
        except NotADirectoryError:
            pass
        return False

    def _get_source_and_display(self, module: str) -> tuple[str, bool]:
        """Return a tuple (source_file, display)"""
        source_file = ''
        display = False
        if self.trace_module:
            source_file = module.replace('bfg_components.src.', '')
            if self.trace_module == source_file:
                display = True
        return (source_file, display)

    @staticmethod
    def _get_call_id_and_call_name(trace_value) -> tuple[str]:
        """Return a tuple (call_id, call_name)"""
        call_id = ''
        call_name = ''
        if isinstance(trace_value, Bid):
            call_id = trace_value.call_id
            call_name = trace_value.name
        return (call_id, call_name)

    def get_attributes_from_hand(self, hand):
        """Set the attributes of this object from a hand instance."""
        for key, item in hand.__dict__.items():
            self.__dict__[key] = item

    def _get_trace_module(self) -> tuple[str] | tuple[None]:
        """Return the name of the module to trace."""
        if os.path.isfile(MODULE_TRACE):
            with open(MODULE_TRACE, 'r') as f_trace_file:
                text = f_trace_file.read()
                text = text.split('\n')
                text.extend(['', ''])
                return (text[0], text[1])
        else:
            return (None, None)

    def _set_trace_hand(self) -> None:
        """Write the current hand to the trace file."""
        if os.path.isfile(MODULE_TRACE):
            with open(MODULE_TRACE, 'w') as f_trace_file:
                f_trace_file.write('\n'.join([self.trace_module, self.__str__()]))
