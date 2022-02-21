"""
blackjack.py

MVP of a blackjack engine

NOTES:

Each player has any number of hands. 
Each hand has an associated wager which is set before the hand is dealt. 
Need to be able to link directly between wagers and hands in order to pay out the players
This may require more sophistication in the Player object

Current state:
Players have a list of lists that represent the array of hands
Players have an array of floats, which contains each bet

Proposal: 
Players have an array of Hand objects
A Hand object contains a list (the hand) and a wager property (the bet)
Can move the "hand evaluation logic" to this class, perhaps?
"""

from copy import deepcopy
import logging
import random
import pandas as pd

STANDARD_DECK = ["A", "10", "10", "10", "10", "9", "8", "7", "6", "5", "4", "3", "2"]*4 
BLACKJACK = {"A","10"}

logging.basicConfig(level=logging.DEBUG, format='%(name)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

def isInteger(s:str)->bool:
    # taken from stack overflow
    try:
        int(s)
        return True
    except ValueError:
        return False

class Deck():
    def __init__(self, contents:str = STANDARD_DECK):
        self.stack = []
        self.n_cards = None

        if contents is not None:
            self.stack = self.stack + contents
            self.n_cards = len(contents)

    def shuffle(self):
        random.shuffle(self.stack)
        return self

    def draw(self) -> str:
        if len(self.stack)==0: # inefficient to check this here
            print("Out of cards!") # move to game loop, track size there
            raise IndexError()

        card = self.stack.pop()

        return card

    def check_shoe(self, discard, depth:float=.66):
        """
        If the fraction of remaining cards is lower than the minimum depth, shuffle discard back in
        """
        if (1-depth) > len(self.stack)/self.n_cards:
            logger.debug("shuffling discard back in")
            self.stack = random.shuffle(self.stack + discard.stack)
        return self

class Hand():
    """
    Proposal: 
    Players have an array of Hand objects
    A Hand object contains a list for the hand and a wager property
    The Hand class contains the logic for figuring out how to play a hand, given a rule set
    """
    def __init__(self, wager_size=1.0):
        self.wager_size = wager_size
        self.wager = wager_size
        self.hand = []
        self.is_blackjack = None
        self.can_split = None
        self.result = None
        self.hand_value = None

    def __repr__(self):
        rep = "WAGER: {}   HAND: {}".format(self.wager, self.hand)
        return rep

    def draw_hand(self, deck):
        self.hand = [deck.draw(), deck.draw()]
        self.is_hand_blackjack()
        self.can_split_hand()
        return self

    def is_hand_blackjack(self):
        self.is_blackjack = set(self.hand)==BLACKJACK
        return self

    def can_split_hand(self):
        self.can_split = len(set(self.hand))==1
        return self

    def double_down(self):
        self.wager += self.wager_size
        return self

    def determine_hand_action(self, up, rule_set) -> str:
        """
        Don't deal with splits here
        Return the action to take, given the dealer's up card and the rule set
        up: Dealer's upcard. If checking the dealer's hand, pass in "0". If player, use dealer's upcard. String
        rule_set: Dataframe of rule set
        """
        hand = self.hand
        action = ""
        is_hand_all_integers = all([isInteger(x) for x in hand])
        # If all cards are integers, return the sum
        if is_hand_all_integers:
            hand_value = sum([int(x) for x in hand])
            if hand_value<12:
                action = rule_set.loc[str(hand_value), up]
                if action=="db" and len(hand)>2:
                    action="h"
            elif hand_value>21:
                action = "B"
            else: 
                action = rule_set.loc["h"+str(hand_value), up]
            self.hand_value = hand_value
            return action
        # If some cards are aces, figure out what the total is
        
        n_aces = sum([True if x == "A" else False for x in hand])

        if n_aces>0:
            ace_value = Hand.figure_out_soft_hand(hand, n_aces)
            self.hand_value = int(ace_value[1:]) if ace_value[0] in ("s","h") else ace_value
            if ace_value=="B":
                action = "B"
            else:
                action = rule_set.loc[ace_value, up]
            return action

        print("hit an uncovered case")
        return -1

    def resolve_hand(self, dealer_up, rule_set, deck):
        """
        Method to determine the next action to take
        """
        next_action = self.determine_hand_action(dealer_up, rule_set)
        while (next_action!="-") and (next_action!="dbs"):
            if next_action=="B":
                next_action = "-"
                self.result = "bust"
                continue
            if next_action=="db":
                self.hand.append(deck.draw())
                next_action = "-"
                self.double_down()
            if next_action=="h" or next_action=="sr":
                self.hand.append(deck.draw())
            next_action = self.determine_hand_action(dealer_up, rule_set)

        return self

    @classmethod
    def figure_out_soft_hand(cls, hand, n_aces:int, debug:bool=False):
        """
        1. split hand into aces and other
        2. compute total value of other
        3. Find max of aces + other GIVEN
            value of aces IS 
            val = []
                for n in n_aces:1:
                    val.append = 11*n + (n_aces-n)
        4. Return as s[total] 
        """
        non_aces = [x for x in hand if x!="A"]
        other_value = sum([int(x) for x in non_aces])
        aces_values = [m*11 + (n_aces-m)*1 for m in range(0,n_aces+1,1)]

        total_values = [x + other_value for x in aces_values]

        if debug is True:
            print("ace evaluation:")
            print("    hand: {}".format(hand))
            print("    total values: {}".format(total_values))

        hand_values = [x for x in total_values if x<22]
        if hand_values:
            hand_value = max(hand_values)

            hard_or_soft = "s" if hand_value-other_value>=11 else "h" # should actually be a multiple of 11

            final_value = hard_or_soft + str(hand_value)
        
        else:
            final_value = "B"

        if debug is True:
            logger.debug("final value: {}".format(final_value))

        return final_value



class Game(): 
    """
    How about this:

    A Game contains an array of hands to be played and a final set of hands

    While hands to be played:
    analyze hands
    append to final hands

    params:
    players: mutually exclusive with n_players. List of Player objects
    n_players: mutually exclusive with players. Int number of players to create
    deck: Deck object to use
    hands_per_player: Number of hands to play per player
    
    """
    def __init__(self, 
                 players=None, 
                 n_players:int=1, 
                 deck=None, 
                 discard=None,
                 hands_per_player:int=2):
        self.dealer = Dealer()
        if players is None:
            self.players = [Player(n_hands=hands_per_player) for x in range(n_players)]
        else:
            self.players = players
        self.hands = []
        self.final_hands = []
        self.player_rule_location = "../data/basic_strategy_no_double_split.csv"
        self.dealer_rule_location = "../data/simple_dealer_s17_stand.csv"
        self.rule_set = self.get_rules(self.player_rule_location)
        self.dealer_rule_set = self.get_rules(self.dealer_rule_location, idx="DH")
        if deck is None:
            self.deck = Deck().shuffle()
        else:
            self.deck = deck
        if discard is None:
            self.discard = Deck(contents=None)
        else:
            self.discard = discard

    def perform_round(self, debug=False):
        
        # Players bet
        self.dealer.hole = self.deck.draw()

        # Draw hands
        for p in self.players:
            p.deal_hands(self.deck)

        self.dealer.up = self.deck.draw()

        # Hack a Hand object into existence for the dealer
        dealer_hand = Hand()
        dealer_hand.hand = [self.dealer.up, self.dealer.hole]
        dealer_hand.is_hand_blackjack()

        self.dealer.hand = dealer_hand
        """
        # Check for dealer blackjack
        if self.dealer.hand.is_blackjack:
            # If dealer has blackjack, just pass everyone's hands on to the final
            # list of hands and we will evaluate later
            # HACK
            # ignoring insurance for now
            for p in self.players:
                p.final_hands = p.hands
            return None
        """

        if debug:
            print("Dealer hand:")
            print(self.dealer.hand)
            print("Player hands:")
            [print(p.hands) for p in self.players]
    
        for p in self.players:
            while p.hands:
                hand = p.hands.pop()
                # TODO splitting appears to be broken...
                # If you can split, and should split, do so and append two new hands
                if hand.can_split: # can split
                    
                    hand_string = hand.hand[0] + "-" + hand.hand[1]
                    
                    # TODO: if we're splitting aces, only get one card apiece

                    action = self.rule_set.loc[hand_string, self.dealer.up]
                    
                    if action == "spl": # should split
                        logger.debug("split")
                        logger.debug(repr(hand))
                        new_hand_1 = deepcopy(hand)
                        new_hand_2 = deepcopy(hand)
                        
                        new_hand_1.hand = [hand.hand[0], self.deck.draw()]
                        new_hand_1.can_split_hand()

                        new_hand_2.hand = [hand.hand[1], self.deck.draw()]
                        new_hand_2.can_split_hand()

                        p.hands.append(new_hand_1)
                        p.hands.append(new_hand_2)
                        logger.debug("Number of hands in queue: {}".format(len(p.hands)))
                        continue
                
            hand.resolve_hand(self.dealer.up, self.rule_set, self.deck)
                
            p.final_hands.append(hand)
            
        # Dealer has to play their hand
        self.dealer.hand.resolve_hand("0", self.dealer_rule_set, self.deck)
        
        # Assess the final hands against the dealer hand
        self.assess_hands_against_dealer(debug=debug)

        if debug:
            print("Player hands: ---------")
            for p in self.players:
                print(repr(p))

            print("Dealer hand: ---------")
            print(repr(self.dealer.hand))

        # Cleanup step
        for p in self.players:
            p.clear_hands(self.discard)

        self.dealer.clear_hands(self.discard)

        return None

    def assess_hands_against_dealer(self, debug=False):
        """
        1. Remove any player hands that outright busted
        2. Check for dealer blackjack. 
            If dealer has blackjack, check each player/hand for blackjack
                If blackjack, push, else, bust
        3. If dealer busted, remaining hands win
        4. If dealer didn't bust, compare to dealer
            > dealer, win
            < dealer, bust
            == dealer, push

        TODO: How can I rewrite this as a matrix or dataframe operation?
        """

        dealer_value = self.dealer.hand.hand_value

        # Remove any player hands that outright busted        
        for p in self.players:
            for h in p.final_hands:
                if h.hand_value == "B":
                    h.result = "bust"
                
                if h.result == "bust":
                    p.bust_hand(h)
                    if debug:
                        print("Busting player hand")

        # Check for dealer blackjack. 
        for p in self.players:
            for h in p.final_hands:
                if self.dealer.hand.is_blackjack:
                    if h.is_blackjack:
                        h.result = "push"
                        p.push_hand(h)
                        if debug:
                           print("Player push on dealer blackjack")
                    else:
                        h.result = "bust"
                        p.bust_hand(h)
                        if debug:
                            print("Player loses to dealer blackjack")

                    return self

        # If dealer busted, remaining hands win
        if self.dealer.hand.result in ("bust", "B"):
            for p in self.players:
                for h in p.final_hands:
                    if h.is_blackjack:
                        p.blackjack(h)
                        h.result="blackjack"
                        if debug:
                            print("Player blackjack on dealer bust")
                    else:
                        if h.result!="bust":
                            p.win_hand(h)
                            h.result="win"
                            if debug:
                                print("Player wins on dealer bust")
        else:
            for p in self.players:
                for h in p.final_hands:
                    if h.is_blackjack:
                        p.blackjack(h)
                        h.result="blackjack"
                        if debug:
                            print("Player blackjack paying out")
                    else:
                        if h.result!="bust":
                            if h.hand_value==dealer_value:
                                h.result="push"
                                p.push_hand(h)
                                if debug:
                                    print("Player push")
                            if h.hand_value>dealer_value:
                                h.result="win"
                                p.win_hand(h)
                                if debug:
                                    print("Player beats dealer")
                            if h.hand_value<dealer_value:
                                h.result="bust"
                                p.bust_hand(h)
                                if debug:
                                    print("Player loses to dealer")
        # If dealer didn't bust, compare to dealer

        return self
    
    def update_wagers(self):
        return 1
    
    @classmethod
    def get_rules(cls, path:str, idx:str="PH") -> pd.DataFrame:
        return pd.read_csv(path, sep=";").set_index(idx)


# class Agent
class Agent():
    def __init__(self, bank:float=100):
        self.bank=bank
        self.hand=None
        self.hand_value = None # parsed value that corresponds to rule set

    def clear_hands(self):
        raise NotImplementedError

# class Dealer sup Agent
class Dealer(Agent):
    def __init__(self):
        super().__init__()
        self.bank = 10E6
        self.up = None
        self.hole = None
        self.hand = None

    def clear_hands(self, deck):
        deck.stack+=self.hand.hand
        self.hand=[]
        self.hole=None
        self.hand=None
        
# class Player sup Agent
class Player(Agent):
    def __init__(self, bank:float=100, n_hands:int=1, bet_size:float=5.0):
        super().__init__(bank=bank)
        self.n_hands=n_hands
        self.hands=[]
        self.final_hands=[]
        self.bet_size=bet_size

    def __repr__(self):
        s1 = "Player debug log:"
        s0 = " bank: {}".format(self.bank)
        s2 = [repr(h) for h in self.hands]
        s3 = [repr(h) for h in self.final_hands]
        s4 = " ".join(s2)
        s5 = " ".join(s3)
        ret = s1 + s0 + " Undealt hands: " + s4 + " Final hands: " + s5
        return ret
        
    
    def update_bet_size(self, game) -> float:
        """
        Update the bet size depending on game state. 
        Not implemented
        """
        raise NotImplementedError()

    def deal_hands(self, deck):
        self.hands = [Hand(wager_size=self.bet_size).draw_hand(deck) for n in range(self.n_hands)]
        self.bank -= self.bet_size*self.n_hands

    def bust_hand(self, hand):
        """
        To do: implement a "return to the deck" functionality
        """
        # self.bank -= hand.wager
        # Don't need to remove the wager, it's already been anted
        return self

    def win_hand(self, hand):
        self.bank += hand.wager*2
        return self

    def push_hand(self, hand):
        self.bank += hand.wager

    def blackjack(self, hand):
        self.bank += hand.wager*2.5

    def clear_hands(self, deck):
        for h in self.hands:
            deck.stack+=h.hand
        self.hands = []
        for h in self.final_hands:
            deck.stack+=h.hand
        self.final_hands = []




def main():
    deck = Deck(contents=STANDARD_DECK*6)
    deck.shuffle()
    discard = Deck(contents=None)
    p1 = Player(n_hands=2)
    p2 = Player(n_hands=2)
    n_rounds = 100
    logger.debug("Running {} rounds".format(n_rounds))
    players = [p1, p2]
    game = Game(players=players, deck=deck, discard=discard)
    for i in range(n_rounds):
        deck.check_shoe(discard, depth=.66)
        logger.debug(len(deck.stack))
        game.perform_round(debug=False)
    

if __name__=="__main__":
    main()



