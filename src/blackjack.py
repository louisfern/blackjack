"""
blackjack.py

MVP of a blackjack engine
"""

import random
import pandas as pd

STANDARD_DECK = ["A", "10", "10", "10", "10", "9", "8", "7", "6", "5", "4", "3", "2"]*4 

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
    def __init__(self, n_players:int = 1, deck=None):
        self.dealer = Dealer()
        self.n_players = n_players
        self.hands = []
        self.final_hands = []
        self.rule_location = "../data/basic_strategy_no_double_split.csv"
        self.rule_set = self.get_rules(self.rule_location)
        if deck is None:
            self.deck = Deck().shuffle()

    def perform_round(self):
        self.dealer.hole = self.deck.draw()

        self.hands = [[self.deck.draw(), self.deck.draw()] for x in range(self.n_players)]

        self.dealer.up = self.deck.draw()

        # Check for dealer blackjack
        print(self.hands)

        while self.hands:
            hand = self.hands.pop()

            # If you can split, and should split, do so and append two new hands
            if len(set(hand))==1: # can split
                hand_string = hand[0] + "-" + hand[1]
                
                action = self.rule_set.loc[hand_string, self.dealer.up]
                
                if action == "spl": # should split
                    self.hands.append([hand[0], self.deck.draw()])
                    self.hands.append([hand[1], self.deck.draw()])
                    print("splitting, new stack of hands to deal:")
                    print(self.hands)
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

            self.final_hands.append(hand)
    
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
    def get_rules(cls, path:str) -> pd.DataFrame:
        return pd.read_csv(path, sep=";").set_index("PH")

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
    def __init__(self, bank:int=100):
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

def main():
    deck = Deck()
    deck.shuffle()
    
    game = Game(n_players=2)
    game.perform_round()

    print("Dealer   UP {}   HOLE {}".format(game.dealer.up, game.dealer.hole))
    
    print("final hands")
    print(game.final_hands)

if __name__=="__main__":
    main()



