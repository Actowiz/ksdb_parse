import json
import re
from datetime import datetime, timedelta


class ShopsyParse():

    def __init__(self, response):
        self.response = response
        self.data_json = json.loads(self.response.text)
        if self.data_json:
            if self.data_json.get('RESPONSE'):
                if self.data_json.get('RESPONSE').get('pageData'):
                    self.page_context = self.data_json.get('RESPONSE').get('pageData').get('pageContext')
                self.slots = self.data_json.get('RESPONSE').get('slots')

    def get_product_id(self):
        if self.page_context:
            product_id = self.page_context.get('productId')
            return product_id

    def get_listing_id(self):
        if self.page_context:
            product_id = self.page_context.get('listingId')
            return product_id

    def get_product_name(self):
        if self.page_context:
            if self.page_context.get('titles'):
                title = self.page_context.get('titles').get('title')
                subtitle = self.page_context.get('titles').get('subtitle')
                product_name = f"{title if title else ''} ({subtitle if subtitle else ''})".replace('()', '')
                return product_name

    def get_brand(self):
        if self.page_context:
            brand = self.page_context.get('brand')
            return brand

    def get_image_url(self):
        if self.page_context:
            image_url = (self.page_context.get('imageUrl')
                         .replace('{@width}','1920')
                         .replace('{@height}', '1080')
                         .replace('{@quality}', '100'))
            return image_url

    def get_category_hierarchy(self):
        if self.page_context:
            category_dict = self.page_context.get('analyticsData')
            if category_dict:
                category_hierarchy = {
                    'l1': category_dict.get('category'),
                    'l2': category_dict.get('subCategory'),
                    'l3': category_dict.get('superCategory'),
                    'l4': category_dict.get('vertical'),
                } if category_dict else {}
                return category_hierarchy

    def get_product_url(self):
        if self.page_context:
            if self.page_context.get('seo'):
                product_url = self.page_context.get('seo').get('webUrl') + f"?pid={self.get_product_id()}"
                return product_url

    def get_page_url(self):
        return 'N/A'

    def get_final_price(self):
        if self.page_context:
            if self.page_context.get('pricing'):
                if self.page_context.get('pricing').get('finalPrice'):
                    decimalValue = self.page_context.get('pricing').get('finalPrice').get('decimalValue')
                    return decimalValue

    def get_fsp(self):
        if self.page_context:
            if self.page_context.get('pricing'):
                fsp = self.page_context.get('pricing').get('fsp')
                return fsp

    def get_discount(self):
        if self.page_context:
            if self.page_context.get('pricing'):
                totalDiscount = self.page_context.get('pricing').get('totalDiscount')
                return totalDiscount

    def get_mrp(self):
        if self.page_context:
            if self.page_context.get('pricing'):
                mrp = self.page_context.get('pricing').get('mrp')
                return mrp

    def get_avg_rating(self):
        if self.page_context:
            if self.page_context.get('rating'):
                avg_rating = self.page_context.get('average')
                return avg_rating

    def get_number_of_ratings(self):
        if self.page_context:
            if self.page_context.get('rating'):
                number_of_ratings = self.page_context.get('rating').get('count')
                return number_of_ratings

    def get_target_slot_data(self, widget_type):
        if self.slots:
            for slot in self.slots:
                if slot.get('widget'):
                    if slot.get('widget').get('type') == widget_type:
                        if slot.get('widget'):
                            slot_data = slot.get('widget').get('data')
                            return slot_data
                            
    def get_policy_info(self):
        widget_type = 'POLICY_DETAILS'
        slot = self.get_target_slot_data(widget_type)
        policy_info = []
        if slot:
            policies = slot.get('policyInfo')
            if policies:
                for policy in policies:
                    'RESPONSE.slots[8].widget.data.policyInfo[0].value.policyCallout.text'
                    if policy.get('value'):
                        if policy.get('value').get('policyCallout'):
                            policy_text = policy.get('value').get('policyCallout').get('text')
                            if policy_text:
                                policy_info.append(policy_text)
        if policy_info:
            return policy_info
    
    def get_variations_list(self):
        variation_pids = []
        widget_type = "COMPOSED_SWATCH"
        slot = self.get_target_slot_data(widget_type)
        if slot:
            if slot.get('swatchComponent'):
                if slot.get('swatchComponent').get('value'):
                    if slot.get('swatchComponent').get('value').get('products'):
                        variations = slot.get('swatchComponent').get('value').get('products').keys()
                        variation_pids.extend(variations)
        widget_type = "SWATCH_VARIANTS"
        slot = self.get_target_slot_data(widget_type)
        if slot:
            if slot.get('renderableComponents'):
                for renderableComponent in slot.get('renderableComponents'):
                    if renderableComponent.get('value'):
                        pid = renderableComponent.get('value').get('id')
                        variation_pids.append(pid)
        return variation_pids


    def get_moq(self):
        widget_type = 'SHOPSY_PRODUCT_PAGE_SUMMARY_V2'
        slot = self.get_target_slot_data(widget_type)
        moq = '1'
        if slot.get('moqComponent'):
            if slot.get('moqComponent').get('type') == 'MoqAnnouncement':
                if slot.get('moqComponent').get('announcement'):
                    if slot.get('moqComponent').get('announcement').get('title'):
                        if slot.get('moqComponent').get('announcement').get('title').get('value'):
                            moq_str = slot.get('moqComponent').get('announcement').get('title').get('value').get('text')
                            numbers = re.findall(r'\d+', moq_str)
                            if numbers:
                                moq = numbers[0]
        return moq

    def get_all_images(self):
        widget_type = 'MULTIMEDIA_SHOPSY'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            multimediaComponents = slot.get('multimediaComponents')
            if multimediaComponents:
                images = []
                for multimediaComponent in multimediaComponents:
                    if multimediaComponent.get('value'):
                        if multimediaComponent.get('value').get('contentType') == 'IMAGE':
                            image_url = multimediaComponent.get('value').get('url')
                            image_url = image_url.replace('{@width}', '1920').replace('{@height}','1080').replace('{@quality}', '100')
                            images.append(image_url)
                return images

    def get_seller_return_policy(self):
        widget_type = "DELIVERY"
        slot = self.get_target_slot_data(widget_type)
        if slot:
            deliveryCallouts = slot.get('deliveryCallouts')
            if deliveryCallouts:
                for deliveryCallout in deliveryCallouts:
                    if deliveryCallout.get('value'):
                        delivery_callout_text = deliveryCallout.get('text')
                        if delivery_callout_text and 'Return' in delivery_callout_text:
                            return delivery_callout_text

    def get_arrival_date(self):
        if self.get_availablility() == 'true':
            return 'N/A'
        widget_type = "DELIVERY"
        slot = self.get_target_slot_data(widget_type)
        arrival_date = ''
        if slot:
            messages = slot.get('messages')
            if messages:
                for message in messages:
                    if message.get('value'):
                        if message.get('value').get('type') == 'DeliveryInfoMessage':
                            date_text = message.get('value').get('dateText')
                            arrival_date = datetime.strptime(
                                    datetime.strftime(datetime.now() + timedelta(days=1), '%d %b, %A, %Y'),
                                    '%d %b, %A, %Y') if date_text.startswith("Tomorrow") else datetime.strptime(
                                    f"{date_text}, {datetime.strftime(datetime.now(), '%Y')}", '%d %b, %A, %Y')
        if not arrival_date:
            date_text = self.page_context.get('trackingDataV2').get('slaText')
            arrival_date = datetime.strptime(f"{date_text}, {datetime.strftime(datetime.now(), '%Y')}", '%d %b, %A, %Y')
        return arrival_date

    def get_shipping_price(self):

        if ('"freeOption":true' in self.response.text) or ('FREE Delivery' in self.response.text):
            return '0'

        widget_type = "DELIVERY"
        slot = self.get_target_slot_data(widget_type)
        for msg in slot.get('messages'):
            shiping_charges = None
            if msg.get('value'):
                if msg.get('value').get('type') == "DeliveryInfoMessage":
                    shiping_charges = msg.get('value').get('charge')[0].get('decimalValue')
            if shiping_charges:
                return shiping_charges
            else:
                return '0'

    def get_coupons(self):
        widget_type = "NEP_COUPON"
        slot = self.get_target_slot_data(widget_type)
        if slot:
            couponSummaries = slot.get('couponSummaries')
            couponTag, couponTitle = None, None
            if couponSummaries:
                for couponSummarie in couponSummaries:
                    if couponSummarie.get('couponTag'):
                        data = couponSummarie.get('couponTag').get('data')
                        if data:
                            couponTag = data[0].get('value').get('text')
                    if couponSummarie in couponSummaries:
                        data = couponSummarie.get('newTitle').get('data')
                        if data:
                            couponTitle = data[0].get('value').get('text')
            if couponTag and couponTitle:
                return {'couponTag': couponTag, 'couponTitle': couponTitle}

    def get_offers(self):
        widget_type = "PRODUCT_PAGE_SUMMARY_V2"
        slot = self.get_target_slot_data(widget_type)
        if slot:
            if slot.get('offerInfo'):
                if slot.get('offerInfo').get('value'):
                    if slot.get('offerInfo').get('value').get('offerGroups'):
                        offers = slot.get('offerInfo').get('value').get('offerGroups')[0].get('offers')
                        if offers:
                            for offer in offers:
                                offerTag = offer.get('value').get('tags')[0]
                                offerName = offer.get('value').get('title')
                                return {'title': offerTag, 'details': offerName}

    def get_seller_count(self):
        if self.page_context:
            if self.page_context.get('trackingDataV2'):
                sellerCount = self.page_context.get('trackingDataV2').get('sellerCount')
                return sellerCount

    def get_one_seller(self):
        if self.page_context:
            if self.page_context.get('trackingDataV2'):
                Seller_Name = self.page_context.get('trackingDataV2').get('sellerName')
                Seller_Rating = self.page_context.get('trackingDataV2').get('sellerRating')
                return [{'Seller_Name': Seller_Name, 'Seller_Rating': Seller_Rating}]

    def get_individual_ratings(self):
        if self.page_context:
            if self.page_context.get('rating'):
                rating_breakup = self.page_context.get('rating').get('breakup')
                if rating_breakup:
                    return {5 - _: rating_breakup[_] for _, i in
                     enumerate(rating_breakup)} if rating_breakup else None

    def get_availablility(self):
        sold_out = 'true'
        productstatus = None
        if self.page_context:
            if self.page_context.get('trackingDataV2'):
                productstatus = self.page_context.get('trackingDataV2').get('productStatus')
        if "Currently out of stock for" in self.response.text:
            sold_out = 'false'
        elif productstatus == "current":
            sold_out = 'false'

        return sold_out

    def get_itemid(self):
        if self.page_context:
            item_id = self.page_context.get('itemId')
            return item_id

    def get_fassured(self):
        if '"fAssured": true' in self.response.text:
            return True
        else:
            return False

    def get_isbn(self):
        isbn_pattern = r'ISBN:\s*(\d+)'
        isbn_matches = re.findall(isbn_pattern, self.response.text)
        if isbn_matches:
            return isbn_matches[0]

    def clean_name(self, value):
        value = str(value)
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

    def get_key_features(self):
        if self.data_json.get('RESPONSE'):
            if self.data_json.get('RESPONSE').get('data'):
                key_features = self.data_json.get('RESPONSE').get('data').get('product_key_features_1')
                if key_features:
                    features = []
                    for data_1 in key_features.get('data'):
                        features.append(self.clean_name(data_1.get('value').get('text')))
                    return features if features else None

    def get_product_description(self):
        if self.data_json:
            if self.data_json.get('RESPONSE'):
                if self.data_json.get('RESPONSE').get('data'):
                    product_description = self.data_json.get('RESPONSE').get('data').get('product_text_description_1')
                    if product_description:
                        regex_pattern = re.compile(r'<.*?>')
                        try:
                            description = re.sub(regex_pattern, '', self.clean_name(
                                " | ".join([data.get('value').get('text') for data in product_description.get('data')])))
                        except:
                            description = ''
                        return description

    def get_detail_component(self):
        detailedComponents = dict()
        try:
            detail_components = self.data_json.get('RESPONSE').get('data').get('listing_manufacturer_info').get('data')[
                0].get('value').get('detailedComponents')
            if detail_components:
                for detail_component in detail_components:
                    detailedComponents[self.clean_name(detail_component.get('value').get('title'))] = self.clean_name(
                        detail_components.get('value').get('callouts')[0])
        except:
            pass
        try:
            mapped_cards = self.data_json.get('RESPONSE').get('data').get('listing_manufacturer_info').get('data')[0].get(
                'value').get('mappedCards')
            detail_comps =self.data_json.get('RESPONSE').get('data').get('listing_manufacturer_info').get('data')[0].get(
                'value').get('detailedComponents')
            if mapped_cards:
                for mapped_card in mapped_cards:
                    detailedComponents[self.clean_name(mapped_card.get('key'))] = self.clean_name(mapped_card.get('values')[0])
            if detail_comps:
                for detail_comp in detail_comps:
                    try:
                        detailedComponents[
                            self.clean_name(detail_comp.get('value').get('title')).replace("'", "")] = detail_comp.get(
                            'value').get('callouts')
                    except:
                        pass
            return detailedComponents
        except:
            pass

    def get_specification(self):
        try:
            productSpecification = dict()
            specifications = self.data_json.get('RESPONSE').get('data').get('product_specification_1').get('data')
            if specifications:
                for specification in specifications:
                    for attribute in specification.get('value').get('attributes'):
                        productSpecification[self.clean_name(attribute.get('name'))] = self.clean_name(
                            " | ".join(attribute.get('values')))
            return productSpecification
        except:
            pass

    def get_seller_list(self):
        sellers = list()
        try:
            for seller in self.data_json.get('RESPONSE').get('data').get('product_seller_detail_1').get('data'):
                sel = dict()
                if seller.get('value').get('sellerInfo').get('value').get('type') == 'SellerInfoValue':
                    sel['SellerId'] = self.clean_name(seller.get('value').get('sellerInfo').get('value').get('id'))
                    sel['SellerName'] = self.clean_name(seller.get('value').get('sellerInfo').get('value').get('name'))
                    sel['rating'] = seller.get('value').get('sellerInfo').get('value').get('rating').get('average')
                    sel['price'] = seller.get('value').get('pricing').get('value').get('finalPrice').get('decimalValue')
                    sellers.append(sel)
        except:
            pass
        return sellers

    def get_product_details_from_pdp(self):
        widget_type = "PRODUCT_DETAILS"
        slot = self.get_target_slot_data(widget_type)
        if slot:
            if slot.get('renderableComponent'):
                if slot.get('renderableComponent').get('value'):
                    product_detail = []
                    details = slot.get('renderableComponent').get('value').get('details')
                    if details:
                        product_detail.append(f'details : {details}')
                    specifications = slot.get('renderableComponent').get('value').get('specification')
                    if specifications:
                        for specification in specifications:
                            name = specification.get('name')
                            values = specification.get('values')
                            if isinstance(values, list):
                                values = ' | '.join(values)
                            product_detail.append(f'{name.strip()} : {values}'.strip())
                    return product_detail
