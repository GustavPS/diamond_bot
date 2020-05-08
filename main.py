from bot import Bot
import json

def main():
    bot = Bot("77521622-0b1f-43f5-8ccc-5ee7ff4ec57f", "FG2.0")
    bot.join_board(2)
    bot.game_loop()
main()
