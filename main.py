from bot import Bot
import json

def main():
    bot = Bot("a72263a3-ec00-4693-ae61-bfc021f415a0", "GustavFilip1337")
    bot.join_board(1)
    bot.game_loop()
main()
