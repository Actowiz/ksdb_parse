import json
from datetime import datetime, timedelta
from itemloaders.processors import TakeFirst
from scrapy.loader import ItemLoader
from item import KsdbShopsyLogoutAppItem


class ShopsyParseMain:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pass

    def parse(self, response):

        loader = ItemLoader(item=KsdbShopsyLogoutAppItem())
        loader.default_output_processor = TakeFirst()

        data_json = json.loads(response.text)
        product_id = ''
        try:
            title = data_json.get('RESPONSE').get('pageData').get('pageContext').get('titles').get('title')
            subtitle = data_json.get('RESPONSE').get('pageData').get('pageContext').get('titles').get('subtitle')
            product_name = f"{title if title else ''} ({subtitle if subtitle else ''})".replace('()', '')
        except:
            product_name = ''

        try:
            brand = data_json.get('RESPONSE').get('pageData').get('pageContext').get('brand')
        except:
            brand = ''
        try:
            image_url = data_json.get('RESPONSE').get('pageData').get('pageContext').get('imageUrl').replace('{@width}',
                                                                                                             '1920').replace(
                '{@height}', '1080').replace('{@quality}', '100')
        except:
            image_url = ''
        try:
            category_dict = data_json.get('RESPONSE').get('pageData').get('pageContext').get('analyticsData')
            category_hierarchy = {
                'l1': category_dict.get('category'),
                'l2': category_dict.get('subCategory'),
                'l3': category_dict.get('superCategory'),
                'l4': category_dict.get('vertical'),
            } if category_dict else {}
        except:
            category_hierarchy = {}

        try:
            product_url = data_json.get('RESPONSE').get('pageData').get('pageContext').get('seo').get(
                'webUrl') + f"?pid={product_id}"
        except:
            product_url = ''
        try:
            listing_id = data_json.get('RESPONSE').get('pageData').get('pageContext').get('listingId')
        except:
            listing_id = None
        page_url = 'N/A'

        try:
            if data_json.get('RESPONSE').get('pageData').get('pageContext').get('pricing'):
                product_price = data_json.get('RESPONSE').get('pageData').get('pageContext').get('pricing').get(
                    'finalPrice').get('decimalValue')
                mrp = data_json.get('RESPONSE').get('pageData').get('pageContext').get('pricing').get('mrp')
                discount = data_json.get('RESPONSE').get('pageData').get('pageContext').get('pricing').get(
                    'totalDiscount')
            else:
                product_price, mrp, discount = '0', '0', '0'
        except:
            product_price, mrp, discount = '0', '0', '0'

        try:
            avg_rating = data_json.get('RESPONSE').get('pageData').get('pageContext').get('rating').get('average')
            number_of_ratings = data_json.get('RESPONSE').get('pageData').get('pageContext').get('rating').get('count')
        except:
            avg_rating, number_of_ratings = None, None

        slots = data_json.get('RESPONSE').get('slots')
        slots = slots if slots else []

        other_data = dict()

        arrival_date = 'N/A'
        shipping_charges = '0'
        variations = []

        for slot in slots:
            try:
                widget_type = slot.get('widget').get('type')
            except:
                widget_type = None

            if widget_type == "COMPOSED_SWATCH":
                try:
                    var_comp = [var_pid for var_pid in
                                slot.get('widget').get('data').get(
                                    'swatchComponent').get('value').get('products').keys()]
                    variations.extend(var_comp)
                except:
                    pass
            if widget_type == "SWATCH_VARIANTS":
                try:
                    var_comp = [var_pid.get('value').get('id') for var_pid in
                                slot.get('widget').get('data').get(
                                    'renderableComponents')]
                    variations.extend(var_comp)
                except Exception as e:
                    print(e)
            if widget_type:
                try:
                    if widget_type == 'PRODUCT_PAGE_SUMMARY_V2':
                        if slot.get('widget').get('data').get('moqComponent').get('type') == 'MoqAnnouncement':
                            moq = slot.get('widget').get('data').get('moqComponent').get('announcement').get(
                                'subTitle').get('value').get('text')
                            other_data['MOQ'] = moq
                except:
                    other_data['MOQ'] = "1"
                try:
                    if widget_type == "COMPOSED_SWATCH":
                        other_data['variation_id'] = [var_pid for var_pid in
                                                      slot.get('widget').get('data').get(
                                                          'swatchComponent').get('value').get('products').keys()]
                except:
                    pass
                # IMAGES
                if widget_type == "MULTIMEDIA_SHOPSY":
                    try:
                        multimediaComponents = slot.get('widget').get('data').get(
                            'multimediaComponents')
                        other_data['Images'] = [
                            multimediaComponent.get('value').get('url').replace('{@width}', '1920').replace('{@height}',
                                                                                                            '1080').replace(
                                '{@quality}', '100') for multimediaComponent in multimediaComponents if
                            multimediaComponent.get('value').get('contentType') == 'IMAGE']
                    except:
                        pass

                if widget_type == "POLICY_DETAILS":
                    try:
                        deliveryCallouts = slot.get('widget').get('data').get('policyInfo')[0].get(
                            'value').get('policyCallout').get('text')
                        other_data['seller_return_policy'] = deliveryCallouts if deliveryCallouts else None
                    except:
                        pass

                if widget_type == "DELIVERY":
                    # SELLER RETURN POLICY
                    try:
                        deliveryCallouts = slot.get('widget').get('data').get('deliveryCallouts')
                        return_text = [deliverycallout.get('value').get('text') for deliverycallout in deliveryCallouts
                                       if 'Return' in deliverycallout.get('value').get('text')]
                        other_data['seller_return_policy'] = return_text[0] if return_text else None
                    except:
                        pass
                    # ARRIVAL DATE
                    try:
                        try:
                            date_text = [msg.get('value').get('dateText') for msg in
                                         slot.get('widget').get('data').get('messages') if
                                         msg.get('value').get('type') == "DeliveryInfoMessage"]
                            arrival_date = date_text[0] if date_text else ''
                            arrival_date = datetime.strptime(
                                datetime.strftime(datetime.now() + timedelta(days=1), '%d %b, %A, %Y'),
                                '%d %b, %A, %Y') if arrival_date.startswith("Tomorrow") else datetime.strptime(
                                f"{arrival_date}, {datetime.strftime(datetime.now(), '%Y')}", '%d %b, %A, %Y')
                        except:
                            arrival_date = ''
                        if not arrival_date:
                            arrival_date = data_json.get('RESPONSE').get('pageData').get('pageContext').get(
                                'trackingDataV2').get('slaText')
                            arrival_date = datetime.strptime(
                                f"{arrival_date}, {datetime.strftime(datetime.now(), '%Y')}", '%d %b, %A, %Y')
                    except:
                        arrival_date = ''
                    # SHIPPING CHARGES
                    try:
                        if ('"freeOption":true' in response.text) or ('FREE Delivery' in response.text):
                            shipping_charges = '0'
                        else:
                            shiping_charges_text = [msg.get('value').get('charge')[0].get('decimalValue') for msg in
                                                    slot.get('widget').get('data').get('messages') if
                                                    msg.get('value').get('type') == "DeliveryInfoMessage"]
                            shipping_charges = shiping_charges_text[0] if shiping_charges_text and shiping_charges_text[
                                0] != '0' else '0'
                    except:
                        pass

                # COUPON DATA

                if widget_type == "NEP_COUPON":
                    try:
                        couponSummaries = slot.get('widget').get('data').get('couponSummaries')
                        for couponSummarie in couponSummaries:
                            couponTag = couponSummarie.get('couponTag').get('data')[0].get('value').get('text')
                            couponTitle = couponSummarie.get('newTitle').get('data')[0].get('value').get('text')
                            other_data['coupons'] = {'couponTag': couponTag, 'couponTitle': couponTitle}
                    except:
                        pass

                # OFFER DATA
                if widget_type == "PRODUCT_PAGE_SUMMARY_V2":
                    try:
                        offerGroups = slot.get('widget').get('data').get('offerInfo').get(
                            'value').get('offerGroups')
                        offers = offerGroups[0].get('offers') if offerGroups else []
                        for offer in offers:
                            offerTag = offer.get('value').get('tags')[0]
                            offerName = offer.get('value').get('title')
                            other_data['offers'] = {'title': offerTag, 'details': offerName}
                    except:
                        pass

        try:
            seller_count = data_json.get('RESPONSE').get('pageData').get('pageContext').get('trackingDataV2').get(
                'sellerCount')
            if seller_count == 1:
                Seller_Name = data_json.get('RESPONSE').get('pageData').get('pageContext').get('trackingDataV2').get(
                    'sellerName')
                Seller_Rating = data_json.get('RESPONSE').get('pageData').get('pageContext').get('trackingDataV2').get(
                    'sellerRating')
                other_data['sellerList'] = [{'Seller_Name': Seller_Name, 'Seller_Rating': Seller_Rating}]
        except:
            seller_count = 0

        try:
            rating_breakup = data_json.get('RESPONSE').get('pageData').get('pageContext').get('rating').get('breakup')
            other_data['individualRatingsCount'] = {5 - _: rating_breakup[_] for _, i in
                                                    enumerate(rating_breakup)} if rating_breakup else None
        except:
            pass
        sold_out = 'true'
        try:
            productstatus = data_json.get('RESPONSE').get('pageData').get('pageContext').get('trackingDataV2').get(
                'productStatus')
            if "Currently out of stock for" in response.text:
                sold_out = 'false'
            elif productstatus == "current":
                sold_out = 'false'
        except:
            pass
        try:
            other_data['item_id'] = data_json.get('RESPONSE').get('pageData').get(
                'pageContext').get('itemId')
        except:
            pass
        if sold_out == 'true':
            arrival_date = 'N/A'
        try:
            item_id = data_json['RESPONSE']['pageData']['pageContext']['itemId']
        except:
            item_id = None

        if 'MOQ' not in other_data.keys():
            other_data['MOQ'] = "1"

        try:
            if int(mrp) < int(product_price):
                mrp = product_price
                discount = 'N/A'
        except:
            pass
        try:
            if int(mrp) == 0:
                mrp = "N/A"
        except:
            pass
        try:
            if int(product_price) == 0:
                product_price = "N/A"
        except:
            pass
        try:
            if int(discount) == 0:
                discount = "N/A"
        except:
            pass

        other_data['Variation'] = list(set(variations))
        other_data['listing_id'] = listing_id
        other_data['item_id'] = item_id
        other_data['data_vendor'] = 'Actowiz'
        other_data['delivery'] = 'logout'
        loader.add_value('position', 'N/A')
        # loader.add_value('product_id', product_id)
        # loader.add_value('catalog_id', product_id)
        loader.add_value('product_name', product_name.replace(' ()', ''))
        loader.add_value('catalog_name', product_name.replace(' ()', ''))
        loader.add_value('image_url', image_url)
        loader.add_value('category_hierarchy', json.dumps(category_hierarchy, ensure_ascii=False))
        loader.add_value('product_price', product_price if product_price else 'N/A')
        loader.add_value('arrival_date', arrival_date)
        loader.add_value('shipping_charges', shipping_charges)
        loader.add_value('is_sold_out', sold_out)
        loader.add_value('discount', str(discount) if discount else 'N/A')
        loader.add_value('mrp', str(mrp) if mrp else 'N/A')
        loader.add_value('page_url', page_url)
        loader.add_value('product_url', product_url)
        loader.add_value('number_of_ratings', str(number_of_ratings))
        loader.add_value('avg_rating', str(avg_rating))
        loader.add_value('brand', brand)

        item = loader.load_item()

        return item
