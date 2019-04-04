from bot import Bot
import json

def main():
    bot = Bot("3b64297f-6b74-4102-876a-12a5f093a186", "Etimo4")
    #bot.register_bot("ilost@my.token", "Etimo4")
    bot.join_board(1)
    bot.game_loop()
main()
