""" Bid for Game
    Bridge objects
"""

from bridgeobjects import Card, SUITS, Hand, Suit
from bridgeobjects import Call
from .comments import comment_id, comment_html, strategy_html
# from .strategy_xref import StrategyXref


class Bid(Call):
    """Return BfG Bid class."""
    def __init__(self, name: str = '',
                 call_id: str = '0000',
                 use_shortage_points:
                 bool = False,
                 *args,
                 **kwargs) -> None:
        super().__init__(name, *args, **kwargs)
        self.use_shortage_points: bool = use_shortage_points
        self.rtf_comment: str = ''
        self.rtf_strategy: str = ''
        # if call_id not in CommentXref.comments:
        #     call_id = '0000'
        self.call_id: str = call_id

        # the comments dict contains a gettext reference to the comment/strategy text.
        self.comment_id: str = ''
        self.strategy_id: str = ''
        self.comment_html: str = ''
        self.strategy_html: str = ''
        self.comment_rst: str = ''
        self.strategy_rst: str = ''

    def __repr__(self) -> str:
        """Return a __repr__ display value of object."""
        return f'bid: {self._name}, {self.call_id}'

    def get_comments(self) -> None:
        """Get the bid comments from the x_refs."""
        self.comment_id = comment_id(self.call_id)
        self.comment_html = comment_html(self.call_id)
        self.strategy_html = strategy_html(self.call_id)

        self.comment_rst = self._convert_html_to_rst(self.comment_html)
        self.strategy_rst = self._convert_html_to_rst(self.strategy_html)

    @staticmethod
    def _convert_html_to_rst(html: str) -> str:
        """Return and html_string as rst."""
        rst = html.replace('<br>', '\n')
        rst = rst.replace('<p> ', '<p>')
        rst = rst.replace('<p>', '\n\n')
        rst = rst.replace('<span style="color:red">', '**')
        rst = rst.replace('<span style="color:green">', '**')
        rst = rst.replace('</span>', '**')
        return rst


class Pass(Bid):
    """Class definition for PASS bid."""
    def __init__(self, call_id: str = '0000', use_shortage_points: bool = False, *args, **kwargs):
        super(Pass, self).__init__(name='P', call_id=call_id,
                                   use_shortage_points=use_shortage_points, *args, **kwargs)
        pass


class Double(Bid):
    """Class definition for DOUBLE bid."""
    def __init__(self, call_id: str = '0000', use_shortage_points: bool = False, *args, **kwargs):
        super(Double, self).__init__(name='D', call_id=call_id,
                                     use_shortage_points=use_shortage_points, *args, **kwargs)
        pass


class HandSuit(object):
    """Instantiate BfG HandSuit class."""
    SUITS = {'NT': -1, 'S': 0, 'H': 1, 'D': 2, 'C': 3, -1: 'NT', 0: 'S', 1: 'H', 2: 'D', 3: 'C'}

    def __init__(self, suit: Suit | None = None,
                 hand: Hand | None = None,
                 bid_history: list[str] = None):
        """Initialise class."""
        self.suit = suit
        self.name = suit.name
        self.cards = []
        self._card_list = []
        if hand:
            self.cards = hand.cards
            self._card_list = [card for card in hand.cards if card.suit == suit]
        if not bid_history:
            bid_history = []
        self.bid_history = bid_history
        self.honours = 0
        self.touching_honours = 0
        self.honour_points = 0
        self.ace_as_single_honour = False
        self.highest_touching_honour = -1
        if self._card_list:
            self.honours = self._honours()
            self.touching_honours = self._touching_honours()
            self.highest_touching_honour = self._highest_touching_honour()
            self.ace_as_single_honour = self._ace_as_single_honour()
            self.length = len(self._card_list)
            self.honour_points = self._honour_points()
        if bid_history:
            (self.partners_bid, self.opponents_bid) = self._get_bids()

    def __repr__(self) -> str:
        """Return a __repr__ display value of object."""
        return 'HandSuit: %s' % self.name

    def suit_quality(self) -> int:
        """Return the suit quality."""
        quality = 0
        if Card('A', self.suit.name) in self._card_list:
            quality += 1
        if Card('K', self.suit.name) in self._card_list:
            quality += 1
        if Card('Q', self.suit.name) in self._card_list:
            quality += 0.5
        if Card('J', self.suit.name) in self._card_list:
            quality += 0.5
        return quality

    def has_control(self, hand: Hand) -> bool:
        """Return True if hand has control of that suit."""
        suit = self.suit
        if Card('A', suit.name) in self.cards:
            return True
        elif (Card('K', suit.name) in self.cards and
              hand.suit_holding[suit] >= 2):
            return True
        elif (Card('Q', suit.name) in self.cards and
              hand.suit_holding[suit] > 3):
            return True
        elif (Card('J', suit.name) in self.cards and
              hand.suit_holding[suit] >= 4):
            return True
        return False

    def _touching_honours(self) -> int:
        touching_pairs = ['AK', 'KQ', 'QJ', 'JT']
        touching_honours = 1
        touching_honours_hold = 1
        for index, card in enumerate(self._card_list[1:]):
            if self._card_list[index].rank + card.rank in touching_pairs:
                touching_honours += 1
            else:
                if touching_honours_hold < touching_honours:
                    touching_honours_hold = touching_honours
                touching_honours = 1
        touching_honours = max(touching_honours, touching_honours_hold)
        return touching_honours

    def _highest_touching_honour(self) -> Card | None:
        highest_touching_honour = None
        if self.cards and self.touching_honours > 1:
            highest_touching_honour = self.cards[0]
            for card in self.cards:
                if card.value == 13 - highest_touching_honour.value:
                    highest_touching_honour = card
                    break
        return highest_touching_honour

    def _ace_as_single_honour(self) -> bool:
        result = False
        for card in self._card_list:
            if card.name == 'A':
                result = True
            elif card.name in ['TJQK']:
                result = False
                break
        return result

    def _honours(self) -> int:
        """Return the number of honours in hand_suit including tens."""
        honours = 0
        for card in self._card_list:
            if card.value >= 9:
                honours += 1
        return honours

    def _honour_points(self) -> int:
        value = 0
        for index, card in enumerate(self._card_list[:5]):
            if card:
                value += 4 - index
        return value

    def _get_bids(self) -> tuple[bool]:
        (partners_bid, opponents_bid) = (False, False)
        bid_history = list(reversed(self.bid_history[:-3]))
        offset = 0
        contract_suit = self._suit_from_bid(bid_history[0])
        for index, bid in enumerate(bid_history[0::2]):
            suit = self._suit_from_bid(bid)
            if suit == self.suit:
                opponents_bid = True
            if contract_suit == self._suit_from_bid(bid):
                offset = index % 2

        for bid in bid_history[offset*2+1::4]:
            suit = self._suit_from_bid(bid)
            if suit == self.suit:
                partners_bid = True

        return (partners_bid, opponents_bid)

    @staticmethod
    def _suit_from_bid(bid: str) -> Suit | int | None:
        """Return suit from a bid."""
        suit = None
        if len(bid) == 2:
            suit = SUITS[bid[1]].name
        elif len(bid) == 2:
            suit = -1
        return suit
