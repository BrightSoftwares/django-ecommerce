from fsm import WhatsAppBot
from fsm.states import States
from django.conf import settings
from fsm.storage.memory import MemoryStorage
from core import menu_text

bot = WhatsAppBot(settings.TWILIO_AUTH_TOKEN, MemoryStorage())

def handle_whatsapp_user_input(request):
    # print(request.POST)
    user_input = request.POST.get('Body', '')
    user_id = request.POST.get('From', '')

    state_data = bot.get_data(user_id)
    current_menu_position = state_data.get('current_menu_position')

    return state_to_action(current_menu_position, user_id, user_input)

    # if current_menu_position is None:
    #     bot.reset_state(user_id)
    #     bot.set_state(States.home.value, user_id)
    #     return menu_text.get_home_menu()
    # else:

    # # bot.set_state(States.new_order_shipment_address.value, user_id)
    # # bot.update_data({'shipment_method_id': shipment_method_id}, user_id)
    # # bot.set_state(States.new_order_shipment_address.value, user_id)

    # # bot.reset_state(user_id)
    # # bot.set_data({'product_topup_id': product_topup_id}, user_id)

    # # bot.update_data({'amount_in_btc': amount_in_btc}, user_id)

    # # bot.set_state(States.topup_bitcoin_address.value, user_id)

    # # bot.update_data({'new_category_price': str(price)}, user_id)

    # # state_data = bot.get_data(user_id)
    # return "Got request {} from user".format(user_input)


def state_to_action(current_menu_position, user_id, user_input):
    print("state_to_action > current position: {}, user input {}".format(current_menu_position, user_input))
    switcher = {
        None: menu_text.home_context,
        States.home.value: menu_text.home_context,
        States.shop.value: menu_text.shopping_context,
        States.cart.value: menu_text.get_cart_menu,
        States.my_account.value: menu_text.get_myaccount_menu,
        States.about.value: menu_text.get_about_menu
    }
    # Get the function from switcher dictionary
    func = switcher.get(current_menu_position, lambda: "Error : Invalid state")
    # Execute the function
    print("Execuring the function {}".format(func))
    return func(user_id, user_input)