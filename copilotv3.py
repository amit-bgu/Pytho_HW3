import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch

class Card:
    def __init__(self, rank, suit):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f"{self.rank}{self.suit}"

class Deck:
    def __init__(self, seed):
        card_ranks = [2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K", "A"]
        card_suits = ["♠", "♥", "♦", "♣"]
        self.cards = []
        self.seed = seed

        for suit in card_suits:
            for rank in card_ranks:
                self.cards.append(Card(rank, suit))
        random.seed(self.seed)
        random.shuffle(self.cards)

    def shuffle(self):

        random.shuffle(self.cards)
        print("[[THE DECK WAS SHUFFLED]]")

    def deal_card(self):
        return self.cards.pop(0)

    def recreate_and_shuffle(self):
        """ מאפס את החפיסה לסדר קבוע ומערבב אותה """
        card_ranks = [2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K", "A"]
        card_suits = ["♠", "♥", "♦", "♣"]
        self.cards = []
        for suit in card_suits:
            for rank in card_ranks:
                self.cards.append(Card(rank, suit))
        self.shuffle()

class Hand:
    def __init__(self):
        self.cards = []
        self.is_ace = None
        self.value = None

    def add_card(self, card):
        self.cards.append(card)

    def reset(self):
        self.cards = []

    def get_value(self):
        value = 0
        aces = 0
        for card in self.cards:
            if card.rank in ["J", "Q", "K"]:
                value += 10
            elif card.rank == "A":
                value += 11
                aces += 1
            else:
                value += int(card.rank)

        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        self.value = value
        return value

    def __str__(self):
        return "[" + ', '.join(f"'{card}'" for card in self.cards) + "]"

class Player:
    def __init__(self, name, chips, bet):
        self.name = name
        self.chips = chips
        self.hand = Hand()
        self.bet = bet
        self.status = None
        self.total_invested = chips

    def place_hand(self):
        self.chips -= self.bet

    def add_card(self, deck):
        self.hand.add_card(deck.deal_card())

    def has_bust(self):
        if self.hand.get_value() > 21:
            return True

    def reset_bust(self):
        self.hand.reset()

    def __str__(self):
        return f"{self.name} ({self.chips} chips)"

class BotPlayer(Player):
    def __init__(self, name, chips, seed):
        super().__init__(name, chips, bet = 0)
        self.seed = seed
        self.rng = random.Random(seed)
        self.total_bets = chips
        self.total_invested = chips
        self.bot_sit = None

    def decide_move(self):
        if self.hand.get_value() < 17:
            return "hit"
        else:
            return "stand"

    def place_random_bet(self):
        self.bet = self.rng.randint(1, self.chips)

    def rebuy(self):
        self.chips += self.total_invested
        self.total_invested += self.total_invested



class Dealer(Player):
    def __init__(self):
        super().__init__("Dealer", 0, 0)
        self.__hidden_card = None

    def set_hidden_card(self, card2):
        self.__hidden_card = card2
        self.hand.add_card(card2)

    def reveal_hidden_card(self):
        return self.__hidden_card

    def should_draw(self):
        return self.hand.get_value() < 17

class GameManager:
    def __init__(self):
        self.deck = None
        self.dealer = None
        self.player = None
        self.bots = []
        self.player_sit = None
        self.round_active = None
        self.seed = None
        self.sits = [None, None, None]

    def load_players_from_file(self, path):
        x = 0
        with open(path, "r") as f:
            lines = f.readlines()
            for line in lines:
                name, chips, self.seed = line.strip("\n").split(",")
                self.bots.append(BotPlayer(name, int(chips), int(self.seed)))
                x += 1

    def set_deck(self, seed):
        self.deck = Deck(self.seed)
        #self.deck.shuffle()

    def init_values(self):
        player_name = input("Enter your name: ")
        while True:
            try:
                chips = int(input("Enter the amount of chips: "))
                assert 100 <= chips <= 1000
                break
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
            except AssertionError:
                print("Please enter a number between 100 and 1000.")

        while True:
            try:
                self.player_sit = int(input("Where would you like to sit? (Choose a seat number from 1 to 3): "))
                assert self.player_sit in [1, 2, 3]
                break
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
            except AssertionError:
                print("Please enter a number between 1 and 3.")

        return player_name, chips

    def start_game(self):
        name, chips = self.init_values()
        self.player = Player(name, chips, bet=0)
        self.dealer = Dealer()

        # Print bot chips before Welcome
        for bot in self.bots:
            print(f"{bot.name} now has {bot.chips} chips.")

        print("Welcome to Blackjack!")
        print("Nothing is left to chance when you are an engineer.")
        while True:
            try:
                self.seed = int(input("Enter a seed value for the game: "))
                break
            except ValueError:
                print("Invalid input. Please enter a valid integer.")


        self.set_deck(self.seed)
        #self.deck = Deck(self.seed)
        #self.deck.shuffle()

        self.sits[self.player_sit - 1] = self.player
        bot_index = 0
        for i in range(3):
            if self.sits[i] is None:
                self.sits[i] = self.bots[bot_index]
                self.bots[bot_index].bot_sit = i
                bot_index += 1

    def handel_bets(self):
        print(f"\n{self.player.name}, you have {self.player.chips} chips.")

        while self.player.chips == 0:
            while True:
                answer = input("You have no chips left. Do you want to buy more? (yes/no): ").strip().lower()
                if answer in ["yes", "no"]:
                    break
                print("Please enter one of the following: yes, no")
            if answer == "no":
                print("You chose to leave the table.")
                self.round_active = False
                return
            # answer == "yes"
            while True:
                try:
                    amount = int(input("Enter amount of chips to add: "))
                    assert 100 <= amount <= 1000
                    break
                except ValueError:
                    print("Invalid input. Please enter a valid integer.")
                except AssertionError:
                    print("Please enter a number between 100 and 1000.")
            self.player.chips += amount
            self.player.total_invested += amount
            #print(f"You now have {self.player.chips} chips.")

        while True:
            answer = input("Do you want to play a round? (yes/no): ").lower()
            if answer in ["yes", "no"]:
                break
            print("Please enter one of the following: yes, no")
        if answer == "no":
            print("You chose to leave the table.")
            self.round_active = False
            return

        self.round_active = True
        while True:
            try:
                self.player.bet = int(input(f"{self.player.name}, enter your bet (1 - {self.player.chips}): "))
                assert 1 <= self.player.bet <= self.player.chips
                break
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
            except AssertionError:
                print(f"Please enter a number between 1 and {self.player.chips}.")

        self.player.place_hand()
        print(f"{self.player.name} now has {self.player.chips} chips.")



        for bot in self.bots:
            if bot.chips == 0:
                bot.rebuy()
                print(f"{bot.name} was out of chips and added {bot.chips} more chips.")
            bot.place_random_bet()
            bot.place_hand()
            print(f"{bot.name} bets {bot.bet} chips and now has {bot.chips} chips.")


    def play(self, decision, player):
        if decision:
            decision == "hit"

        if decision == "hit":
            player.hand.add_card(self.deck.deal_card())
            return player.hand.cards[-1]
        else:
            return player.hand.cards

    def resolve_results(self):
        self.status_update()

        if self.player.status == "busted":
            print("You busted and lost your bet.")
        elif self.player.status == "lose":
            print("You lost this round.")
        elif self.player.status == "win":
            self.player.chips += self.player.bet * 2
            print(f"You win! You now have {self.player.chips} chips.")
        elif self.player.status == "tie":
            self.player.chips += self.player.bet
            print(f"It's a tie. You get your bet back. Total chips: {self.player.chips}")

        for bot in self.bots:
            if bot.status == "busted":
                print(f"{bot.name} had {bot.hand.get_value()} → busted and lost.")
            elif bot.status == "lose":
                print(f"{bot.name} had {bot.hand.get_value()} → lost this round.")
            elif bot.status == "win":
                bot.chips += bot.bet * 2
                print(f"{bot.name} had {bot.hand.get_value()} → won and now has {bot.chips} chips.")
            elif bot.status == "tie":
                bot.chips += bot.bet
                print(f"{bot.name} had {bot.hand.get_value()} → tied and got their bet back. Total: {bot.chips} chips.")

    def status_update(self):
        if self.dealer.has_bust():
            self.dealer.status = "busted"
            for player in self.sits:
                if player.has_bust():
                    player.status = "busted"
                else:
                    player.status = "win"
        else:
            self.dealer.status = "not_busted"
            for player in self.sits:
                if player.has_bust():
                    player.status = "busted"
                elif self.dealer.hand.get_value() < player.hand.get_value():
                    player.status = "win"
                elif self.dealer.hand.get_value() == player.hand.get_value():
                    player.status = "tie"
                else:
                    player.status = "lose"






    def play_round(self):
        self.round_active = True
        self.handel_bets()
        if not getattr(self, 'round_active', True):
            return

        for player in self.sits:
            player.hand.reset()
        self.dealer.hand.reset()

        # Only reset the deck if fewer than 20 cards remain
        if len(self.deck.cards) <= 20:
            self.deck.recreate_and_shuffle()



        for deal in range(2):
            for player in self.sits:
                player.hand.add_card(self.deck.deal_card())
            card = self.deck.deal_card()
            if deal == 0:
                self.dealer.hand.add_card(card)
            else:
                self.dealer.set_hidden_card(card)

        print()  # Blank line before showing hands

        # Print hands in seating order
        for player in self.sits:
            if player == self.player:
                print(f"You got: {player.hand} (value: {player.hand.get_value()})")
            else:
                print(f"{player.name} hand: {player.hand} (value: {player.hand.get_value()})")

        print()
        print(f"Dealer shows: {self.dealer.hand.cards[0]}")
        print()

        # Turns in seating order
        for player in self.sits:
            if player == self.player:
                while True:
                    if player.has_bust():
                        break
                    try:
                        decision = input("Do you want to 'hit' or 'stand'? ").lower()
                        assert decision in ["hit", "stand"]
                    except AssertionError:
                        print("Please enter one of the following: hit, stand")
                        continue
                    if decision == "hit":
                        print(f"You drew: {self.play(decision, player)}")
                        print(f"New hand: {player.hand} (value: {player.hand.get_value()})")
                    else:
                        break
            else:
                if self.sits[player.bot_sit - 1] == self.player and player.bot_sit != 0:
                    print()
                print(f"{player.name}'s turn:")
                while player.decide_move() == "hit":
                    print(f"{player.name} draws: {self.play(player.decide_move(), player)}")
                print(f"{player.name} stands. Hand: {player.hand} (value: {player.hand.get_value()})")
                print()

        # Dealer's turn
        if self.sits[2] == self.player:
            print()
        print(f"Dealer reveals hidden card: {self.dealer.reveal_hidden_card()}")
        print(f"Dealer's hand: {self.dealer.hand} (value: {self.dealer.hand.get_value()})")
        while self.dealer.should_draw():
            drawn_card = self.play("hit", self.dealer)
            print(f"Dealer draws a: {drawn_card}")
            print(f"Dealer now has: {self.dealer.hand} (value: {self.dealer.hand.get_value()})")
        print()
        print(f"Your final hand value: {self.player.hand.get_value()}")

    #add here the if have no chips left func

    def print_summary(self):
        print("\n--- Game Summary ---")
        print(f"{self.player.name}: {self.player.chips} chips")
        for bot in self.bots:
            print(f"{bot.name}: {bot.chips} chips")

        chips_array = np.array([player.chips for player in self.sits])
        average_chips = np.mean(chips_array)
        highest_chips = np.max(chips_array)
        print(f"\nAverage chips: {average_chips:.2f}")
        print(f"Highest chip count: {highest_chips}\n")

        print("Player ranking (highest to lowest):")
        player_ranking = sorted(
            self.sits,
            key=lambda player: (player.chips / player.total_invested if player.total_invested else 0),
            reverse=True
        )
        for rank_position, player in enumerate(player_ranking, 1):
            return_rate = player.chips / player.total_invested if player.total_invested else 0
            print(
                f"{rank_position}. {player.name} - Chips: {player.chips}, Invested: {player.total_invested}, Return Rate: {return_rate:.2f}")
        self.create_graphical_summary(player_ranking)
        print("Table image with seating and rankings saved as 'table_summary.png'")

    def create_graphical_summary(self, player_ranking):
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_facecolor('#145A32')
        plt.axis('off')

        table_circle = plt.Circle((0.5, 0.5), 0.32, color='#2e8b57')
        ax.add_patch(table_circle)

        seat_coordinates = {
            1: (0.8, 0.5),
            2: (0.5, 0.15),
            3: (0.2, 0.5),
        }

        ranking_by_name = {player.name: rank + 1 for rank, player in enumerate(player_ranking)}

        for seat_number, player in enumerate(self.sits, 1):
            x, y = seat_coordinates[seat_number]
            is_human_player = (player == self.player)
            box_color = '#ffd700' if is_human_player else '#ff0000'
            label = f"You ({player.name})" if is_human_player else player.name
            chips = player.chips
            rank = ranking_by_name[player.name]
            box_text = f"{label}\n#{rank}\n{chips} chips"

            rect = FancyBboxPatch((x - 0.09, y - 0.06), 0.18, 0.12, boxstyle="round,pad=0.02", fc=box_color, ec='black',
                                  lw=2, zorder=2)
            ax.add_patch(rect)
            plt.text(x, y, box_text, ha='center', va='center', fontsize=16, color='black', zorder=3)

        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.savefig('table_summary.png', bbox_inches='tight', dpi=150)
        plt.close()

if __name__ == "__main__":
    manager = GameManager()
    manager.load_players_from_file("bots.txt")
    manager.start_game()
    while True:
        manager.play_round()
        if getattr(manager, 'round_active', True):
            manager.resolve_results()
        else:
            break
    manager.print_summary()
