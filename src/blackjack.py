"""
blackjack.py

MVP of a blackjack engine
"""

import random
import pandas as pd

STANDARD_DECK = ["A", "10", "10", "10", "10", "9", "8", "7", "6", "5", "4", "3", "2"]*4 
BLACKJACK = {"A","10"}

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

        if contents is not None:
            self.stack = self.stack + contents

    def shuffle(self):
        random.shuffle(self.stack)
        return self

    def draw(self) -> str:
        if len(self.stack)==0: # inefficient to check this here
            print("Out of cards!") # move to game loop, track size there
            raise IndexError()

        card = self.stack.pop()

        return card


class Game(): 
    """
    How about this:

    A Game contains an array of hands to be played and a final set of hands

    While hands to be played:
    analyze hands
    append to final hands


    """
    def __init__(self, n_players:int = 1, deck=None, hands_per_player:int=2):
        self.dealer = Dealer()
        self.players = [Player(n_hands=hands_per_player) for x in range(n_players)]
        self.hands = []
        self.final_hands = []
        self.player_rule_location = "../data/basic_strategy_no_double_split.csv"
        self.dealer_rule_location = "../data/simple_dealer_s17_stand.csv"
        self.rule_set = self.get_rules(self.player_rule_location)
        self.dealer_rule_set = self.get_rules(self.dealer_rule_location, idx="DH")
        if deck is None:
            self.deck = Deck().shuffle()

    def perform_round(self):
        
        # Players bet
        for p in self.players:
            p.wager()

        self.dealer.hole = self.deck.draw()

        # Draw hands
        for p in self.players:
            p.deal_hands(self.deck)

        self.dealer.up = self.deck.draw()

        # Check for dealer blackjack

        dealer_has_blackjack = {self.dealer.hole, self.dealer.up}==BLACKJACK
        if dealer_has_blackjack:
            # If dealer has blackjack, just pass everyone's hands on to the final
            # list of hands and we will evaluate later
            # hack
            # ignoring insurance for now
            for p in self.players:
                p.final_hands = p.hands
            return None

        [print(p.hands) for p in self.players]
    
        for p in self.players:
            while p.hands:
                hand = p.hands.pop()

                # If you can split, and should split, do so and append two new hands
                if len(set(hand))==1: # can split
                    hand_string = hand[0] + "-" + hand[1]
                    
                    # TODO: if we're splitting aces, only get one card apiece

                    action = self.rule_set.loc[hand_string, self.dealer.up]
                    
                    if action == "spl": # should split
                        p.hands.append([hand[0], self.deck.draw()])
                        p.hands.append([hand[1], self.deck.draw()])
                        print("splitting, new stack of hands to deal:")
                        print(p.hands)
                        continue

                # If you can't split, figure out what your hand is and take the next step
        
                next_action = self.determine_hand_action(hand, self.dealer.up, self.rule_set)
                while (next_action!="-") and (next_action!="dbs"):
                    if next_action=="B":
                        # hand = ["BUSTED"]
                        next_action = "-"
                        continue
                    if next_action=="db":
                        hand.append(self.deck.draw())
                        next_action = "-"
                        print("DOUBLED, FIGURE OUT HOW TO CHANGE THAT BET")
                    if next_action=="h" or next_action=="sr":
                        hand.append(self.deck.draw())
                    next_action = self.determine_hand_action(hand, self.dealer.up, self.rule_set)

                p.final_hands.append(hand)
            
        # Dealer has to play their hand

        # Assess the final hands against the dealer hand
        self.assess_hand_against_dealer()

    def assess_hand_against_dealer(self):
        return 1
    
    @staticmethod
    def determine_hand_action(hand, up, rule_set) -> str:
        """
        Don't deal with splits here
        Return the action to take, given the dealer's up card and the rule set
        """
        action = ""
        is_hand_all_integers = all([isInteger(x) for x in hand])
        # If all cards are integers, return the sum
        if is_hand_all_integers:
            hand_value = sum([int(x) for x in hand])
            if hand_value<12:
                action = rule_set.loc[str(hand_value), up]
            elif hand_value>21:
                action = "B"
            else: 
                action = rule_set.loc["h"+str(hand_value), up]

            return action
        # If some cards are aces, figure out what the total is
        
        n_aces = sum([True if x == "A" else False for x in hand])

        if n_aces>0:
            ace_value = Game.figure_out_soft_hand(hand, n_aces)
            if ace_value=="B":
                action = "B"
            else:
                action = rule_set.loc[ace_value, up]
            return action

        print("hit an uncovered case")
        return None

    @classmethod
    def get_rules(cls, path:str, idx:str="PH") -> pd.DataFrame:
        return pd.read_csv(path, sep=";").set_index(idx)

    @classmethod
    def figure_out_soft_hand(cls, hand, n_aces:int):
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

        print("    final value: {}".format(final_value))
        return final_value

# class Agent
class Agent():
    def __init__(self, bank:float=100):
        self.bank=bank
        self.hand=None
        self.hand_value = None # parsed value that corresponds to rule set

# class Dealer sup Agent
class Dealer(Agent):
    def __init__(self):
        super().__init__()
        self.bank = 10E6
        self.up = None
        self.hole = None

# class Player sup Agent
class Player(Agent):
    def __init__(self, bank:float=100, n_hands:int=1):
        super().__init__(bank=bank)
        self.n_hands=n_hands
        self.hands=[]
        self.final_hands=[]
        self.wagers=[]
        self.bet_size=5
    
    def update_bet_size(self, game) -> float:
        """
        Update the bet size depending on game state. 
        Not implemented
        """
        raise NotImplementedError()

    def deal_hands(self, deck):
        self.hands = [[deck.draw(), deck.draw()] for n in range(self.n_hands)]

    def wager(self):
        self.wagers = [self.bet_size for n in range(self.n_hands)]
        



def main():
    deck = Deck()
    deck.shuffle()
    
    game = Game(n_players=2)
    game.perform_round()

    print("Dealer   UP {}   HOLE {}".format(game.dealer.up, game.dealer.hole))
    
    print("final hands")
    [print(p.final_hands) for p in game.players]

if __name__=="__main__":
    main()



