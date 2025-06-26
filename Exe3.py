import random
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.patches import FancyBboxPatch

#---CARD---
class Card:
    def __init__(self, rank, suit):
        self.suit = suit
        self.rank = rank
    def __str__(self): return f"{self.rank}{self.suit}"

#---Deck---
class Deck:
    SUITS = ['♠', '♥', '♦', '♣']
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

    def __init__(self, seed=None):
        self.rng = random.Random(seed)  # always use this RNG
        self.seed = seed
        self.reset_and_shuffle()

    def reset_and_shuffle(self):
        self.cards = [Card(rank, suit) for suit in self.SUITS for rank in self.RANKS]
        self.rng.shuffle(self.cards)

    def deal_card(self):
        if len(self.cards) < 20:
            self.reset_and_shuffle()
        return self.cards.pop(0)


#---Hand---
class Hand:
    def __init__(self):
        self.cards = []
    def add_card(self, card): self.cards.append(card)
    def reset(self): self.cards.clear()

    def get_value(self):
        val, aces = 0, 0
        for card in self.cards:
            if card.rank in ['J', 'Q', 'K']: val += 10
            elif card.rank == 'A': val += 11; aces += 1
            else: val += int(card.rank)
        while val > 21 and aces: val -= 10; aces -= 1
        return val
    def show(self): return [str(c) for c in self.cards]

#---Player---
class Player:
    def __init__(self, name, chips):
        self.name, self.chips = name, chips
        self.hand, self.bet, self.total_invested = Hand(), 0, chips
    def place_bet(self, amount):
        if 1 <= amount <= self.chips:
            self.bet = amount
            self.chips -= amount
            return True
        return False
    def has_bust(self): return self.hand.get_value() > 21
    def reset_hand(self): self.hand.reset(); self.bet = 0

#---Bot---
class Bot(Player):
    def __init__(self, name, chips, seed):
        super().__init__(name, chips)
        self.rng = random.Random(seed)
    def place_random_bet(self):
        b = self.rng.randint(1, self.chips if self.chips else 1)
        self.place_bet(b)
        return b
    def decide_move(self): return 'hit' if self.hand.get_value() < 17 else 'stand'
    def rebuy(self):
        if self.chips == 0:
            self.chips = self.total_invested
            self.total_invested *= 2
            return True
        return False

#---Dealer---
class Dealer(Player):
    def __init__(self):
        super().__init__('Dealer', 0)
        self.hidden_card = None
    def set_hidden_card(self, card): self.hidden_card = card
    def get_hidden(self): return self.hidden_card
    def reveal_hidden_card(self):
        if self.hidden_card: self.hand.add_card(self.hidden_card)
        self.hidden_card = None
    def should_draw(self): return self.hand.get_value() < 17

