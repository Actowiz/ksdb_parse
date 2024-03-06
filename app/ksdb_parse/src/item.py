import re
from datetime import datetime, timedelta
import dateparser
import pytz
import scrapy
from itemloaders.processors import MapCompose, Join



def modifies_image_urls(value: str):
    """
    Process image URLs.
    """
    if value:
        image_split = value.split('.')
        if len(image_split) > 4:
            image_url = '.'.join(image_split[:-2])
            return image_url + '.' + image_split[-1]
        else:
            return value


def clean_name(value: str):
    """
    Clean product names.
    """
    if value.strip():
        value = (
            value.strip()
                .replace('\\', '')
                .replace('"', '\"')
                .replace("\u200c", "")
                .replace("\u200f", "")
                .replace("\u200e", "")
                .replace("\n", "")
                .replace("\r", "")
                .replace("\t", "")
        )
        if "\n" in value:
            value = " ".join(value.split())
        return value


def clear_price(value: str):
    """
    Extract and clean price values.
    """
    if value.strip():
        sub_value = re.sub(r'[^0-9.]', '', value).strip()
        if sub_value and sub_value.strip(".") and sub_value != ".":
            return sub_value


def process_arrival_date(value: str):
    """
    Process and format arrival date values.
    """
    today_date = datetime.now(pytz.timezone('Asia/Calcutta'))

    if value.strip():

        if value == 'FREE Delivery':
            return None

        if value == "Today":
            return str(today_date.date()) + " 00:00:00"

        if "as soon as" in value.lower():
            value = value.replace("as soon as", "")

        if "Tomorrow" in value:
            value = value.replace("Tomorrow", "")

        if str(datetime.now().year + 1) in value:
            value = value.split("-", 1)[-1].strip()

        if "-" in value:

            if re.findall("\d+ - \d+", value):
                value = re.sub("-\s*\d+", "", value)

        arrival = (dateparser.parse(value.split("-")[0], settings={'DATE_ORDER': 'DMY'}))
        if arrival:
            arrival = arrival.replace(tzinfo=pytz.timezone('Asia/Calcutta'))
            diff = arrival - today_date
            if diff.days < -100:
                arrival = arrival + timedelta(days=365)

            return str(arrival.date()) + " 00:00:00"


def shipping_charges(value):
    """
    Extract and clean shipping charges.
    """
    if 'FREE delivery' not in value and "FREE" not in value:
        return value




class KsdbShopsyLogoutAppItem(scrapy.Item):
    """
    Scrapy Item class for defining the structure of scraped data.
    """
    product_id = scrapy.Field()
    url = scrapy.Field()

    input_pid = scrapy.Field()

    catalog_name = scrapy.Field(
        input_processor=MapCompose(clean_name, str.split),
        output_processor=Join()
    )

    catalog_id = scrapy.Field()

    source = scrapy.Field()

    scraped_date = scrapy.Field()

    product_name = scrapy.Field(
        input_processor=MapCompose(clean_name, str.split),
        output_processor=Join()
    )

    image_url = scrapy.Field(
        input_processor=MapCompose(modifies_image_urls),
    )

    category_hierarchy = scrapy.Field()

    product_price = scrapy.Field(
        input_processor=MapCompose(clear_price, float),
    )

    arrival_date = scrapy.Field(
        # input_processor=MapCompose(process_arrival_date)
    )

    shipping_charges = scrapy.Field(
        input_processor=MapCompose(shipping_charges, clear_price, float),
    )

    is_sold_out = scrapy.Field()

    discount = scrapy.Field()

    mrp = scrapy.Field(
        input_processor=MapCompose(clear_price, float),
    )

    page_url = scrapy.Field()

    product_url = scrapy.Field()

    number_of_ratings = scrapy.Field(
        input_processor=MapCompose(clear_price, int),
    )

    avg_rating = scrapy.Field(
        input_processor=MapCompose(clear_price, float),
    )

    position = scrapy.Field()

    country_code = scrapy.Field()

    others = scrapy.Field()

    Id = scrapy.Field()

    zip_code = scrapy.Field()

    brand = scrapy.Field()

    l1 = scrapy.Field()

    l2 = scrapy.Field()

    l3 = scrapy.Field()

    l4 = scrapy.Field()

class KsdbAmazonProductItem(scrapy.Item):
    product_id = scrapy.Field()

    input_pid = scrapy.Field()

    catalog_name = scrapy.Field(
        input_processor=MapCompose(clean_name, str.split),
        output_processor=Join()
    )

    catalog_id = scrapy.Field()

    source = scrapy.Field()

    scraped_date = scrapy.Field()

    product_name = scrapy.Field()

    image_url = scrapy.Field(
        input_processor=MapCompose(modifies_image_urls),
    )

    category_hierarchy = scrapy.Field()

    product_price = scrapy.Field(
        input_processor=MapCompose(clear_price, float),
    )

    arrival_date = scrapy.Field(
        input_processor=MapCompose(process_arrival_date)
    )

    shipping_charges = scrapy.Field(
        input_processor=MapCompose(shipping_charges, clear_price, float),
    )

    is_sold_out = scrapy.Field()

    discount = scrapy.Field()

    mrp = scrapy.Field(
        input_processor=MapCompose(clear_price, float),
    )

    page_url = scrapy.Field()

    product_url = scrapy.Field()

    number_of_ratings = scrapy.Field(
        input_processor=MapCompose(clear_price, int),
    )

    avg_rating = scrapy.Field(
        input_processor=MapCompose(clear_price, float),
    )

    position = scrapy.Field()

    country_code = scrapy.Field()

    others = scrapy.Field()

    is_zip = scrapy.Field()

    Id = scrapy.Field()

    zip_code = scrapy.Field()

    is_login = scrapy.Field()

    shipping_charges_json = scrapy.Field()

    product_price_json = scrapy.Field()

    mrp_json = scrapy.Field()

    discount_json = scrapy.Field()

    batch = scrapy.Field()
