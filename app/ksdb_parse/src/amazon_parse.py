import json,re
from datetime import datetime, timedelta
from itemloaders.processors import TakeFirst
from scrapy.loader import ItemLoader
from ksdb_parse.src.item import KsdbAmazonProductItem,clean_name,modifies_image_urls
from itemloaders.processors import MapCompose, Join

class AmazonParseMain:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pass

    def parse(self, response):

        loader = ItemLoader(item=KsdbAmazonProductItem(),response=response)
        loader.default_output_processor = TakeFirst()

        post_code_value = loader.get_xpath(
            '//*[@id="nav-global-location-slot"]//span[@id="glow-ingress-line2" and not(contains(text(), "Select your address"))]//text()',
            MapCompose(clean_name),
            TakeFirst(),
            re="(\d+)",
        )

        loader.add_value('is_zip', 1)
        loader.add_value('zip_code', post_code_value)

        loader.add_value('Id', response.meta["Id"])

        loader.add_value('product_url', response.meta["az_url"])

        if 'position' in response.meta:
            loader.add_value('position', response.meta['position'])

        # PRODUCT NAME
        loader.add_xpath('catalog_name', '//h1[@id="title"]//text()')
        if not len(loader.get_collected_values('catalog_name')):
            loader.add_xpath('catalog_name', '//span[@id="productTitle"]//text()')

        loader.add_value('catalog_id', response.meta["asin"])
        loader.add_value('input_pid', response.meta["_pid"])

        # PRODUCT PRICE
        loader.add_xpath(
            'product_price',
            ('//div[@data-feature-name="corePrice_desktop" or @data-feature-name="corePriceDisplay_desktop"]'
             '//span[contains(@class, "apexPriceToPay") or contains(@class, "PriceToPay") '
             'or @id="priceblock_ourprice"]//text()')
        )
        loader.add_xpath(
            'product_price',
            '//*[@data-a-color="price" and @id="tp-tool-tip-subtotal-price-value"]//*[@class="a-offscreen"]/text()'
        )
        loader.add_xpath('product_price', '//*[@data-a-color="price"]//*[@class="a-offscreen"]/text()')
        loader.add_xpath(
            'product_price',
            '//div[@id="corePrice_desktop"]//td[contains(text(), "Price")]/following-sibling::td/span[@id="priceblock_ourprice"]/span'
        )
        loader.add_xpath(
            'product_price',
            '//*[@class="a-size-base a-color-price" and not (preceding-sibling::span[contains(text(), "New") and contains(text(), "from")])]/text()'
        )
        loader.add_xpath('product_price', '//*[@id="price"]/text()')
        loader.add_xpath(
            'product_price',
            '//*[@class="a-color-base" and contains(text(), "from") and not(@role="article") '
            'and not (ancestor::div[@id="productFactsDesktop_feature_div"])]/text()'
        )
        loader.add_xpath('product_price', '//*[@id="kindle-price"]/text()')
        loader.add_xpath('product_price', '//input[@name="priceValue"]/@value')
        loader.add_value('product_price', '0.0')

        # MRP
        loader.add_xpath(
            'mrp',
            ('//div[@data-feature-name="corePrice_desktop" or @data-feature-name="corePriceDisplay_desktop"]'
             '//span[contains(@class, "priceBlockStrikePriceString") or @data-a-strike="true"]//text()')
        )
        loader.add_xpath(
            'mrp', '//*[contains(text(), "M.R.P.:")]/..//span[@aria-hidden="true" or @id="listPrice"]/text()'
        )
        loader.add_xpath('mrp', '//*[@data-a-color="secondary"]//*[@class="a-offscreen"]/text()')
        loader.add_xpath(
            'mrp', '//div[@id="corePrice_desktop"]//span[contains(@class, "priceBlockStrikePriceString")]//text()'
        )
        loader.add_value('mrp', '0.0')

        # CATEGORY HIERARCHY
        hierarchy_text = loader.get_xpath('//div[@class="a-subheader a-breadcrumb feature"]//li//text()', Join())
        category_hierarchy = {
            f'l{index}': cat
            for index, cat in enumerate([cat.strip() for cat in hierarchy_text.split('›') if cat.strip()], start=1)
        }
        category_hierarchy = json.dumps(category_hierarchy)
        loader.add_value('category_hierarchy', category_hierarchy)

        # SHIPPING CHARGES
        loader.add_xpath(
            'shipping_charges',
            '//*[@id="mir-layout-DELIVERY_BLOCK-slot-DELIVERY_MESSAGE"]//a[contains(text(), "delivery")]/text()'
        )
        loader.add_xpath(
            'shipping_charges',
            '//*[@data-csa-c-delivery-price]/@data-csa-c-delivery-price',
        )
        loader.add_xpath(
            'shipping_charges',
            '//div[@id="deliveryBlockMessage"]//div[contains(text(), "delivery")]/text()',
        )

        # IMAGE_URLS
        image_list = list()
        videos_list = list()
        image_json = re.findall(b"jQuery.parseJSON\(\'(.*?)\'\);", response.body)
        image_json2 = response.xpath('//script[contains(text(),"ImageBlockATF")]//text()').get()

        if image_json:
            image_dict = list()
            try:
                image_json = json.loads(image_json[0])
            except:
                image_json = json.loads(image_json[0].replace(b'\\\'', b''))
            if 'colorToAsin' in image_json:
                for key in image_json['colorToAsin']:
                    if (
                            response.meta['asin'] in image_json['colorToAsin'][key]['asin']
                            and key in image_json['colorImages']
                    ):
                        image_dict = image_json['colorImages'][key]
                        break

            for img in image_dict:

                hiRes = img.get('hiRes')
                large = img.get('large')
                thumb = img.get('thumb')

                if hiRes:
                    image_list.append(hiRes)
                elif large:
                    image_list.append(large)
                elif thumb:
                    image_list.append(thumb)
            try:
                vid_ls = image_json['videos']
            except:
                vid_ls = []

            if vid_ls:
                for vurl in vid_ls:
                    vid_link = vurl.get('url')
                    if vid_link:
                        videos_list.append(vid_link)

        if image_json2 and not image_list:
            try:
                image_json2 = (
                    image_json2.split("{ 'initial':")[1].split("'colorToAsin")[0]
                    .replace('\\n', '').replace('\\t', '').replace('\\r', '').strip()
                )
                if image_json2.endswith('},'):
                    image_json2 = image_json2[:-2]

                image_list_d = json.loads(image_json2)

                for img in image_list_d:
                    hiRes = img.get('hiRes')
                    large = img.get('large')
                    thumb = img.get('thumb')

                    if hiRes:
                        image_list.append(hiRes)
                    elif large:
                        image_list.append(large)
                    elif thumb:
                        image_list.append(thumb)

            except:
                ...

        if image_list:
            loader.add_value('image_url', image_list[0])
        else:
            loader.add_xpath(
                'image_url', '//*[@class="imgTagWrapper"]/img/@src|//*[@class="image-wrapper"]/img/@src'
            )
            loader.add_xpath(
                'image_url',
                '//*[@id="ebooks-img-canvas"]//img[@id="ebooksImgBlkFront"]/@src|//*[@id="img-wrapper"]//img/@src'
            )

        # AVERAGE RATINGS
        loader.add_xpath('avg_rating', '//*[@id="acrPopover"]/@title', re='(.*)out of 5 stars')
        loader.add_xpath('number_of_ratings', '//*[@id="acrCustomerReviewText"]/text()')

        # ARRIVAL DATE
        loader.add_xpath('arrival_date', '//*[@id="mir-layout-DELIVERY_BLOCK"]//b/text()')
        loader.add_xpath('arrival_date', '//*[@id="mir-layout-DELIVERY_BLOCK"]//@data-csa-c-delivery-time')
        loader.add_xpath(
            'arrival_date',
            '//div[@data-csa-c-content-id="almLogoAndDeliveryMessage"]'
            '//span[@class="a-color-base a-text-bold"]/text()'
        )

        # SOLD OUT
        loader.add_value('is_sold_out', 'false')
        unqualified_buy_box = loader.get_xpath('//*[@id="unqualifiedBuyBox"]', Join())
        particle_buy_box = loader.get_xpath('//div[@id="partialStateBuybox"]', Join())
        if 'To buy, select' in particle_buy_box:
            pass
        elif unqualified_buy_box:
            loader.replace_value('is_sold_out', 'true')
        else:
            buy_box_msg = loader.get_xpath('//div[@id="outOfStock" and @class="a-box"]')
            if buy_box_msg and (
                    'Currently unavailable' in str(buy_box_msg) or 'Temporarily out of stock' in str(buy_box_msg)
            ):
                loader.replace_value('is_sold_out', 'true')
            else:
                stock_detail = set(
                    loader.get_xpath(
                        '//*[@id="availability"]//text()',
                        MapCompose(str.lower, str.strip, lambda x: x.strip(".").replace('in stock', 'in-stock'),
                                   str.split)
                    )
                )
                if stock_detail and not {'in-stock', 'only', 'dispatched', 'available'} & stock_detail:
                    loader.replace_value('is_sold_out', 'true')

        if not loader.get_collected_values('product_price') or not loader.get_collected_values('product_price')[0]:
            try:
                pricing_json = json.loads(response.xpath("//script[contains(text(), 'Update cart')]//text()").get())
                pricing_json = json.loads(pricing_json['qsItems'][0]['data'])
                loader.replace_value('product_price', pricing_json['price'])
            except:
                pass

        item = loader.load_item()

        # SETTING MRP
        if not item['mrp']:
            loader.replace_value('mrp', str(item['product_price']))

        # CALCULATING THE DISCOUNTED PERCENTAGE
        if item['product_price'] and item['mrp'] > item['product_price']:
            loader.add_value(
                'discount',
                round((1 - (item['product_price'] / item['mrp'])) * 100)
            )
        else:
            loader.add_value('discount', 'N/A')


        loader.add_value('product_name', item['catalog_name'])
        loader.add_value('product_id', item['catalog_id'])

        # GENERATING THE OTHER JSON FILED
        other_data = dict()

        moq = loader.get_xpath('//*[@name="items[0.base][quantity]"]/@value', TakeFirst())
        if moq:
            other_data['MOQ'] = moq
        else:
            other_data['MOQ'] = '1'

        coupons = response.xpath("//div[@data-csa-c-coupon]//*[contains(@id, 'couponText')]/text()")
        if coupons:
            coupons = ", ".join([i.strip() for i in coupons.getall() if i.strip()])
            other_data['coupon'] = coupons

        if image_list:
            other_data['images'] = image_list[1:]
        else:
            images = loader.get_xpath('//*[@id="altImages"]//img/@src', MapCompose(modifies_image_urls))
            if images:
                other_data['images'] = images

        if videos_list:
            other_data['videos'] = videos_list

        # PRODUCT SPECIFICATION OR PRODUCT TECHNICAL SPECIFICATION
        product_specs = dict()
        # for row in response.xpath((
        #         '//*[@id="technicalSpecifications_section_1"'
        #         ' or  @id="productDetails_techSpec_section_1"'
        #         ' or  @id="productDetails_detailBullets_sections1"'
        #         ']//tr'
        # )):
        for row in response.xpath((
                                  '//*[@id="technicalSpecifications_section_1" or  @id="productDetails_techSpec_section_1" or  @id="productDetails_detailBullets_sections1" or @id="productDetails_db_sections"]//tr')):

            tmp_loader = ItemLoader(selector=row)
            key = tmp_loader.get_xpath('.//th/text()', MapCompose(clean_name), TakeFirst())
            value = tmp_loader.get_xpath('.//td/text()', MapCompose(clean_name), TakeFirst())
            if key and value:
                product_specs[key] = value

            if 'Best Sellers Rank' in key:
                value = row.xpath('.//td//text()').getall()
                if key and value:
                    value1 = [i for i in value if i.strip()]
                    product_specs[key] = re.sub(r'\s+', ' ', ' '.join(value1).strip())

        if product_specs:
            if 'Customer Reviews' in product_specs:
                del product_specs['Customer Reviews']

            other_data['product_specification'] = product_specs
            if 'Brand' in other_data['product_specification']:
                other_data['brand'] = other_data['product_specification']['Brand']

        # ABOUT THIS ITEM
        about_this_item = list()
        li_list = response.xpath('//*[contains(text(),"About this item")]//parent::div[@id="feature-bullets"]//li')
        if not li_list:
            li_list = response.xpath('//*[contains(text(),"About this item")]//parent::div//li')
        if not li_list:
            li_list = response.xpath('//div[@id="feature-bullets"]//li')
        for li in li_list:
            li_text = li.xpath(".//text()").get('').strip()
            if li_text:
                about_this_item.append(li_text)
        if about_this_item:
            other_data['about_this_item'] = about_this_item

        # PRODUCT ATTRIBUTE
        product_attributes = dict()
        attr_xpath = response.xpath('//div[@id="productFactsDesktop_feature_div"]'
                                    '//div[@class="a-fixed-left-grid product-facts-detail"]')
        if not attr_xpath:
            attr_xpath = response.xpath('//div[@id="productOverview_feature_div"]//tr')
        for attr in attr_xpath:
            attr1 = [i.strip() for i in attr.xpath(".//text()").getall() if i.strip()]
            if attr1 and len(attr1) == 2:
                product_attributes[attr1[0]] = attr1[1]
            elif len(attr1) > 2:
                attr_key = [i.strip() for i in attr.xpath('./td[1]//text()').getall() if i.strip()]
                attr_value = [i.strip() for i in attr.xpath('./td[2]/span//text()').getall() if i.strip()]

                if attr_key and attr_value:
                    attr_key = ''.join(attr_key).strip()
                    attr_value = ''.join(attr_value).strip().replace('See more', '')

                    if attr_key and attr_value:
                        product_attributes[attr_key] = attr_value

        additional_information = dict()
        additional_infor = response.xpath(
            '//h3[contains(text(),"Additional Information") and @class="product-facts-title"]/following-sibling::*')
        for add_info in additional_infor:
            if 'h3' in add_info.xpath('.').get():
                break
            else:
                add_k = add_info.xpath('.//span[@class="a-color-base"][1]/text()').get('')
                add_v = add_info.xpath(
                    './/span[@class="a-color-base"][1]/../../following-sibling::div//span[@class="a-color-base"]/text()').get(
                    '')
                if add_k and add_v:
                    if not all(
                            item in {add_k.strip(): add_v.strip()}.items() for item in product_attributes.items()):
                        product_attributes.pop(add_k, None)
                        additional_information[add_k.strip()] = add_v.strip()

        ##add 23022024
        selected_variant_loop = response.xpath('//span[@class="selection"]')
        for select_ in selected_variant_loop:
            select_key = select_.xpath('./preceding-sibling::label/text()').get('')
            select_value = select_.xpath('./text()').get('')
            if select_value and select_key:
                product_attributes[select_key.replace(":", "").strip()] = select_value.strip()

        ##add 22032024
        dropdown_variant=response.xpath('//div[contains(@id,"variation_") and contains(@id,"_name")]')
            if not dropdown_variant:
                dropdown_variant=response.xpath('//div[contains(@id,"variation_")]')
        for drop_v in dropdown_variant:
            drop_label=drop_v.xpath('.//label/text()').get()
            drop_value=drop_v.xpath('.//span[@class="a-dropdown-container"]//option[@selected]/text()').get()
            if drop_label and drop_value:
                product_attributes[drop_label.replace(":", "").strip()] = drop_value.strip()

        ##add 23022024 use by xpath
        if response.xpath('//div[@data-feature-name="expiryDate"]'):
            exp_key = response.xpath('//div[@data-feature-name="expiryDate"]/span[1]/text()').get('')
            exp_val = response.xpath('//div[@data-feature-name="expiryDate"]/span[2]/text()').get('')
            
            ##add 22032024
            if not exp_val and not exp_key:
                exp_key = response.xpath('//div[@data-feature-name="expiryDate"]//span[1]/text()').get('')
                exp_val = response.xpath('//div[@data-feature-name="expiryDate"]//span[2]/text()').get('')
            if exp_key.strip() and exp_val.strip():
                product_attributes[exp_key.replace(":", "").strip()] = exp_val.strip()

        ##add 23022024 bsr in attrib
        if response.xpath('//div[@id="glance_icons_div"]//td//span[1]'):
            for attrib in response.xpath('//div[@id="glance_icons_div"]//td//span[1]'):
                extra_key = attrib.xpath('./text()').get('')
                extra_val = attrib.xpath('./following-sibling::span/text()').get('')

                if extra_key.strip() and extra_val.strip():
                    product_attributes[extra_key.replace(":", "").strip()] = extra_val.strip()

        ##add 05032024
        book_specs = response.xpath(
            '//li[contains(@class,"carousel-attribute-card")]//div[contains(@class,"rpi-attribute-label")]')
        for books in book_specs:
            bk = books.xpath('./span/text()').get()
            bv = books.xpath('./following-sibling::div[contains(@class,"rpi-attribute-value")]/span/text()').get()
            
            ##add 22032024
            if not bv:
                bv = books.xpath('./following-sibling::div[contains(@class,"rpi-attribute-value")]//span/text()').getall()
                if bv:
                    bv=' '.join(bv).replace('\n','').replace('\r','').replace('\t','').strip()
            if bk and bv:
                product_attributes[bk.replace(":", "").strip()] = bv.strip()

        if product_attributes:
            other_data['product_attributes'] = product_attributes

        # PRODUCT DETAILS
        product_detail = dict()
        for detail in response.xpath('//*[@id="detailBullets_feature_div"]//li'):
            tmp_loader = ItemLoader(selector=detail)
            key = tmp_loader.get_xpath('.//text()', MapCompose(clean_name))
            if key:
                if not key[0].count(":"):
                    continue
                key[0] = key[0].replace(":", "").strip()
                product_detail[key[0]] = " ".join(key[1:]) if len(key) > 1 else ""

        if response.xpath(
                '//*[@id="detailBullets_feature_div"]//following-sibling::ul//span[contains(text(),"Best Sellers Rank")]'):
            bsr_text = response.xpath(
                '//*[@id="detailBullets_feature_div"]//following-sibling::ul//span[contains(text(),"Best Sellers Rank")]/..//text()').getall()
            if bsr_text:
                bsr_text = re.sub(r'\s+', ' ', ' '.join(bsr_text).replace("Best Sellers Rank:", "").strip())
                if bsr_text:
                    product_detail['Best Sellers Rank'] = bsr_text

        if product_detail:
            if 'Customer Reviews' in product_detail:
                del product_detail['Customer Reviews']

            other_data['product_detail'] = product_detail
            if 'Brand' in other_data['product_detail']:
                other_data['brand'] = other_data['product_detail']['Brand']

        if 'brand' not in other_data:
            brand = response.xpath('//a[@id="bylineInfo" and contains(text(), "Brand")]/text()').get('').strip()
            if brand:
                other_data['brand'] = brand

        # SELLER DETAILS
        seller_detail = dict()

        seller_loop = response.xpath('//div[@class="tabular-buybox-container"]//div[@class="tabular-buybox-text"]')
        if seller_loop:
            for sell in seller_loop:
                attrib_name = sell.xpath('./@tabular-attribute-name').get()
                attrib_value = sell.xpath('.//span//text()').get()
                if attrib_name and attrib_value:
                    if attrib_name == 'Sold by':
                        seller_link = sell.xpath('.//a[@id="sellerProfileTriggerId"]/@href').get()
                        if seller_link:
                            seller_detail['Seller_link'] = seller_link
                    seller_detail[attrib_name.strip()] = attrib_value.strip()
        if seller_detail:
            other_data['seller_detail'] = seller_detail

        # OFFER DETAILS
        offer_details = list()
        offer_old = response.xpath('//div[contains(@class, "offers-holder")]//ol/li[@role="listitem"]')
        for offer in offer_old:
            offer_dict = dict()
            offer_dict['title'] = " ".join(
                offer.xpath('.//*[contains(@class, "offers-items-title")]//text()').getall()
            ).strip()
            offer_dict['details'] = " ".join(
                offer.xpath('.//*[contains(@class, "a-truncate-full")]//text()').getall()
            ).strip()
            if offer_dict not in offer_details and (offer_dict['title'] or offer_dict['details']):
                offer_details.append(offer_dict)
        # OFFER DETAILS NEW
        new_offer = response.xpath(
            '//span[@class="promotion-description"]//span[contains(@class,"a-truncate")]//span[@class="description" and (following-sibling::span[contains(@data-promotionmodalid,"-modal-1")])]')
        if not new_offer and not offer_old:
            new_offer = response.xpath(
                '//span[@class="promotion-description"]//span[contains(@class,"a-truncate")]//span[@class="description"]')
        for new_off in new_offer:
            offer_val = new_off.xpath('./text()').get('')
            offer_key = new_off.xpath('./preceding-sibling::span[@class="sopp-offer-title"]/text()').get('')
            if offer_key and offer_val:
                off_dict = dict()
                off_dict['title'] = offer_key.replace(':', '').strip()
                off_dict['details'] = offer_val.strip()

                if off_dict not in offer_details:
                    offer_details.append(off_dict)

        if offer_details:
            other_data['offers'] = offer_details

        other_data['deal_of_the_day'] = True if response.xpath(
            '//span[text()="Deal of the Day"]//ancestor::span[@class="dealBadge"]'
        ) else False

        other_data['deal_price'] = True if response.xpath(
            '//span[text()="Deal"]//ancestor::span[@class="dealBadge"]'
        ) else False

        other_data['bundle_list_price'] = True if "Bundle List Price" in response.text else False

        # ------------------ NEW
        if response.xpath('//span[text()="Prime Day launch"]'):
            other_data['prime_day_launch'] = True

        best_seller_badge = dict()
        best_seller_badge['is_badge_available'] = False

        badge_object = response.xpath('//a[@class="badge-link" and @title]')
        if badge_object:
            best_seller_badge['is_badge_available'] = True
            best_seller_badge['badge_text'] = badge_object.xpath('.//i/text()').get('')
            best_seller_badge['badge_cat_name'] = badge_object.attrib['title']
            best_seller_badge['badge_cat_link'] = badge_object.attrib['href']

        other_data['best_seller_badge'] = best_seller_badge
        # ------------------
        # ------------------ NEW

        if response.xpath('//div[@data-feature-name="acBadge"]//*[contains(@class,"ac-badge-rectangle")]'):
            other_data['amazon_choice'] = True
        else:
            other_data['amazon_choice'] = False
        # ------------------

        # ------------------ NEW
        if response.xpath('//div[@data-feature-name="shippingMessageInsideBuyBox"]//*[@aria-label="Fulfilled"]'):
            other_data['amazon_fulfilled'] = True
        else:
            other_data['amazon_fulfilled'] = False
        # ------------------

        # ------------------ NEW
        description = loader.get_xpath(
            '//div[@id="productDescription_feature_div"]//div[@id="productDescription"]//text()',
            MapCompose(clean_name),
            Join()
        )
        if not description:
            description = response.xpath('//div[@id="productDescription"]//text()').getall()
            if description:
                description = [i.strip() for i in description if i.strip()]
                description = ' '.join(description).replace('\n', '').replace('\r', '').replace('\t', '').strip()
        if description:
            other_data['description'] = description
        # ------------------

        if 'dimensionToAsinMap' not in response.text:
            other_data['variation_id'] = response.meta['asin'].split()
        else:
            variation_id = list()
            variation_id.append(response.meta['asin'])
            all_asin = re.findall(r'dimensionToAsinMap\" :(.*?)\n', response.text)[0]
            all_asin_json = json.loads(all_asin.strip(",").strip())
            for asin in all_asin_json:
                asin = all_asin_json[asin]
                if asin not in variation_id:
                    variation_id.append(asin)

            other_data['variation_id'] = sorted(variation_id)

        # other_data['delivery'] = response.meta['delivery_tag']
        other_data['data_vendor'] = 'Actowiz'

        rating_dict = dict()
        rating_k = 5
        for rat in response.xpath('//table[@id="histogramTable"]//tr//div[@class="a-meter"]'):
            val = rat.xpath('.//@aria-valuenow').get('')
            rating_dict[rating_k] = val
            rating_k -= 1
        other_data['individualRatingsCount'] = rating_dict

        seller_policy = response.xpath('//div[@id="iconfarmv2_feature_div"]//*[@alt]/@alt').getall()
        if seller_policy:
            seller_policy = [i.strip() for i in seller_policy if i.strip()]
            if seller_policy:
                other_data['seller_return_policy'] = seller_policy

        # new headers 23022024

        if response.xpath('//div[@id="outer-nveg"]'):
            other_data['non_veg_indicator'] = True

        if response.xpath('//div[@id="outer-veg"]'):
            other_data['veg_indicator'] = True

        ##add 26022024
        additional_services = dict()
        if response.xpath('//div[@id="ppdBundlesEnhancedBox"]//span[@id="ppdBundlesHeading"]'):
            for bundle in response.xpath('//div[@id="ppdBundlesEnhancedBox"]//span[@id="ppdBundlesHeading"]'):
                bundle_text = bundle.xpath('./b/text()').get()
                bundle_price = bundle.xpath(
                    './..//following-sibling::div//span[@id="ppdBundlesPriceValueId"]/text()').get()
                if bundle_text and bundle_price:
                    additional_services['service_name'] = bundle_text.strip()
                    additional_services['service_price'] = bundle_price.strip()

        if additional_services:
            other_data['additional_services'] = additional_services

        if response.xpath('//div[@data-feature-name="customerReviewsAttribute"]'):
            headname = response.xpath('//div[@data-feature-name="customerReviewsAttribute"]//h1/text()').get('')
            if not headname:
                headname = 'Customer ratings'
            extra_rating_dict = dict()
            for customer_rating in response.xpath(
                    '//div[@data-feature-name="customerReviewsAttribute"]//span[@class="a-size-base a-color-base"]'):
                extra_rating_key = customer_rating.xpath('./text()').get('')
                extra_rating_val = customer_rating.xpath(
                    './../../following-sibling::div//span[@class="a-icon-alt"]/text()').get('')

                if extra_rating_key and extra_rating_val:
                    extra_rating_dict[extra_rating_key.strip()] = extra_rating_val.strip()
            if extra_rating_dict:
                other_data['extra_rating'] = {headname.strip(): extra_rating_dict}

        certifications = list()
        if response.xpath('//div[@class="provenance-certifications-row-description"]'):
            for cert in response.xpath('//div[@class="provenance-certifications-row-description"]'):
                cert_k = cert.xpath('./div/text()').get('')
                cert_v = cert.xpath('.//span[contains(@class,"a-truncate-full")]//text()').get('')
                if cert_k and cert_v:
                    certifications.append({"title": cert_k.strip(), "details": cert_v.strip()})

        if certifications:
            other_data['certifications'] = certifications

        extra_description = response.xpath('//div[@id="bookDescription_feature_div"]//text()').getall()
        if extra_description:
            extra_description = [i.strip() for i in extra_description if i.strip() and i != 'Read more']
            extra_description = ' '.join(extra_description).replace('\n', '').replace('\r', '').replace('\t',
                                                                                                        '').strip()
            if extra_description:
                other_data['extra_description'] = extra_description

        luxury_beauty = response.xpath('//a[@id="beautyBadgeDetails"]')
        if luxury_beauty:
            other_data['luxury_beauty_badge'] = True

        loader.add_value('others', json.dumps(other_data))

        item = loader.load_item()

        if (
                "Currently unavailable" in response.text and
                "We don't know when or if this item will be back in stock" in response.text
        ):
            del item['product_price']
            del item['mrp']
            del item['shipping_charges']
            del item['discount']

        if 'product_price' in item and 'mrp' in item and item['product_price'] > item['mrp']:
            item['product_price'], item['mrp'] = item['product_price'], item['product_price']
            if 'discount' in item:
                del item['discount']

        return item
