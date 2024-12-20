import re
import json
import jmespath  # For querying JSON-like data structures using expressions
from datetime import datetime, timedelta


class FlipkartParse:
    def __init__(self, response):
        # Constructor initializes the parser with the response data.

        # Get raw JSON data embedded in a specific <script> tag using XPath
        self.response = response
        raw_json = response.xpath('//script[@nonce and contains(text(), "__INITIAL_STATE__ ")]/text()').get('')

        # Extract JSON by splitting and cleaning the string
        data_json = json.loads(raw_json.split("=", 1)[-1][:-1])
        self.data_json = data_json  # Store the parsed JSON for later use

        # Extract phone number if available in the user state
        if self.data_json:
            if 'userService' in self.data_json['userState']:
                phone_number = self.data_json['userState']['userService'].get('mobileNo', None)
                self.phone_number = phone_number
            else:
                self.phone_number = None

        # Extract page context JSON for later use
        self.page_context_json = data_json['pageDataV4']['page']['pageData']['pageContext']

        # Initialize variables to store various product details
        self.product_specification = None
        self.product_details = None
        self.availability = None
        self.notify = None
        self.composed_pincode_delivery = None
        self.other_images = None
        self.product_page_summary = None
        self.highlights = None
        self.seller_widget = None
        self.product_services = None
        self.easy_payment_options = None
        self.offers = list()

        # Parse the page's data to extract specific widgets and their data
        for data in data_json['pageDataV4']['page']['data']:
            for j in data_json['pageDataV4']['page']['data'][data]:
                if j['slotType'] == "WIDGET":
                    widget_type = j['widget']['type']

                    # Match widgets by type and extract their respective data
                    if widget_type in ("PRODUCT_PAGE_SUMMARY_V2", "PRODUCT_PAGE_SUMMARY"):
                        self.product_page_summary = j['widget']['data']
                    if widget_type == "COMPOSED_PINCODE_DELIVERY":
                        self.composed_pincode_delivery = j['widget']['data']
                    if widget_type == "AVAILABILITY":
                        self.availability = j['widget']['data']
                    if widget_type == "NOTIFY":
                        self.notify = j['widget']['data']
                    if widget_type == "PRODUCT_SPECIFICATION":
                        self.product_specification = j['widget']['data']
                    if widget_type == "PRODUCT_DETAILS":
                        self.product_details = j['widget']['data']
                    if widget_type == "MULTIMEDIA":
                        self.other_images = j['widget']['data']
                    if widget_type == "HIGHLIGHTS":
                        self.highlights = j['widget']['data']
                    if widget_type == "SELLER":
                        self.seller_widget = j['widget']['data']
                    if widget_type == "PRODUCT_SERVICES":
                        if 'actions' in j['widget']['data']:
                            self.product_services = j['widget']['data']['actions']
                    if widget_type == "PRODUCT_OFFERS":
                        self.offers = j['widget']['data']['offerGroups']
                    if widget_type == "PAYMENTS_EXTENDED":
                        extended_payment = j['widget']

                        # Extract "Easy Payment Options" if available in extended payment widget
                        if (
                                "header" in extended_payment and
                                extended_payment["header"] and
                                "value" in extended_payment['header'] and
                                extended_payment['header']['value'] and
                                'titleValue' in extended_payment['header']['value'] and
                                extended_payment['header']['value']['titleValue'] and
                                "text" in extended_payment['header']['value']['titleValue'] and
                                extended_payment['header']['value']['titleValue']['text'] == "Easy Payment Options"
                        ):
                            extended_payment = j['widget']['data']
                            for payment in extended_payment:
                                if 'paymentOptions' in payment and extended_payment[payment]:
                                    self.easy_payment_options = [
                                        pay['value']['text'] for pay in extended_payment[payment]
                                    ]

        # Fallback: Use "notify" data as availability if no explicit availability data is present
        if not self.availability and self.notify:
            self.availability = self.notify

        if not self.product_specification and self.product_details:
            self.product_specification = self.product_details

        # Compile a JMESPath expression for querying specific data points
        self.expression = jmespath.compile(
            'pageDataV4.page.pageData.pageContext.fdpEventTracking.events.psi.pr.parameterRating'
        )

    # Method to format an image URL by replacing placeholders with actual values
    def get_image_format(self, image):
        return (
            image
            .replace('{@width}', '1920')  # Replace the width placeholder with 1920
            .replace('{@height}', '1080')  # Replace the height placeholder with 1080
            .replace('{@quality}', '100')  # Replace the quality placeholder with 100
        )

    # Method to retrieve the pincode from the data JSON
    def get_pincode(self):
        if self.data_json:  # Check if JSON data is available
            pincode = self.data_json['pageDataV4']["productPageMetadata"].get('pincode', '0')
            return pincode  # Return the pincode or '0' if not found

    # Method to get the formatted image URL
    def get_image_url(self):
        if self.data_json:  # Check if JSON data is available
            image_url = self.get_image_format(image=self.page_context_json.get('imageUrl','N/A'))
            return image_url  # Return the formatted image URL

    # Method to retrieve the category hierarchy of the product
    def get_category_hierarchy(self):
        if self.data_json:  # Check if JSON data is available
            try:
                product_page_metadata = self.data_json['pageDataV4']["productPageMetadata"]
                category_hierarchy = dict()  # Initialize an empty dictionary for the hierarchy

                # Parse the breadcrumbs for category titles
                breadcrumbs = product_page_metadata["breadcrumbs"]
                for index, category in enumerate(breadcrumbs, start=1):
                    if len(breadcrumbs) == index:  # Skip the last breadcrumb (current page)
                        continue
                    category_hierarchy[f"l{index}"] = category['title']  # Add category to the hierarchy
            except Exception as e:
                print(e)
                category_hierarchy=None
            # Return "N/A" if no categories are found, otherwise return the hierarchy as a JSON string
            return "N/A" if not category_hierarchy else json.dumps(category_hierarchy)

    # Method to retrieve the product pricing details
    def get_product_price(self):
        # Initialize variables to store pricing details
        all_prices = dict()
        selling_price = None
        product_price = None
        discount = None
        mrp = None

        # If product page summary is available, extract pricing data
        if self.product_page_summary:
            if 'pricing' in self.product_page_summary and self.product_page_summary['pricing']:
                pricing = self.product_page_summary['pricing']['value']
                product_price = pricing['finalPrice']['decimalValue']  # Final product price
                # Added Code :-
                # if pricing['prices'][1]['value']:
                #     product_price = pricing['prices'][1]['value']
                # Extract total discount if available
                if 'totalDiscount' in pricing and pricing['totalDiscount']:
                    discount = pricing['totalDiscount']

                # Parse individual price components (MRP, FSP, etc.)
                for price in pricing['prices']:
                    if 'name' in price and 'decimalValue' in price:
                        all_prices[price['name']] = price['decimalValue']
                    if price['priceType']:
                        if "MRP" in price['priceType']:  # Maximum Retail Price
                            mrp = price['decimalValue']
                        if 'FSP' in price['priceType']:  # Final Selling Price
                            selling_price = price['decimalValue']

                # Fallback to extract MRP if not already set
                if 'mrp' in pricing and pricing['mrp'] and not mrp:
                    mrp = pricing['mrp']['decimalValue']
                    if 'Maximum Retail Price' not in all_prices:
                        all_prices[pricing['mrp']['name']] = pricing['mrp']['decimalValue']

        # Fallback to extract pricing from page context if not available in product page summary
        else:
            if 'pricing' in self.page_context_json and self.page_context_json['pricing']:
                pricing = self.page_context_json['pricing']
                product_price = pricing['finalPrice']['decimalValue']

                # Extract total discount if available
                if 'totalDiscount' in pricing and pricing['totalDiscount']:
                    discount = pricing['totalDiscount']

                # Parse individual price components (MRP, FSP, etc.)
                for price in pricing['prices']:
                    if 'name' in price and 'decimalValue' in price:
                        all_prices[price['name']] = price['decimalValue']
                    if price['priceType']:
                        if "MRP" in price['priceType']:  # Maximum Retail Price
                            mrp = price['decimalValue']
                        if 'FSP' in price['priceType']:  # Final Selling Price
                            selling_price = price['decimalValue']

                # Fallback to extract MRP if not already set
                if 'mrp' in pricing and pricing['mrp']:
                    mrp = str(pricing['mrp'])
                    if 'Maximum Retail Price' not in all_prices:
                        all_prices['Maximum Retail Price'] = pricing['mrp']

        # Calculate the discount percentage if possible
        if product_price:
            product_price = float(product_price)
        if mrp:
            mrp = float(mrp)
        if discount and product_price and mrp and mrp > product_price:
            discount = round((1 - (product_price / mrp)) * 100)
        elif discount and (not discount or type(discount) != int):
            discount = round((1 - (product_price / mrp)) * 100)

        # Handle special price cases, ensuring consistency
        try:
            if 'Special Price' in all_prices and eval(all_prices['Special Price']) != product_price:
                if discount != round((1 - (product_price / mrp)) * 100):
                    product_price = eval(all_prices['Special Price'])
        except:
            pass  # Ignore errors during price evaluation

        # Return all price details: all_prices, selling_price, product_price, discount percentage, and MRP
        if selling_price != product_price:
            if discount == 'N/A':
                product_price = mrp
            elif not discount:
                product_price = mrp
        return all_prices, selling_price, product_price, discount, mrp

    # Method to parse and retrieve the catalog name (product name)
    def get_catalog_name(self):
        # Check for 'newTitle' in the page context; use it if available
        if 'newTitle' in self.page_context_json['titles']:
            catalog_name = self.page_context_json['titles']['newTitle']
        else:
            # Fallback to 'title' if 'newTitle' is not present
            catalog_name = self.page_context_json['titles']['title']

        # If there's a subtitle and the catalog_name is still empty, use the subtitle
        if 'subtitle' in self.page_context_json['titles']:
            catalog_name += f" ({self.page_context_json['titles']['subtitle']})"

        # If product_page_summary exists and catalog_name is still not set
        if self.product_page_summary and not catalog_name:
            title_component = self.product_page_summary['titleComponent']['value']
            title = list()
            # Append available components to construct the title
            if 'newTitle' in title_component and 'superTitle' in title_component:
                title.append(title_component['superTitle'])
                title.append(title_component['newTitle'])
                if 'subtitle' in title_component:
                    title.append("(" + title_component['subtitle'] + ")")

            # Join the constructed title or return None if empty
            if title:
                return " ".join(title)
            else:
                return None
        else:
            if catalog_name:
                return catalog_name
            else:
                return None

    # Method to get the estimated arrival date for a product
    def get_arrival_date(self):
        arrival_date = None
        if self.get_is_sold_out() == 'false':
            # Check for delivery data and extract the arrival date text
            if (
                    self.composed_pincode_delivery and
                    'deliveryData' in self.composed_pincode_delivery and
                    self.composed_pincode_delivery['deliveryData'] and
                    'messages' in self.composed_pincode_delivery['deliveryData']
            ):
                arrival_date = self.composed_pincode_delivery['deliveryData']['messages'][0]['value'].get('dateText', '')

            # Fallback to tracking data if arrival date is not found
            if not arrival_date:
                if self.page_context_json['trackingDataV2']:
                    arrival_date = self.page_context_json['trackingDataV2'].get('slaText', '')
            if arrival_date:
                year = datetime.today().year
                if arrival_date:
                    if "Tomorrow" in arrival_date:
                        return (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
                    calculated_value = arrival_date.split("-")[0]
                    if calculated_value and "-" in arrival_date:
                        if calculated_value.date() < datetime.today().date():
                            calculated_value = calculated_value.replace(year=year + 1)
                        return str(calculated_value)
                    else:
                        days = re.findall("([0-9]{1}) Days", arrival_date)
                        if days:
                            days = int(days[0])
                            return (datetime.today() + timedelta(days=days)).strftime("%Y-%m-%d 00:00:00")
                    try:
                        date = datetime.strptime(arrival_date, '%d %b, %A').replace(year=year).strftime("%Y-%m-%d 00:00:00")
                        return date
                    except:
                        return arrival_date
                return arrival_date
        return "N/A"

    # Method to get the shipping charges for a product
    def get_shipping_charges(self):
        shipping_charges = None

        # If the product is unavailable or sold out, skip
        if (
                self.availability
                and self.availability['announcementComponent']
                and self.availability['announcementComponent']['value']['title'] in ['Currently Unavailable', 'Sold Out']
        ):
            pass
        else:
            # Extract shipping charges from delivery data
            if self.composed_pincode_delivery:
                if (
                        self.composed_pincode_delivery['deliveryData']
                        and not self.composed_pincode_delivery['deliveryData']['messages'][0]['value']['freeOption']
                ):
                    shipping_charges = \
                        self.composed_pincode_delivery['deliveryData']['messages'][0]['value']['charge'][0]['decimalValue']

        return shipping_charges

    # Method to check if the product is sold out
    def get_is_sold_out(self):
        is_sold_out = None

        # Check for unavailable or sold-out status in the availability component
        if (
                self.availability
                and self.availability['announcementComponent']
                and self.availability['announcementComponent']['value']['title'] in ['Currently Unavailable', 'Sold Out']
        ):
            is_sold_out = "true"
        else:
            # Check pincode-related errors
            if self.composed_pincode_delivery:
                pincode_component = self.composed_pincode_delivery['pincodeData']['pincodeComponent']
                if pincode_component and 'errorCode' in pincode_component['value']:
                    is_sold_out = "true"

        # Default to "false" if not determined earlier
        if not is_sold_out:
            is_sold_out = "false"

        # Check for 'Add to cart' and 'Buy Now' buttons; if missing, mark as sold out
        add_to_cart = self.response.xpath('//button[text()="Add to cart"]')
        buy_now = self.response.xpath('//button[text()="Buy Now"]')
        if not add_to_cart and not buy_now:
            is_sold_out = "true"

        return is_sold_out

    # Method to retrieve the number of product ratings
    def get_number_of_ratings(self):
        number_of_ratings = None

        # Check if rating count is available in the page context
        if (
                'rating' in self.page_context_json and
                self.page_context_json['rating'] and
                'count' in self.page_context_json['rating']
        ):
            number_of_ratings = self.page_context_json['rating']['count']

        # Fallback to ratings and reviews from the product page summary
        elif (
                self.product_page_summary and
                'ratingsAndReviews' in self.product_page_summary and
                self.product_page_summary['ratingsAndReviews'] and
                'value' in self.product_page_summary['ratingsAndReviews'] and
                self.product_page_summary['ratingsAndReviews']['value'] and
                'rating' in self.product_page_summary['ratingsAndReviews']['value']
        ):
            rating_value = self.product_page_summary['ratingsAndReviews']['value']['rating']
            number_of_ratings = rating_value['count']

        return number_of_ratings

    # Method to retrieve the average product rating
    def get_avg_rating(self):
        avg_rating = None

        # Check if average rating is available in the page context
        if (
                'rating' in self.page_context_json and
                self.page_context_json['rating'] and
                'count' in self.page_context_json['rating']
        ):
            avg_rating = self.page_context_json['rating']['average']

        # Fallback to ratings and reviews from the product page summary
        elif (
                self.product_page_summary and
                'ratingsAndReviews' in self.product_page_summary and
                self.product_page_summary['ratingsAndReviews'] and
                'value' in self.product_page_summary['ratingsAndReviews'] and
                self.product_page_summary['ratingsAndReviews']['value'] and
                'rating' in self.product_page_summary['ratingsAndReviews']['value']
        ):
            rating_value = self.product_page_summary['ratingsAndReviews']['value']['rating']
            avg_rating = rating_value['average']

        return avg_rating

    # Method to extract other images of the product
    def get_others_image(self):  # Done
        if self.other_images:
            other_images = list()
            # Iterate through multimedia components to extract image URLs
            for image in self.other_images['multimediaComponents']:
                image = image['value']
                if 'url' in image:
                    other_images.append(self.get_image_format(image=image['url']))
            return other_images

    # Method to extract manufacturing information and specifications
    def get_manufacturing_and_specification(self):

        if self.product_specification:
            # Extract manufacturing information
            manufacturing_info = dict()
            if (
                    'listingManufacturerInfo' in self.product_specification
                    and self.product_specification['listingManufacturerInfo']
            ):
                manufacturing_info = self.product_specification['listingManufacturerInfo']['value']
                if manufacturing_info and 'detailedComponents' in manufacturing_info:
                    for details in manufacturing_info['detailedComponents']:
                        details = details['value']
                        manufacturing_info[details['subTitle']] = ",".join(details['callouts'])
                if manufacturing_info and 'mappedCards' in manufacturing_info:
                    for card in manufacturing_info['mappedCards']:
                        if 'key' not in card:
                            continue
                        manufacturing_info[card['key']] = ",".join(card['values'])
                if manufacturing_info:
                    if 'mappedCards' in manufacturing_info:
                        del manufacturing_info['mappedCards']
                    if 'detailedComponents' in manufacturing_info:
                        del manufacturing_info['detailedComponents']
                    if 'type' in manufacturing_info:
                        del manufacturing_info['type']

            # Extract product specifications
            product_specification = dict()
            product_detail = dict()
            if 'renderableComponents' in self.product_specification and \
                    self.product_specification['renderableComponents']:
                for component in self.product_specification['renderableComponents']:
                    component = component['value']
                    values = dict()
                    key = component['key']
                    for attribute in component['attributes']:
                        attribute_key = attribute['name']
                        if not attribute_key:
                            attribute_key = key
                        values[attribute_key] = ",".join(attribute['values'])
                    product_specification[key] = values

            # Handle alternate structure for specifications
            elif 'renderableComponent' in self.product_specification and \
                    self.product_specification['renderableComponent']:
                values = dict()
                for component in self.product_specification['renderableComponent']['value'].get('specification', []):
                    values[component['name']] = ",".join(component['values'])
                if 'ProductDetailValue' in self.product_specification['renderableComponent']['value']['type']:
                    product_detail = values
                    tmp_value = self.product_specification['renderableComponent']['value']
                    if 'details' in tmp_value and isinstance(tmp_value['details'], str):
                        product_detail.update({"description": tmp_value['details']})
                else:
                    product_specification['specification'] = values

            return manufacturing_info, product_specification, product_detail

    # Method to retrieve variation IDs
    def get_variation_id(self):
        try:
            # First method of accessing variation data
            data_js = self.data_json['pageDataV4']['page']['data']['ROOT'][1]
            data_js = data_js['widget']['data']['parentProduct']['value']['productSwatch']['products']
        except:
            try:
                # Fallback to an alternate method
                data_js = self.data_json['pageDataV4']['page']['data']
                data_js = data_js["10001"][0]['widget']['data']['singleAttributeSwatch']['value']['products']
            except:
                try:
                    # Second fallback
                    data_js = self.data_json['pageDataV4']['page']['data']
                    data_js = data_js["10002"][4]['widget']['data']['swatchComponent']['value']['products']
                except:
                    data_js = list()

        if data_js:
            variation_id = sorted(list(data_js.keys()))
            return variation_id
        return None

    # Method to extract details of offers and coupons
    def get_offers_coupon_details(self):
        coupon_available = False
        coupon_offers = list()
        offer_details = list()

        if self.offers:
            for offer_component in self.offers:
                for offer in offer_component['renderableComponents']:
                    offer = offer['value']
                    # Check if the offer is a coupon
                    if 'Coupons for you' in offer_component['title']:
                        coupon_available = True
                        coupon_offers.append({
                            "title": "|".join(offer['tags']),
                            "details": offer['formattedText'],
                            "legend": offer_component['title']
                        })
                        continue
                    # General offer details
                    offer_details.append({
                        "title": "|".join(offer['tags']),
                        "details": offer['formattedText'],
                        "legend": offer_component['title']
                    })

        return offer_details, coupon_available, coupon_offers

    # Method to retrieve the brand name
    def get_brand(self):
        brand = self.page_context_json.get('brand', '')
        if brand:
            return brand.strip()  # Ensure no leading or trailing spaces
        else:
            return None

    # Method to retrieve Minimum Order Quantity (MOQ)
    def get_moq(self):
        moq = None
        # Check if MOQ data is available
        if self.product_page_summary and 'moqComponent' in self.product_page_summary:
            try:
                moq = self.product_page_summary['moqComponent']['announcement']['subTitle']['value']['text']
            except:
                pass
        return moq

    # Method to extract the rating breakup
    def get_rating_breakup(self):
        rating_breakup = dict()
        # Check if the rating data exists in the page context JSON
        if (
                'rating' in self.page_context_json and
                self.page_context_json['rating'] and
                'count' in self.page_context_json['rating']
        ):
            # Populate the rating breakup dictionary with data from the JSON
            for index, rating in enumerate(self.page_context_json['rating']['breakup'], start=1):
                rating_breakup[index] = rating

        # Check if rating data exists in product page summary as a fallback
        elif (
                self.product_page_summary and
                'ratingsAndReviews' in self.product_page_summary and
                self.product_page_summary['ratingsAndReviews'] and
                'value' in self.product_page_summary['ratingsAndReviews'] and
                self.product_page_summary['ratingsAndReviews']['value'] and
                'rating' in self.product_page_summary['ratingsAndReviews']['value']
        ):
            rating_value = self.product_page_summary['ratingsAndReviews']['value']['rating']
            # Populate the rating breakup dictionary with data from the summary
            for index, rating in enumerate(rating_value['breakup'], start=1):
                rating_breakup[index] = rating

        return rating_breakup

    # Method to extract highlights of the product
    def get_highlights(self):
        highlights = None
        # Check if the highlights data exists
        if (
                self.highlights
                and 'highlights' in self.highlights
                and 'value' in self.highlights['highlights']
                and 'text' in self.highlights['highlights']['value']
        ):
            # Extract the highlights text
            highlights = self.highlights['highlights']['value']['text']
        return highlights

    # Method to extract ISBN from highlights
    def get_isbn(self):
        isbn = None
        # Check if the highlights data exists
        if (
                self.highlights
                and 'highlights' in self.highlights
                and 'value' in self.highlights['highlights']
                and 'text' in self.highlights['highlights']['value']
        ):
            highlights = self.highlights['highlights']['value']['text']
            # Extract the ISBN if present in the highlights
            for i in highlights:
                if i.lower().startswith('isbn'):
                    isbn = i.split(":")[-1].strip()
                    break
        return isbn

    # Method to extract both highlights and ISBN
    def get_highlights_isbn(self):
        isbn = None
        highlights = None
        # Check if the highlights data exists
        if (
                self.highlights
                and 'highlights' in self.highlights
                and 'value' in self.highlights['highlights']
                and 'text' in self.highlights['highlights']['value']
        ):
            highlights = self.highlights['highlights']['value']['text']
            # Extract the ISBN if present in the highlights
            for i in highlights:
                if i.lower().startswith('isbn'):
                    isbn = i.split(":")[-1].strip()
                    break
        return highlights, isbn

    # Method to extract the seller's return policy
    def get_seller_policy(self):
        seller_policy = list()
        # Check if the seller widget data exists
        if self.seller_widget:
            if 'SellerMetaValue' in self.seller_widget and self.seller_widget['SellerMetaValue']:
                seller_meta_value = self.seller_widget['SellerMetaValue']
                # Extract return policies from the seller metadata
                if seller_meta_value['value'] and 'returnCallouts' in seller_meta_value['value']:
                    for i in seller_meta_value['value']['returnCallouts']:
                        seller_policy.append(i['displayText'])
        return seller_policy

    # Method to extract services offered for the product
    def get_services(self):
        services = list()
        # Check if the product services data exists
        if self.product_services:
            # Extract service descriptions
            services = [service['text'] for service in self.product_services]
        return services

    # Method to extract the product description
    def get_description(self):
        description = "".join(
            self.response.xpath('//*[text()="Description"]/following-sibling::div//text()').getall())
        # Clean up and format the description
        if description.strip():
            description = description.strip().replace("Read More", "")
            return description

    # Method to extract parameterized rating data
    def get_parameterized_rating(self):
        parameterized_rating = self.expression.search(self.data_json)
        return parameterized_rating

    # Method to extract the author information
    def get_author(self):
        author = None
        # Extract author information using XPath
        author_list = self.response.xpath('//div[text()="Author"]/following-sibling::div/a/text()').getall()
        if author_list:
            author = author_list[0].strip()
        return author

    # Method to combine various extracted details into a single JSON object
    def get_other_json(self, data_item, all_prices):
        others = dict()

        # Extract other images
        images_list = self.get_others_image()
        if images_list:
            others['images'] = self.get_others_image()

        # Extract manufacturing info and specifications
        try:
            manufacturing_info, product_specification, product_detail = self.get_manufacturing_and_specification()
            if manufacturing_info:
                others['manufacturing_info'] = manufacturing_info
            if product_specification:
                others['product_specification'] = product_specification
            if product_detail:
                others['product_detail'] = product_detail
        except:
            pass

        # Extract variation IDs
        variation_id = self.response.meta['fk_pid'].split()
        if self.get_variation_id():
            variation_id = self.get_variation_id()
        others['variation_id'] = variation_id

        # Extract offer details
        offer_details, coupon_available, coupon_offers = self.get_offers_coupon_details()
        others['offers'] = offer_details
        others['coupon_status'] = coupon_available
        others['coupon_description'] = coupon_offers

        # Extract brand information
        others['brand'] = self.get_brand()

        # Extract delivery tags
        delivery_tag = self.response.meta['delivery_tag'].split("|")
        others['delivery'] = delivery_tag[0]
        if len(delivery_tag) > 1:
            others['daily_fashion_category'] = delivery_tag[1]

        # Add fixed metadata
        others['data_vendor'] = 'Actowiz'

        # Extract selling price
        selling_price = data_item['selling_price']
        others['NEW_USER_selling_price'] = "N/A" if not selling_price else selling_price

        # Check for "F Assured" flag
        others['f_assured'] = True if '"fAssured":true' in self.response.text else False

        # Extract item ID
        others['item_id'] = self.response.meta['fk_url'].split("?")[0].split("/")[-1]
        if "%20" in others['item_id']:
            others['item_id'] = ""

        # Extract Minimum Order Quantity (MOQ)
        others['MOQ'] = self.get_moq()

        if not others['MOQ']:
            others['MOQ'] = "1"

        # Extract individual ratings count
        rating_breakup = self.get_rating_breakup()
        if rating_breakup:
            others['individualRatingsCount'] = rating_breakup

        # Extract highlights and ISBN
        highlights, isbn = self.get_highlights_isbn()
        if isbn:
            others['isbn'] = isbn
        if highlights:
            others['highlights'] = highlights

        # Extract seller's return policy
        seller_policy = self.get_seller_policy()
        if seller_policy:
            others['seller_return_policy'] = seller_policy

        # Extract product services
        product_services = self.get_services()
        if product_services:
            others['services'] = product_services

        # Add easy payment options if available
        if self.easy_payment_options:
            others["easy_payment_options"] = self.easy_payment_options

        # Merge all prices if provided
        if all_prices:
            others.update(**all_prices)

        # Extract and format product description
        description = self.get_description()
        if description:
            others['description'] = description

        # Add default MOQ if not present
        if "MOQ" not in others:
            others['MOQ'] = "1"

        # Extract parameterized ratings
        others['parameterized_rating'] = self.get_parameterized_rating()

        # Extract author information
        author = self.response.xpath('//div[text()="Author"]/following-sibling::div/a/text()').getall()
        if author:
            others['author'] = author[0].strip()

        return others

    # Method to extract seller details for a given item
    def get_seller_list(self, item):
        seller_list = dict()

        # Check if the seller data exists in the page context and construct seller information
        if self.page_context_json['trackingDataV2'] and 'sellerName' in self.page_context_json['trackingDataV2']:
            seller_list = {
                self.page_context_json['trackingDataV2']['sellerId']: {
                    # Extract and store the Minimum Order Quantity (MOQ), price, rating, and seller name
                    "MOQ": json.loads(item['others'])['MOQ'],
                    "price": item['product_price'],
                    "rating": self.page_context_json['trackingDataV2']['sellerRating'],
                    "SellerName": self.page_context_json['trackingDataV2']['sellerName'].strip()
                }
            }
        return seller_list

    # Method to extract the seller count from the response text (JSON-like data in text format)
    def get_seller_count(self):
        # Use regular expression to find the seller count value
        seller_count = re.findall('"sellerCount":(\d+),', self.response.text)
        if seller_count:
            # If seller count is found, convert to integer
            seller_count = int(seller_count[0])
        else:
            # If no seller count found, set count to 0
            seller_count = 0
        return seller_count

    # Method to find the "Notify Me" button on the page using XPath
    def get_notify_button(self):
        # Look for the button element with text "NOTIFY ME"
        notify_button = self.response.xpath('//button[text()="NOTIFY ME"]')
        return notify_button

    # Method to extract the zip code (pincode) from the product page metadata
    def get_zip_code(self):
        # Extract the pincode value from the product page metadata
        product_page_metadata = self.data_json['pageDataV4']["productPageMetadata"]
        zip_code = product_page_metadata.get('pincode')
        return zip_code

    # Method to get shipping charges, product price, MRP, and discount for the item
    def get_shipping_product_discount_mrp(self, item, status):
        others = json.loads(item['others'])

        # If user is logged out, return shipping charges, price, MRP, and discount as NEW_USER data
        if status == "logout":
            shipping_charges_json = json.dumps(
                {"NEW_USER": str(item['shipping_charges']) if 'shipping_charges' in item and item[
                    'shipping_charges'] else "N/A"}
            )
            product_price_json = json.dumps(
                {"NEW_USER": str(item['product_price']) if 'product_price' in item and item['product_price'] else "N/A"}
            )
            mrp_json = json.dumps(
                {"NEW_USER": str(item['mrp']) if 'mrp' in item and item['mrp'] else "N/A"}
            )
            discount_json = json.dumps(
                {"NEW_USER": str(item['discount']) if 'discount' in item and item['discount'] else "N/A"}
            )
            return shipping_charges_json, product_price_json, mrp_json, discount_json

        else:
            # If user is logged in, return the same details along with coupon information and login status
            is_login = 1
            coupon_status = others['coupon_status']
            coupon_description = others['coupon_description']
            shipping_charges_json = json.dumps(
                {"OLD_USER": str(item['shipping_charges']) if 'shipping_charges' in item and item[
                    'shipping_charges'] else "N/A"}
            )
            product_price_json = json.dumps(
                {"OLD_USER": str(item['product_price']) if 'product_price' in item and item['product_price'] else "N/A"}
            )
            mrp_json = json.dumps(
                {"OLD_USER": str(item['mrp']) if 'mrp' in item and item['mrp'] else "N/A"}
            )
            discount_json = json.dumps(
                {"OLD_USER": str(item['discount']) if 'discount' in item and item['discount'] else "N/A"}
            )

            return shipping_charges_json, product_price_json, mrp_json, discount_json, is_login, coupon_status, coupon_description
