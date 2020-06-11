from enum import Enum


class States(Enum):
    home = '0'
    shop = '1'
    cart = '2'
    my_account = '3'
    about = '4'

    # Shopping features
    shop_search = '11'
    shop_addtocart = '12'
