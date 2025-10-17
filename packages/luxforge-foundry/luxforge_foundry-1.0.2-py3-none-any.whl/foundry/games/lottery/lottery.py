# /#!/usr/bin/env python3

# lottery.py
# Author: Luxforge
# Crack the boredom lottery. Win prizes. Have fun.

from foundry.menu.menu import Menu

class LotteryMenu(Menu):
    """
    Interactive CLI menu for lottery tasks.
    """
    MENU_META = {
        "name": "Lottery Menu",  # Display name
        "desc": "Menu for lottery tasks"  # Description
    }


    lottery_phrases = [
        "Feeling lucky?",
        "Try your luck!",
        "May the odds be ever in your favor.",
        "Fortune favors the bold.",
        "Luck is what happens when preparation meets opportunity.",
        "The harder you work, the luckier you get.",
        "You miss 100% of the shots you don't take.",
        "Luck is a matter of preparation.",
        "Diligence is the mother of good luck.",
        "Luck is believing you're lucky.",
        "The best luck of all is the luck you make for yourself."
    ]
    def _set_options(self):

        self.options = {
            "G": ("Generate Numbers", self.generate_numbers),
            "F": ("Generate Fact", self.generate_fact),
            "C": ("Flip Coin", self.flip_coin),
            "R": ("Roll Dice", self.roll_dice)
        }
    
    def __validate_number(self, int):
        """
        Validate that the input is a positive integer.
        """
        try:
            value = int(value)
            if value <= 0:
                raise ValueError
            return value
        except ValueError:
            return None

    def generate_numbers(self):
        """
        Generate a set of random lottery numbers.
        Ask the user for the range (obviously starting at 1 and not going too high)
        """
        import random
        total_numbers = input("Enter the total number of numbers for this lottery pull (e.g. 6): ")
        total_numbers = self.__validate_number(total_numbers)
        if total_numbers is None:
            print("Error: Invalid number of total numbers.")
            input("Press Enter to return to the menu...")
            return
        min_number = input("Enter the minimum number for the lottery pull (e.g. 1): ")
        max_number = input("Enter the maximum number for the lottery pull (e.g. 49): ")
        if min_number >= max_number:
            print("Error: Invalid number range.")
            input("Press Enter to return to the menu...")
            return
        if total_numbers > (max_number - min_number + 1):
            print("Error: Total numbers requested exceeds the available range.")
            input("Press Enter to return to the menu...")
            return
        
        lottery_numbers = []

        # Generate the numbers
        while len(lottery_numbers) < total_numbers:
            number = random.randint(min_number, max_number)
            if number not in lottery_numbers:
                lottery_numbers.append(number)
        
        # Now slowly reveal them
        print("Drawing your lottery numbers...")
        import time
        for number in lottery_numbers:
            # Sleep between 1 and 6 seconds before revealing the next number
            sleep_time = random.randint(1, 6)
            time.sleep(sleep_time)
            phrase = random.choice(self.lottery_phrases)
            print(phrase)
            print(f"Number drawn!! --  {number}!")  
        
        numbers = set(lottery_numbers)
        print(f"Your lottery numbers are: {sorted(numbers)}")
        print("Thank you for playing!")
        input("Press Enter to return to the menu...")

    def generate_fact(self):
        """
        Generate a random fact.
        """
        import requests
        response = requests.get("https://uselessfacts.jsph.pl/random.json?language=en")
        if response.status_code == 200:
            fact = response.json().get("text")
            print(f"Random Fact: {fact}")
        else:
            print("Could not retrieve a fact at this time.")
        input("Press Enter to return to the menu...")

    def flip_coin(self):
        """
        Flip a coin and display the result.
        """
        import random
        result = random.choice(["Heads", "Tails"])
        print(f"The coin landed on: {result}")
        input("Press Enter to return to the menu...")

    def roll_dice(self):
        """
        Roll a six-sided dice and display the result.
        """
        import random
        result = random.randint(1, 6)
        print(f"You rolled a: {result}")
        input("Press Enter to return to the menu...")   

if __name__ == "__main__":
    menu = LotteryMenu()
    menu.launch()