# /#!/usr/bin/env python3

# menu.py
# Author: Luxforge
# Menu to host the games

from foundry.menu.menu import Menu
from foundry.logger.logger import logger

class GamesMenu(Menu):
    """
    Interactive CLI menu for games.
    """
    MENU_META = {
        "name": "Games",  # Display name
        "desc": "Menu for playing various games"  # Description
    }
    def _set_options(self):
        self.options = {
            "C": ("Chess", self.play_chess),
            "T": ("Tic-Tac-Toe", self.play_tic_tac_toe)
        }
    def play_chess(self):
        logger.info("Project for another time perhaps.")
        input("Press Enter to return to the menu...")
    
    def play_tic_tac_toe(self):
        logger.info("Project for another time perhaps.")
        input("Press Enter to return to the menu...")