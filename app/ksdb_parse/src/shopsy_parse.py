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

    def get_category_hierarchy_2(self):
        widget_type = 'PHYSICAL_ATTACH'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            if slot.get('parentProduct').get('value').get('analyticsData'):
                category_dict = slot.get('parentProduct').get('value').get('analyticsData')
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

    def get_Maximum_Retail_Price(self):
        if self.page_context:
            # RESPONSE.pageData.pageContext.pricing.prices[0].name
            if self.page_context.get('pricing'):
                for price_loop in self.page_context.get('pricing').get('prices'):
                    priceType = price_loop.get('priceType')
                    if priceType == 'MRP':
                        Maximum_Retail_Price = price_loop.get('decimalValue')
                        return Maximum_Retail_Price

    def get_Selling_Price(self):
        if self.page_context:
            # RESPONSE.pageData.pageContext.pricing.prices[0].name
            if self.page_context.get('pricing'):
                for price_loop in self.page_context.get('pricing').get('prices'):
                    priceType = price_loop.get('priceType')
                    if priceType == 'FSP':
                        Selling_Price = price_loop.get('decimalValue')
                        return Selling_Price

    def get_final_price_FPS(self):
        widget_type = 'SHOPSY_PRODUCT_PAGE_SUMMARY_V2'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            # widget.data.pricing.value.finalPrice.decimalValue
            if slot.get('pricing'):
                if slot.get('pricing').get('value'):
                    for Price_loop in slot.get('pricing').get('value').get('prices'):
                        priceType = Price_loop.get('priceType')
                        if priceType == 'FSP':
                            finalprice = Price_loop.get('value')
                            return finalprice

    def get_Special_price(self):
        if self.page_context:
            # RESPONSE.pageData.pageContext.pricing.prices[0].name
            if self.page_context.get('pricing'):
                for price_loop in self.page_context.get('pricing').get('prices'):
                    priceType = price_loop.get('priceType')
                    if priceType == 'SPECIAL_PRICE':
                        Special_price = price_loop.get('decimalValue')
                        return Special_price

    def get_final_price_SPECIAL_PRICE(self):
        widget_type = 'SHOPSY_PRODUCT_PAGE_SUMMARY_V2'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            # widget.data.pricing.value.finalPrice.decimalValue
            if slot.get('pricing'):
                if slot.get('pricing').get('value'):
                    for Price_loop in slot.get('pricing').get('value').get('prices'):
                        priceType = Price_loop.get('priceType')
                        if priceType == 'SPECIAL_PRICE':
                            finalprice = Price_loop.get('value')
                            return finalprice

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

    def get_mrp_2(self):
        widget_type = 'SHOPSY_PRODUCT_PAGE_SUMMARY_V2'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            # widget.data.pricing.value.finalPrice.decimalValue
            if slot.get('pricing'):
                if slot.get('pricing').get('value'):
                    try:
                        if slot.get('pricing').get('value').get('mrp').get('value'):
                            mrp = slot.get('pricing').get('value').get('mrp').get('value')
                            return mrp
                        else:
                            for Price_loop in slot.get('pricing').get('value').get('prices'):
                                priceType = Price_loop.get('priceType')
                                if priceType == 'MRP':
                                    mrp = Price_loop.get('value')
                                    return mrp
                    except:
                        for Price_loop in slot.get('pricing').get('value').get('prices'):
                            priceType = Price_loop.get('priceType')
                            if priceType == 'MRP':
                                mrp = Price_loop.get('value')
                                return mrp

    def get_avg_rating(self):
        if self.page_context:
            if self.page_context.get('rating'):
                avg_rating = self.page_context.get('rating').get('average')
                return avg_rating

    def get_avg_rating_PRODUCT_PAGE_SUMMARY_V2(self):
        widget_type = 'SHOPSY_PRODUCT_PAGE_SUMMARY_V2'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            if slot.get('ratingsAndReviews'):
                avg_rating = slot.get('ratingsAndReviews').get('value').get('rating').get('average')
                return avg_rating

    def get_avg_rating_2(self):
        widget_type = 'ADVERTISEMENT'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            if slot.get('advertisementValue'):
                avg_rating=  slot.get('advertisementValue').get('value').get('rating').get('average')
                return avg_rating

    def get_avg_rating_3(self):
        widget_type = 'PHYSICAL_ATTACH'
        # widget.data.parentProduct.value.rating.breakup
        slot = self.get_target_slot_data(widget_type)
        if slot:
            if slot.get('parentProduct'):
                avg_rating=  slot.get('parentProduct').get('value').get('rating').get('average')
                return avg_rating

    def get_number_of_ratings(self):
        if self.page_context:
            if self.page_context.get('rating'):
                number_of_ratings = self.page_context.get('rating').get('count')
                return number_of_ratings

    def get_number_of_ratings_PRODUCT_PAGE_SUMMARY_V2(self):
        widget_type = 'SHOPSY_PRODUCT_PAGE_SUMMARY_V2'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            if slot.get('ratingsAndReviews'):
                number_of_ratings = slot.get('ratingsAndReviews').get('value').get('rating').get('count')
                return number_of_ratings

    def get_number_of_ratings_2(self):
        widget_type = 'ADVERTISEMENT'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            if slot.get('advertisementValue'):
                number_of_ratings = slot.get('advertisementValue').get('value').get('rating').get('count')
                return number_of_ratings

    def get_number_of_ratings_3(self):
        widget_type = 'PHYSICAL_ATTACH'
        slot = self.get_target_slot_data(widget_type)
        # RESPONSE.slots[7].widget.data.parentProduct.value.rating.count
        if slot:
            if slot.get('parentProduct'):
                number_of_ratings = slot.get('parentProduct').get('value').get('rating').get('count')
                return number_of_ratings

    def get_target_slot_data(self, widget_type):
        if self.slots:
            for slot in self.slots:
                if slot.get('widget'):
                    if slot.get('widget').get('type') == widget_type:
                        if slot.get('widget'):
                            slot_data = slot.get('widget').get('data')
                            return slot_data

    def get_product_announcement(self):
        widget_type = 'PRODUCT_ANNOUNCEMENT'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            if slot.get('widget'):
                if slot.get('widget').get('data'):
                    if slot.get('widget').get('data').get('announcement'):
                        if slot.get('widget').get('data').get('announcement').get('value'):
                            text = slot.get('widget').get('data').get('announcement').get('value').get('title')
                            return text


    def get_policy_info(self):
        widget_type = 'POLICY_DETAILS'
        slot = self.get_target_slot_data(widget_type)
        policy_info = []
        if slot:
            policies = slot.get('policyInfo')
            if policies:
                for policy in policies:
                    if policy.get('value'):
                        if policy.get('value').get('policyCallout'):
                            policy_text = policy.get('value').get('policyCallout').get('text')
                            if policy_text:
                                policy_info.append(policy_text)
        if policy_info:
            return policy_info

    def get_delivery_msg(self):
        widget_type = "DELIVERY"
        delivery_info = []
        slot = self.get_target_slot_data(widget_type)
        if slot:
            deliveryCallouts = slot.get('deliveryCallouts')
            if deliveryCallouts:
                for deliveryCallout in deliveryCallouts:
                    if deliveryCallout.get('value'):
                        delivery_info.append(deliveryCallout.get('value').get('text'))
        return delivery_info

    def get_product_notes(self):
        widget_type = "PRODUCT_NOTE"
        slot = self.get_target_slot_data(widget_type)
        note_info = []
        if slot:
            notes = slot.get('notes')
            if notes:
                for note in notes:
                    if note.get('value'):
                        text = note.get('value').get('text')
                        return text

    def get_product_expiry(self):
        widget_type = "EXPIRY"
        slot = self.get_target_slot_data(widget_type)
        if slot:
            if slot.get('renderableComponent'):
                if slot.get('renderableComponent').get('value'):
                    expiry = slot.get('renderableComponent').get('value').get('expiry')
                    return expiry

    def get_other_announcement(self):
        widget_type = "FORMATTED_ANNOUNCEMENT"
        slot = self.get_target_slot_data(widget_type)
        if slot:
            renderableComponents = slot.get('renderableComponent')
            for renderableComponent in renderableComponents:
                if renderableComponent.get('value'):
                    datas = renderableComponent.get('value').get('data')
                    if datas:
                        for data in datas:
                            if data.get('value'):
                                text = data.get('value').get('text')
                                return text


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
        variations_name = []
        if slot:
            if slot.get('renderableComponents'):
                for renderableComponent in slot.get('renderableComponents'):
                    if renderableComponent.get('value'):
                        pid = renderableComponent.get('value').get('id')
                        variation_pids.append(pid)
                        if renderableComponent.get('value').get('swatchValue'):
                            variations_name.append(renderableComponent.get('value').get('swatchValue').get('value'))
        return variation_pids

    def get_variations_name(self):
        widget_type = "SWATCH_VARIANTS"
        slot = self.get_target_slot_data(widget_type)
        variations_name = []
        if slot:
            if slot.get('renderableComponents'):
                for renderableComponent in slot.get('renderableComponents'):
                    if renderableComponent.get('value'):
                        if renderableComponent.get('value').get('swatchValue'):
                            variations_name.append(renderableComponent.get('value').get('swatchValue').get('value'))
        return variations_name

    def get_moq(self):
        widget_type = 'SHOPSY_PRODUCT_PAGE_SUMMARY_V2'
        slot = self.get_target_slot_data(widget_type)
        moq = '1'
        if slot:
            try:
                # tagsData[0].data[1].text
                for moq_loop in slot.get('tagsData')[0].get('data'):
                    identifier_data = moq_loop.get('identifier')
                    if identifier_data == 'SUPER_COMBO':
                        moq_str = moq_loop.get('text')
                        numbers = re.findall(r'\d+', moq_str)
                        if numbers:
                            moq = numbers[0]
            except:
                if slot.get('moqComponent'):
                    if slot.get('moqComponent').get('type') == 'MoqAnnouncement':
                        if slot.get('moqComponent').get('announcement'):

                            if slot.get('moqComponent').get('announcement').get('title'):
                                if slot.get('moqComponent').get('announcement').get('title').get('value'):
                                    moq_str = slot.get('moqComponent').get('announcement').get('title').get(
                                        'value').get('text')
                                    numbers = re.findall(r'\d+', moq_str)
                                    if numbers:
                                        moq = numbers[0]
                return moq
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
                        if multimediaComponent.get('value').get('contentType') == 'VIDEO':
                            video_url = multimediaComponent.get('value').get('url')
                            video_url = video_url.replace('{@width}', '1920').replace('{@height}', '1080').replace('{@quality}', '100')
                            images.append(video_url)

                return images

    def get_seller_return_policy(self):
        widget_type = "DELIVERY"
        slot = self.get_target_slot_data(widget_type)
        if slot:
            deliveryCallouts = slot.get('deliveryCallouts')
            if deliveryCallouts:
                for deliveryCallout in deliveryCallouts:
                    if deliveryCallout.get('value'):
                        delivery_callout_text = deliveryCallout.get('value').get('text')
                        if 'return' in delivery_callout_text.lower():
                            return delivery_callout_text

    def get_seller_return_policy_2(self):
        widget_type = 'SELLER_V2'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            try:
                for returnCallouts_loop in slot.get('SellerMetaValue').get('value').get('returnCallouts'):
                    Replacement_Policy_tab = returnCallouts_loop.get('tabType')
                    if Replacement_Policy_tab == 'RETURN':
                        Replacement_Policy = returnCallouts_loop.get('displayText')
                        return Replacement_Policy
            except:
                return None

    def get_arrival_date(self):
        # if self.get_availablility() == 'true':
        #     return 'N/A'
        widget_type = "DELIVERY"
        slot = self.get_target_slot_data(widget_type)
        arrival_date = ''
        try:
            if slot:
                messages = slot.get('messages')
                if messages:
                    for message in messages:
                        if message.get('value'):
                            if message.get('value').get('type') == 'DeliveryInfoMessage':
                                date_text = message.get('value').get('dateText')
                                if date_text:
                                    try:
                                        if 'tomorrow' in date_text.lower():
                                            arrival_date = datetime.strptime(
                                                datetime.strftime(datetime.now() + timedelta(days=1), '%d %b, %A, %Y'),
                                                '%d %b, %A, %Y')
                                        elif 'today' in date_text.lower():
                                            arrival_date = datetime.strptime(
                                                datetime.strftime(datetime.now() + timedelta(days=0), '%d %b, %A, %Y'),
                                                '%d %b, %A, %Y')
                                        else:
                                            arrival_date = datetime.strptime(
                                                datetime.strftime(datetime.now() + timedelta(days=1), '%d %b, %A, %Y'),
                                                '%d %b, %A, %Y') if date_text.startswith(
                                                "Tomorrow") else datetime.strptime(
                                                f"{date_text}, {datetime.strftime(datetime.now(), '%Y')}",
                                                '%d %b, %A, %Y')
                                            try:
                                                if arrival_date:
                                                    current_date = datetime.now()
                                                    # Ensure `arrival_date` is a datetime object before comparison
                                                    if isinstance(arrival_date, str):
                                                        arrival_date = datetime.strptime(arrival_date, '%d %b, %A, %Y')
                                                    formatted_current_date = datetime.strptime(
                                                        current_date.strftime('%d %b, %A, %Y'), '%d %b, %A, %Y')

                                                    if arrival_date < formatted_current_date:
                                                        # Increment the year and format back to the desired format
                                                        arrival_date = arrival_date.replace(year=arrival_date.year + 1).strftime("%Y-%m-%d %H:%M:%S")
                                                        # arrival_date = arrival_date.strftime("%Y-%m-%d %H:%M:%S")
                                                else:
                                                    arrival_date = arrival_date
                                            except:
                                                arrival_date = arrival_date
                                    except:
                                        days_str = date_text.split()[0]
                                        days_to_add = int(days_str)
                                        current_date = datetime.now()
                                        new_date = current_date + timedelta(days=days_to_add)
                                        arrival_date_1 = new_date.replace(hour=0, minute=0, second=0, microsecond=0)
                                        arrival_date = arrival_date_1.strftime('%Y-%m-%d %H:%M:%S')
            if not arrival_date:
                date_text = self.page_context.get('trackingDataV2').get('slaText')
                arrival_date = datetime.strptime(f"{date_text}, {datetime.strftime(datetime.now(), '%Y')}", '%d %b, %A, %Y')
                try:
                    if arrival_date:
                        current_date = datetime.now()
                        # Ensure `arrival_date` is a datetime object before comparison
                        if isinstance(arrival_date, str):
                            arrival_date = datetime.strptime(arrival_date, '%d %b, %A, %Y')
                        formatted_current_date = datetime.strptime(
                            current_date.strftime('%d %b, %A, %Y'), '%d %b, %A, %Y')

                        if arrival_date < formatted_current_date:
                            # Increment the year and format back to the desired format
                            arrival_date = arrival_date.replace(year=arrival_date.year + 1).strftime(
                                "%Y-%m-%d %H:%M:%S")
                            # arrival_date = arrival_date.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        arrival_date = arrival_date
                except:
                    arrival_date = arrival_date
            return arrival_date
        except:
            return 'N/A'

    def get_shipping_price(self):

        if ('"freeOption":true' in self.response.text) or ('FREE Delivery' in self.response.text):
            return 'N/A'

        widget_type = "DELIVERY"
        slot = self.get_target_slot_data(widget_type)
        if slot:
            for msg in slot.get('messages'):
                shiping_charges = None
                if msg.get('value'):
                    if msg.get('value').get('type') == "DeliveryInfoMessage":
                        shiping_charges = msg.get('value').get('charge')[0].get('decimalValue')
                if shiping_charges:
                    return shiping_charges
                else:
                    return 'N/A'
        return 'N/A'

    def get_ordered_tag(self):
        widget_type = "FORMATTED_ANNOUNCEMENT"
        slot = self.get_target_slot_data(widget_type)
        if slot:
            # widget.data.renderableComponents[0].value.data.data[0].value.text
            if slot.get('renderableComponents'):
                try:
                    ordered_tag = slot.get('renderableComponents')[0].get('value').get('data').get('data')[0].get('value').get('text')
                    return ordered_tag
                except:
                    return None

    def get_product_Tag(self):
        widget_type = 'MULTIMEDIA_SHOPSY'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            # RESPONSE.slots[1].widget.data.tagsData[0].data[0].text
            if slot.get('tagsData'):
                try:
                    product_Tag = slot.get('tagsData')[0].get('data')[0].get('text')
                    return product_Tag
                except:
                    return None

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
        widget_type = "SHOPSY_PRODUCT_PAGE_SUMMARY_V2"
        slot = self.get_target_slot_data(widget_type)

        widget_type_1 = "PRODUCT_PAGE_SUMMARY_V2"
        slot_1 = self.get_target_slot_data(widget_type_1)

        offer_list = []
        if slot:
            if slot.get('offerInfo'):
                if slot.get('offerInfo').get('value'):
                    if slot.get('offerInfo').get('value').get('offerGroups'):
                        offers = slot.get('offerInfo').get('value').get('offerGroups')[0].get('offers')
                        if offers:
                            for offer in offers:
                                try:
                                    offerTag = offer.get('value').get('tags')[0]
                                except:
                                    offerTag = 'offer'
                                offerName = offer.get('value').get('title')
                                offer_dict = {'title': offerTag, 'details': offerName}
                                offer_list.append(offer_dict)
                            return offer_list

        elif slot_1:
            if slot_1.get('offerInfo'):
                if slot_1.get('offerInfo').get('value'):
                    if slot_1.get('offerInfo').get('value').get('offerGroups'):
                        offers = slot_1.get('offerInfo').get('value').get('offerGroups')[0].get('offers')
                        if offers:
                            for offer in offers:
                                try:
                                    offerTag = offer.get('value').get('tags')[0]
                                except:
                                    offerTag = 'offer'
                                offerName = offer.get('value').get('title')
                                offer_dict= {'title': offerTag, 'details': offerName}
                                offer_list.append(offer_dict)
                            return offer_list

    def get_seller_count(self):
        if self.page_context:
            if self.page_context.get('trackingDataV2'):
                sellerCount = self.page_context.get('trackingDataV2').get('sellerCount')
                return sellerCount

    def get_main_seller(self):
        # RESPONSE.pageData.pageContext.trackingDataV2.sellerId
        if self.page_context:
            if self.page_context.get('trackingDataV2'):
                sellerId = self.page_context.get('trackingDataV2').get('sellerId')
                return sellerId


    def get_one_seller(self):
        if self.page_context:
            if self.page_context.get('trackingDataV2'):
                Seller_Name = self.page_context.get('trackingDataV2').get('sellerName')
                try:
                    Seller_Rating = self.page_context.get('trackingDataV2').get('sellerRating')
                except:
                    Seller_Rating = ''
                sellerId = self.get_main_seller()
                return {f'{sellerId}':{'SellerName': Seller_Name, 'rating': Seller_Rating,'Is_seller_buy_box':'True'}}

    def get_one_seller_data(self):
        widget_type = 'SELLER_V2'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            if slot.get('SellerMetaValue'):
                Seller_Name = slot.get('SellerMetaValue').get('value').get('name')
                try:
                    sellerId = slot.get('SellerMetaValue').get('action').get('params').get('sellerId')
                except:
                    sellerId = ''
                try:
                    Seller_Rating = slot.get('rating').get('value').get('average')
                except:
                    Seller_Rating = ''
                return {f'{sellerId}': {'SellerName': Seller_Name, 'rating': Seller_Rating,
                                    'Is_seller_buy_box': 'True'}}

    def get_coupon_off(self):
        if self.page_context:
            if self.page_context.get('couponMetadata'):
                if self.page_context.get('couponMetadata').get('couponValue'):
                    coupon_description_list = []
                    coupon_description = {}
                    coupon_description['title'] = self.page_context.get('couponMetadata').get('type')
                    coupon_description['legend'] = 'Coupons for you'
                    coupon_description['details'] = str(self.page_context.get('couponMetadata').get('couponValue'))
                    coupon_description_list.append(coupon_description)
                    return coupon_description_list

    def get_coupon_off_2(self):
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
                coupon_description_list = []
                coupon_description = {}
                coupon_description['title'] = 'NORMAL_COUPON'
                coupon_description['legend'] = 'Coupons for you'
                match_re = re.search(r'₹(\d+)', couponTag)
                if match_re:
                    coupon_description['details'] = str(match_re.group(1))
                    coupon_description_list.append(coupon_description)
                    return coupon_description_list


    def get_individual_ratings(self):
        if self.page_context:
            if self.page_context.get('rating'):
                rating_breakup = self.page_context.get('rating').get('breakup')
                if rating_breakup:
                    return {5 - _: rating_breakup[_] for _, i in
                     enumerate(rating_breakup)} if rating_breakup else None

    def get_individual_ratings_SHOPSY_PRODUCT_PAGE_SUMMARY(self):
        widget_type = 'SHOPSY_PRODUCT_PAGE_SUMMARY_V2'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            if slot.get('ratingsAndReviews'):
                rating_breakup = slot.get('ratingsAndReviews').get('value').get('rating').get('breakup')
                if rating_breakup:
                    return {5 - _: rating_breakup[_] for _, i in enumerate(rating_breakup)} if rating_breakup else None

    def get_individual_ratings_1(self):
        widget_type = 'PHYSICAL_ATTACH'
        # RESPONSE.slots[7].widget.data.parentProduct.value.rating.breakup
        slot = self.get_target_slot_data(widget_type)
        if slot:
            if slot.get('parentProduct'):
                rating_breakup = slot.get('parentProduct').get('value').get('rating').get('breakup')
                if rating_breakup:
                    return {_+1: rating_breakup[_] for _, i in enumerate(rating_breakup)} if rating_breakup else None

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

    def get_availablility_2(self):
        widget_type = 'PHYSICAL_ATTACH'
        slot = self.get_target_slot_data(widget_type)
        sold_out = 'true'
        if slot:
            try:
                try:
                    stock_displayState = slot.get('parentProduct').get('value').get('availability').get('displayState')
                except:
                    stock_displayState = ''
                if not stock_displayState:
                    if slot.get('products'):
                        for stock_loop in slot.get('products'):
                            stock_displayState = stock_loop.get('value').get('availability').get('displayState')
                if 'IN_STOCK' in stock_displayState:
                    sold_out = 'false'

            except:
                pass
            return sold_out
        return sold_out

    def get_availablility_3(self):
        sold_out = 'true'
        if self.data_json.get('RESPONSE'):
            if self.data_json.get('RESPONSE').get('pageData'):
                if self.data_json.get('RESPONSE').get('pageData').get('pageLevelSlots'):
                    for stock_key in self.data_json.get('RESPONSE').get('pageData').get('pageLevelSlots'):
                        if self.data_json.get('RESPONSE').get('pageData').get('pageLevelSlots').get(stock_key):
                            av_data = self.data_json.get('RESPONSE').get('pageData').get('pageLevelSlots').get(
                                stock_key)
                            widget_type = av_data.get('widget').get('type')
                            if widget_type == 'ACTION':
                                for av_data_loop in av_data.get('widget').get('data').get('actions'):
                                    if av_data_loop.get('action').get('type'):
                                        action_type = av_data_loop.get('action').get('type')
                                        if action_type == 'CART_ADD':
                                            stock_displayState = av_data_loop.get('value').get('text')
                                            if stock_displayState == 'Add to cart':
                                                sold_out = 'false'
                                                return sold_out
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
                        spec_key = self.clean_name(attribute.get('name'))
                        if not spec_key:
                            spec_key = self.clean_name(specification.get('value').get('key'))
                        productSpecification[spec_key] = self.clean_name(
                            " | ".join(attribute.get('values')))
            return productSpecification
        except:
            pass

    def get_seller_list(self,main_seller_data):
        # sellers = list()
        Sellers_dict = {}
        main_seller_id = main_seller_data
        try:
            for seller in self.data_json.get('RESPONSE').get('data').get('product_seller_detail_1').get('data'):
                sel = dict()
                if seller.get('value').get('sellerInfo').get('value').get('type') == 'SellerInfoValue':
                    SellerId = self.clean_name(seller.get('value').get('sellerInfo').get('value').get('id'))
                    if SellerId == main_seller_id:
                        sel['Is_seller_buy_box'] = 'True'
                    else:
                        sel['Is_seller_buy_box'] = 'False'
                    # sel['SellerId'] = self.clean_name(seller.get('value').get('sellerInfo').get('value').get('id'))
                    sel['SellerName'] = self.clean_name(seller.get('value').get('sellerInfo').get('value').get('name'))
                    try:
                        sel['rating'] = seller.get('value').get('sellerInfo').get('value').get('rating').get('average')
                    except:
                        pass
                    sel['price'] = seller.get('value').get('pricing').get('value').get('finalPrice').get('decimalValue')
                    # RESPONSE.data.product_seller_detail_1.data[1].value.actions.BUY_NOW.data[0].action.params.quantity
                    try:
                        Seller_Moq = seller.get('value').get('actions').get('BUY_NOW').get('data')[0].get('action').get(
                            'params').get('quantity')
                        if Seller_Moq:
                            sel['MOQ'] = Seller_Moq
                        else:
                            sel['MOQ'] = '1'
                    except:
                        sel['MOQ'] = '1'
                    Sellers_dict[f'{SellerId}'] = sel
                # sellers.append(Sellers_dict)
        except:
            pass
        return Sellers_dict

    def get_product_highlights(self):
        widget_type = 'PRODUCT_RICH_HIGHLIGHTS'
        slot = self.get_target_slot_data(widget_type)
        product_highlights = {}
        if slot:
            descriptionCardsComponents = slot.get('descriptionCardsComponents')
            if descriptionCardsComponents:
                for descriptionCardsComponent in descriptionCardsComponents:
                    if descriptionCardsComponent.get('value'):
                        title = descriptionCardsComponent.get('value').get('title')
                        text = descriptionCardsComponent.get('value').get('text')
                        product_highlights[title] = text
        return product_highlights

    def get_Dimensions(self):
        widget_type = 'PRODUCT_DIMENSIONS'
        if self.slots:
            for slot in self.slots:
                if slot.get('widget'):
                    if slot.get('widget').get('type') == widget_type:
                        if slot.get('widget').get('header').get('value').get('titleValue').get('text') == 'Dimensions':
                            Dimensions = {}
                            if slot:
                                for slot_loop in slot.get('widget').get('data').get('specificationsComponents'):
                                    if slot_loop.get('value').get('key'):
                                        Dimensions[slot_loop.get('value').get('key')]=slot_loop.get('value').get('value')
                                return Dimensions

    def get_Material_Color(self):
        widget_type = 'PRODUCT_MATERIALS_WIDGET'
        if self.slots:
            for slot in self.slots:
                if slot.get('widget'):
                    if slot.get('widget').get('type') == widget_type:
                        if slot.get('widget').get('header').get('value').get('titleValue').get('text') == 'Material & Color':
                            Material_Color = {}
                            if slot:
                                for slot_loop in slot.get('widget').get('data').get('specificationsComponents'):
                                    if slot_loop.get('value').get('key'):
                                        Material_Color[slot_loop.get('value').get('key')]=slot_loop.get('value').get('value')
                                return Material_Color

    def get_Highlights(self):
        widget_type = 'HIGHLIGHTS'
        slot = self.get_target_slot_data(widget_type)

        if slot:
            highlights_data = slot.get('highlights').get('value').get('text')
            if highlights_data:
                return highlights_data

    def get_parameterRating(self):
        if self.page_context:
            try:
                parameterRating = self.page_context.get('fdpEventTracking').get('events').get('psi').get('pr').get('parameterRating')
                return parameterRating
            except:
                return None

    def get_parameterRating_1(self):
        widget_type = 'RATING'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            if slot.get('scaleAspectComponents'):
                parameterrating_list = []
                for parameterrating_loop in slot.get('scaleAspectComponents'):
                    parameterrating_dict ={}
                    parameterrating_dict['parameter'] = parameterrating_loop.get('value').get('name')
                    parameterrating_dict['rating']=parameterrating_loop.get('value').get('average')
                    parameterrating_list.append(parameterrating_dict)
                return parameterrating_list

    def get_product_highlights_text(self):
        widget_type = 'RPD_SUMMARY'
        slot = self.get_target_slot_data(widget_type)
        contents_data_list = []
        if slot:
            contentCards = slot.get('contentCards')
            if contentCards:
                for contentCards_loop in contentCards:
                    contentType = contentCards_loop.get('value').get('contentType')
                    if contentType == 'RED_FEATURE':
                        contents = contentCards_loop.get('value').get('contents')
                        if contents:
                            for contents_loop in contents:
                                try:
                                    contents_description = contents_loop.get('description').get('text')
                                    contents_title = contents_loop.get('title').get('text')
                                    contents_data_list.append(contents_title)
                                    contents_data_list.append(contents_description)
                                except:
                                    pass
        if contents_data_list:
            highlights_text = ' '.join(contents_data_list)
            return highlights_text


    def get_Cash_on_Delivery(self):
        widget_type = 'DELIVERY'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            try:
                for deliveryCallouts_loop in slot.get('deliveryCallouts'):
                    if deliveryCallouts_loop:
                        Delivery_Policy = deliveryCallouts_loop.get('value').get('text')
                        if Delivery_Policy:
                            if 'delivery' in Delivery_Policy.lower():
                                return Delivery_Policy
            except:
                return None

    def get_Cash_on_Delivery_2(self):
        widget_type = 'POLICY_DETAILS'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            try:
                for policyInfo_loop in slot.get('policyInfo'):
                    if policyInfo_loop:
                        Delivery_Policy = policyInfo_loop.get('value').get('policyCallout').get('text')
                        if Delivery_Policy:
                            if 'delivery' in Delivery_Policy.lower():
                                return Delivery_Policy
            except:
                return None

    def get_replacement_policy(self):
        widget_type = 'DELIVERY'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            try:
                for deliveryCallouts_loop in slot.get('deliveryCallouts'):
                    if deliveryCallouts_loop:
                        Replacement_Policy = deliveryCallouts_loop.get('value').get('text')
                        if Replacement_Policy:
                            if 'replacement' in Replacement_Policy.lower():
                                return Replacement_Policy
            except:
                return None

    def get_replacement_policy_2(self):
        widget_type = 'SELLER_V2'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            try:
                for returnCallouts_loop in slot.get('SellerMetaValue').get('value').get('returnCallouts'):
                    Replacement_Policy_tab = returnCallouts_loop.get('tabType')
                    if Replacement_Policy_tab == 'REPLACEMENT':
                        Replacement_Policy = returnCallouts_loop.get('displayText')
                        if 'replacement' in Replacement_Policy.lower():
                            return Replacement_Policy
            except:
                return None

    def get_Return_Policy(self):
        widget_type = 'Return'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            try:
                for deliveryCallouts_loop in slot.get('deliveryCallouts'):
                    # RESPONSE.slots[9].widget.data.deliveryCallouts[1].value.text
                    Return_Policy = deliveryCallouts_loop.get('value').get('text')
                    if Return_Policy:
                        if 'return' in Return_Policy.lower():
                            return Return_Policy
            except:
                return None

    def get_Cancellation_policy(self):
        widget_type = 'DELIVERY'
        slot = self.get_target_slot_data(widget_type)
        if slot:
            try:
                for deliveryCallouts_loop in slot.get('deliveryCallouts'):
                    Cancellation_Policy = deliveryCallouts_loop.get('value').get('text')
                    if Cancellation_Policy:
                        if 'cancellation' in Cancellation_Policy.lower():
                            return Cancellation_Policy
            except:
                return None

    def get_product_details_from_pdp(self):
        widget_type = "PRODUCT_DETAILS"
        slot = self.get_target_slot_data(widget_type)
        if slot:
            if slot.get('renderableComponent'):
                if slot.get('renderableComponent').get('value'):
                    # product_detail = []
                    product_detail_dict = {}
                    details = slot.get('renderableComponent').get('value').get('details')
                    if details:
                        product_detail_dict['details'] =details
                        # product_detail.append(product_detail_details)
                    specifications = slot.get('renderableComponent').get('value').get('specification')
                    if specifications:
                        for specification in specifications:
                            name = specification.get('name')
                            values = specification.get('values')
                            if isinstance(values, list):
                                values = ' | '.join(values)
                            product_detail_dict[name.strip()] = values.strip()
                    # product_detail.append(product_detail_details)
                    return product_detail_dict

    # def get_product_details_from_pdp(self):
    #     widget_type = "PRODUCT_DETAILS"
    #     slot = self.get_target_slot_data(widget_type)
    #     if slot:
    #         if slot.get('renderableComponent'):
    #             if slot.get('renderableComponent').get('value'):
    #                 product_detail = []
    #                 details = slot.get('renderableComponent').get('value').get('details')
    #                 if details:
    #                     product_detail.append(f'details : {details}')
    #                 specifications = slot.get('renderableComponent').get('value').get('specification')
    #                 if specifications:
    #                     for specification in specifications:
    #                         name = specification.get('name')
    #                         values = specification.get('values')
    #                         if isinstance(values, list):
    #                             values = ' | '.join(values)
    #                         product_detail.append(f'{name.strip()} : {values}'.strip())
    #                 return product_detail
