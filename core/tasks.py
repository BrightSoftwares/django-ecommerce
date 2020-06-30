from __future__ import absolute_import, unicode_literals
from django.utils.text import slugify
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.conf import settings

from celery import shared_task
from core.models import Item
from time import sleep
from core.vinted import Vinted
import uuid
from urllib.request import urlopen


@shared_task
def pull_vinted_products():
    # sleep(10)
    creds = {
        'login': settings.VINTED_LOGIN,
        'password': settings.VINTED_PASSWORD
    }
    session = Vinted(creds=creds)
    session.login().content.decode('utf-8')

    friend_id = '12813951'  # '36544471'
    print("Getting items for ", friend_id)
    i_member_info, i_all_items = session.get_items4member(friend_id)
    print("Got items from vinted", i_all_items)

    for item in i_all_items:
        an_item = Item()
        an_item.id = int(item["id"])
        an_item.title = item["title"]
        an_item.price = float(item["price_numeric"])
        an_item.discount_price = float(item["price_numeric"])
        an_item.category = 'OW'
        an_item.label = "P"
        an_item.slug = slugify("{}{}".format(an_item.title, an_item.id))

        url = item["photos"][0]['full_size_url']
        img_filename = "{}.jpg".format(an_item.id)  # (uuid.uuid4().hex)
        img_temp = NamedTemporaryFile(delete=True)
        img_temp.write(urlopen(url).read())
        img_temp.flush()
        an_item.image.save(img_filename, File(img_temp))

        an_item.save()

        print("Item {} processed.".format(an_item.title))

    return None
