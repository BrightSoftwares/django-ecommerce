from core import controller
from fsm.states import States

def home_context(user_id, user_input):

    if user_input == '1':
        controller.bot.set_state(States.shop.value, user_id)
        return get_shopping_menu()

    elif user_input == '2':
        controller.bot.set_state(States.cart.value, user_id)
        return get_cart_menu()

    elif user_input == '3':
        controller.bot.set_state(States.my_account.value, user_id)
        return get_myaccount_menu()

    elif user_input == '4':
        controller.bot.set_state(States.about.value, user_id)
        return get_about_menu()

    elif user_input == '0':
        controller.bot.set_state(States.home.value, user_id)
        return get_home_menu()
    else:
        return "Unknown command"


def shopping_context(user_id, user_input):

    if user_input == '11':
        controller.bot.set_state(States.shop_search.value, user_id)
        return get_shopping_menu()

    elif user_input == '12':
        controller.bot.set_state(States.shop_addtocart.value, user_id)
        return get_cart_menu()
    elif user_input == '0':
        controller.bot.set_state(States.home.value, user_id)
        return get_home_menu()
    else:
        return "Unknown command"


def get_home_menu():
    return '''
1. Shopping
2. Panier
3. Mon compte
4. A propos
'''

def get_shopping_menu():
    return '''
Shopping menu
0. Back
'''


def get_cart_menu():
    return "This is the content of your cart"


def get_myaccount_menu():
    return "This is your account"


def get_about_menu():
    return "About Bright-Softwares"