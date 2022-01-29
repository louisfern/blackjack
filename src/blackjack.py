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

    def draw(self) -> str:
        if len(self.stack)==0: # inefficient to check this here
            print("Out of cards!") # move to game loop, track size there
            raise IndexError()

        card = self.stack.pop()

        return card


class Game():
    def __init__(self, n_players:int = 1):
        self.dealer = Dealer()
        self.players = [Player()]*n_players
        self.rule_location = "../data/basic_strategy_no_double_split.csv"
        self.rule_set = self.get_rules(self.rule_location)
        self.dealt_hands = [] 
        

    def start_round(self, Deck):
        self.dealer.hole = Deck.draw()
        self.dealer.up = Deck.draw()
        for player in self.players:
            player.hand.append(Deck.draw())
            player.hand.append(Deck.draw())
        
    @classmethod
    def get_rules(cls, path:str) -> pd.DataFrame:
        return pd.read_csv(path, sep=";")

# class Evaluator

# class Agent
class Agent():
    def __init__(self, bank:int=100):
        self.bank=bank
        self.hand=None
        self.hand_value = None # parsed value that corresponds to rule set

    @staticmethod
    def determine_hand(hand) -> int:

        # Deal with splits ?!?!?
        is_hand_all_integers = all([isInteger(x) for x in hand])
        # If all cards are integers, return the sum
        if is_hand_all_integers:
            hand_value = sum([int(x) for x in hand])
        # If some cards are aces, figure out what the total is

        return hand_value

# class Dealer sup Agent
class Dealer(Agent):
    def __init__(self):
        super().__init__()
        self.bank = 10E6
        self.up = None
        self.hole = None

# class Player sup Agent
class Player(Agent):
    def __init__(self):
        super().__init__()
        self.hand=[]

def main():
    deck = Deck()
    deck.shuffle()
    
    game = Game(n_players=1)
    game.start_round(deck)

    print(game.dealer.up)
    print(game.dealer.hole)
    for p in game.players:
        print(p.hand)

if __name__=="__main__":
    main()




"""
How about this:

A Game contains an array of hands to be played and a final set of hands

While hands to be played:
analyze hands
append to final hands


"""