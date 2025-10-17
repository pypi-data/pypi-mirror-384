#!/usr/bin/env python3

# main_menu.py
# Author: Luxforge
# Main menu launcher for Luxforge tools

# Load the other classes and functions
from foundry.menu.menu import Menu
from foundry.logger.logger import logger

class MainMenu(Menu):
    """
    Interactive CLI menu for management tasks.
    """
    MENU_META = {
        "name": "Main Menu",  # Display name
        "desc": "Main menu for managing various tasks"  # Description
    }

    def _set_options(self):
        logger.d("Setting main menu options - none needed as this will be dynamic")
    
    def load_games_menu(self):
        from foundry.games.menu import GamesMenu
        GamesMenu(previous_menu=self).launch()

if __name__ == "__main__":
    menu = MainMenu()
    menu.launch()