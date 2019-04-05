from bot import Bot
import json

def main():
    bot = Bot("0dd15e93-737b-4702-80ae-bf19aa55ef7b", "GustavFilip")
    bot.join_board(1)
    bot.game_loop()
main()