#---GameManager---
class Game:
    def __init__(self):
        self.deck = None
        self.player = None
        self.bots = []
        self.dealer = Dealer()
        self.sits = []
        self.game_seed = None

    def setup(self):
        name = input("Enter your name: ")
        while True:
            try:
                chips = int(input("Enter the amount of chips: "))
                if 100 <= chips <= 1000: break
                print("Please enter a number between 100 and 1000.")
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        self.player = Player(name, chips)

        player_seat = -1
        while True:
            seat_input = input("Where would you like to sit? (Choose a seat number from 1 to 3): ")
            if seat_input.isdigit() and 1 <= int(seat_input) <= 3:
                player_seat = int(seat_input)
                break
            print("Please enter a number between 1 and 3.")

        self.sits = [None, None, None]
        self.sits[player_seat - 1] = self.player

        try:
            with open("bots.txt") as bot_file:
                for line in bot_file:
                    if len(self.bots) >= 2: break
                    name, chips, seed = line.strip().split(',')
                    self.bots.append(Bot(name, int(chips), int(seed)))
                    print(f"{name} now has {chips} chips.")
        except FileNotFoundError:
            print("File not found: bots.txt")

        print("Welcome to Blackjack!")
        print("Nothing is left to chance when you are an engineer.")
        while True:
            try:
                self.game_seed = int(input("Enter a seed value for the game: "))
                self.deck = Deck(self.game_seed)
                break
            except ValueError:
                print("Invalid input. Please enter a valid integer.")

        self.play()
        self.show_summary()

    def play(self):
          while True:
            if self.player.chips == 0:
                r = input(f"{self.player.name}, you have 0 chips.\nYou have no chips left. Do you want to buy more? (yes/no): ").lower()
                if r.startswith('y'):
                    while True:
                        try:
                            amt = int(input("Enter amount of chips to add: "))
                            if 100 <= amt <= 1000:
                                self.player.chips += amt
                                self.player.total_invested += amt
                                break
                            else:
                                print("Please enter a number between 100 and 1000.")
                        except ValueError:
                            print("Please enter a number between 100 and 1000.")
                else:
                    break

            while True:
                print(f"\n{self.player.name}, you have {self.player.chips} chips.")
                response = input("Do you want to play a round? (yes/no): ").strip().lower()
                if response == 'yes':
                    self.round()
                    break
                elif response == 'no':
                    print("You chose to leave the table.")
                    return
                else:
                    print("Please enter one of the following: yes, no")

    def round(self):
        self.player.reset_hand()
        for b in self.bots: b.reset_hand()
        self.dealer.reset_hand()
        dv = self.dealer.hand.get_value()

        while True:
            try:
                bet = int(input(f"{self.player.name}, enter your bet (1 - {self.player.chips}): "))
                if 1 <= bet <= self.player.chips:
                    self.player.bet = bet
                    self.player.chips -= bet
                    print(f"{self.player.name} now has {self.player.chips} chips.")
                    break
                else:
                    print(f"Please enter a number between (1 - {self.player.chips}): ")
            except ValueError:
                print("Invalid input. Please enter a valid integer.")

        for b in self.bots:
            if b.chips == 0:
               if b.rebuy():
                   print(f"{b.name} was out of chips and added {b.chips} more chips.")
            print(f"{b.name} bets {b.place_random_bet()} chips and now has {b.chips} chips.")

        for _ in range(2):
            self.player.hand.add_card(self.deck.deal_card())
            for b in self.bots: b.hand.add_card(self.deck.deal_card())
            c = self.deck.deal_card()
            if _ == 0: self.dealer.hand.add_card(c)
            else: self.dealer.set_hidden_card(c)
        print(f"\nYou got: {self.player.hand.show()} (value: {self.player.hand.get_value()})")

        for b in self.bots:
            print(f"{b.name} hand: {b.hand.show()} (value: {b.hand.get_value()})")
        print(f"\nDealer shows: {self.dealer.hand.show()[0]}\n")

        while not self.player.has_bust():
            move = input("Do you want to 'hit' or 'stand'? ").lower().strip()
            if move == 'stand':
                break
            elif move == 'hit':
                c = self.deck.deal_card()
                self.player.hand.add_card(c)
                print(f"You drew: {c}")
                print(f"New hand: {self.player.hand.show()} (value: {self.player.hand.get_value()})")
            else:
                print("Please enter one of the following: hit, stand")

        for b in self.bots:
            print(f"\n{b.name}'s turn:")
            while b.decide_move() == "hit":
                card = self.deck.deal_card()
                b.hand.add_card(card)
                print(f"{b.name} draws: {card}")
            print(f"{b.name} stands. Hand: {b.hand.show()} (value: {b.hand.get_value()})")

        print(f"\nDealer reveals hidden card: {self.dealer.get_hidden()}")
        self.dealer.reveal_hidden_card()
        print(f"Dealer's hand: {self.dealer.hand.show()} (value: {self.dealer.hand.get_value()})")
        while self.dealer.should_draw():
            c = self.deck.deal_card()
            self.dealer.hand.add_card(c)
            print(f"Dealer draws a: {c}")
            print(f"Dealer now has: {self.dealer.hand.show()} (value: {self.dealer.hand.get_value()})")
        self.results()

    def results(self):
        dealer_value = self.dealer.hand.get_value()
        print(f"\nYour final hand value: {self.player.hand.get_value()}")
        if self.player.has_bust():
            print("You busted and lost your bet.")
        elif self.dealer.has_bust() or self.player.hand.get_value() > dealer_value:
            self.player.chips += self.player.bet * 2
            print(f"You win! You now have {self.player.chips} chips.")
        elif self.player.hand.get_value() == dealer_value:
            self.player.chips += self.player.bet
            print(f"It's a tie. You get your bet back. Total chips:{self.player.chips}")
        else:
            print("You lost this round.")

        for b in self.bots:
            bot_value = b.hand.get_value()

            if b.has_bust():
                print(f"{b.name} had {bot_value} -> busted and lost.")
            elif self.dealer.has_bust() or bot_value > dealer_value:
                b.chips += b.bet * 2
                print(f"{b.name} had {bot_value} -> won and now has {b.chips} chips.")
            elif bot_value == dealer_value:
                b.chips += b.bet
                print(f"{b.name} had {bot_value} -> tied and got their bet back. Total: {b.chips}.")
            else:
                print(f"{b.name} had {bot_value} -> lost this round.")


            b.bet = 0

    def show_summary(self):
        players = [self.player] + self.bots
        chips = np.array([p.chips for p in players])
        invested = np.array([p.total_invested for p in players])
        roi = np.divide(chips, invested, out=np.zeros_like(chips, dtype=float), where=invested!=0)
        order = np.argsort(-roi)

        print("\n--- Game Summary ---")

        for p in players:
            print(f"{p.name}: {p.chips} chips")
        print(f"\nAverage chips: {np.mean(chips):.2f}")
        print(f"Highest chip count: {np.max(chips)}")

        print("\nPlayer ranking (highest to lowest):")

        for i, idx in enumerate(order):
            p = players[idx]
            print(f"{i + 1}. {p.name} - Chips: {p.chips}, Invested: {p.total_invested}, Return Rate: {roi[idx]:.2f}")
        seating_order = [i for i, p in enumerate(self.sits) if p is not None]
        ranking_dict = {players[idx].name: i + 1 for i, idx in enumerate(order)}
        self.create_table_summary(players, ranking_dict, self.player)
        print("Table image with seating and rankings saved as 'table_summary.png'")

    def create_table_summary(self, players, ranking, main_player):
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_facecolor('seagreen')
        ax.set_aspect('equal')
        plt.axis('off')

        table_circle = patches.Circle((0.5, 0.5), 0.225, color='forestgreen')
        ax.add_patch(table_circle)
        ax.set_aspect('auto')

        seats_pos = {
            1: (0.8, 0.5),  # right
            2: (0.5, 0.15),  # bottom
            3: (0.15, 0.5),  # left
        }

        for i, player in enumerate(players):
            x, y = seats_pos[i + 1]
            label_name = f"{player.name} (you)" if player == main_player else player.name
            box_color = 'gold' if player == main_player else 'red'

            rect = FancyBboxPatch((x - 0.12, y - 0.06), 0.24, 0.12,
                                  boxstyle="round,pad=0.02",
                                  fc=box_color, ec='black', lw=2, zorder=2)
            ax.add_patch(rect)

            player_rank = ranking.get(player.name, '?')
            text = f"{label_name}\n#{player_rank}\n{player.chips} chips"
            ax.text(x, y + 0.005, text, ha='center', va='center', fontsize=10, color='black', weight='bold')

        plt.savefig("table_summary.png", dpi=150)
        plt.close()


if __name__ == '__main__':
    Game().setup()
