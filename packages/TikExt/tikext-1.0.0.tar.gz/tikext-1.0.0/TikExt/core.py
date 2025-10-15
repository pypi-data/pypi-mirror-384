from faker import Faker
import random,requests,time
from user_agent import generate_user_agent
import asyncio
#import aprintp
import os
import urllib.parse
import re
import random
import binascii
import uuid
import time
from MedoSigner import Argus, Gorgon, Ladon, md5
import requests
import random
import uuid
import os
import time
import secrets
import binascii
from user_agent import generate_user_agent as gg
from random import choice as cc
from random import randrange as rr
from MedoSigner import Argus, Gorgon, md5, Ladon
from urllib.parse import urlencode
import asyncio,urllib,aiohttp
from user_agent import generate_user_agent
from SignerPy import *
import requests, SignerPy, json, secrets, uuid, binascii, os, time, random
class TikExt:
    @staticmethod
    def xor(string):
          return "".join([hex(ord(c) ^ 5)[2:] for c in string])
    def GetStatus(self,email):
            text = requests.get('https://raw.githubusercontent.com/muojoig7/TikLib/refs/heads/main/good.txt').text;lines = [line.strip() for line in text.splitlines() if line.strip()];self.sesionn=random.choice(lines).strip()
            if self.sesionn:
                #print(self.sesionn)
                def sign(params, payload: str = None, sec_device_id: str = "", cookie: str or None = None, aid: int = 1233, license_id: int = 1611921764, sdk_version_str: str = "2.3.1.i18n", sdk_version: int = 2, platform: int = 19, unix: int = None):
                    x_ss_stub = md5(payload.encode('utf-8')).hexdigest() if payload else None
                    data = payload
                    if not unix:
                        unix = int(time.time())
                    return Gorgon(params, unix, payload, cookie).get_value() | {
                        "x-ladon": Ladon.encrypt(unix, license_id, aid),
                        "x-argus": Argus.get_sign(
                            params, x_ss_stub, unix, platform=platform, aid=aid, license_id=license_id,
                            sec_device_id=sec_device_id, sdk_version=sdk_version_str, sdk_version_int=sdk_version
                        )
                    }
            
                encrypted = [hex(ord(c) ^ 5)[2:] for c in email]
                em = "".join(encrypted)
            
                session = requests.Session()
                
            
                secret = secrets.token_hex(16)
                cookies = {
                    "passport_csrf_token": secret,
                    "passport_csrf_token_default": secret,
                    "sessionid": self.sesionn
                }
                session.cookies.update(cookies)
            
                device_brands = ["samsung", "huawei", "xiaomi", "apple", "oneplus"]
                device_types = ["SM-S928B", "P40", "Mi 11", "iPhone12,1", "OnePlus9"]
                regions = ["AE", "IQ", "US", "FR", "DE"]
                languages = ["ar", "en", "fr", "de"]
            
                params = {
                    "app_version":"37.8.8",
                    'passport-sdk-version': "6031490",
                    'device_platform': "android",
                    'os': "android",
                    'ssmix': "a",
                    '_rticket': str(round(random.uniform(1.2, 1.6) * 100000000) * -1) + "4632",
                    'cdid': str(uuid.uuid4()),
                    'channel': "googleplay",
                    'aid': "1233",
                    'app_name': "musical_ly",
                    'version_code': "370104",
                    'version_name': "37.1.4",
                    'manifest_version_code': "2023701040",
                    'update_version_code': "2023701040",
                    'ab_version': "37.1.4",
                    'resolution': "720*1448",
                    'dpi': str(random.choice([420, 480, 532])),
                    'device_type': random.choice(device_types),
                    'device_brand': random.choice(device_brands),
                    'language': random.choice(languages),
                    'os_api': str(random.randint(28, 34)),
                    'os_version': str(random.randint(10, 14)),
                    'ac': "wifi",
                    'is_pad': "0",
                    'current_region': random.choice(regions),
                    'app_type': "normal",
                    'sys_region': random.choice(regions),
                    'last_install_time': str(random.randint(1600000000, 1700000000)),
                    'mcc_mnc': "41840",
                    'timezone_name': "Asia/Baghdad",
                    'carrier_region_v2': "418",
                    'residence': random.choice(regions),
                    'app_language': random.choice(languages),
                    'carrier_region': random.choice(regions),
                    'timezone_offset': str(random.randint(0, 14400)),
                    'host_abi': "arm64-v8a",
                    'locale': random.choice(languages),
                    'ac2': "wifi",
                    'uoo': "0",
                    'op_region': random.choice(regions),
                    'build_number': "37.1.4",
                    'region': random.choice(regions),
                    'ts': str(round(random.uniform(1.2, 1.6) * 100000000) * -1),
                    'iid': str(random.randint(1, 10**19)),
                    'device_id': str(random.randint(1, 10**19)),
                    'openudid': str(binascii.hexlify(os.urandom(8)).decode()),
                    'support_webview': "1",
                    'reg_store_region': random.choice(regions).lower(),
                    'user_selected_region': "0",
                    'cronet_version': "f6248591_2024-09-11",
                    'ttnet_version': "4.2.195.9-tiktok",
                    'use_store_region_cookie': "1"
                }
                      
                      
                payload = f"rules_version=v2&account_sdk_source=app&email_source=1&mix_mode=1&passport_ticket=PPTSGOSAYQ95DDATX2PENDFADNXDTNSTPZC4JU&multi_login=1&type=32&email={email}&email_theme=2"
            
                app_name = "com.zhiliaoapp.musically"
                app_version = f"{random.randint(2000000000, 3000000000)}"
                platform = "Linux"
                os_version = f"Android {random.randint(10, 15)}"
                locales = ["ar_AE", "en_US", "fr_FR", "es_ES"]
                locale = random.choice(locales)
                device_type = random.choice(["phone", "tablet", "tv"])
                build = f"UP1A.{random.randint(200000000, 300000000)}"
                cronet_version = f"{random.randint(10000000, 20000000)}"
                cronet_date = f"{random.randint(2023, 2025)}-{random.randint(1, 12):02}-{random.randint(1, 28):02}"
                quic_version = f"{random.randint(10000000, 20000000)}"
                quic_date = f"{random.randint(2023, 2025)}-{random.randint(1, 12):02}-{random.randint(1, 28):02}"
            
                user_agent = (f"{app_name}/{app_version} ({platform}; U; {os_version}; {locale}; {device_type}; "
                              f"Build/{build}; Cronet/{cronet_version} {cronet_date}; "
                              f"QuicVersion:{quic_version} {quic_date})")
            
            
                x_args = sign(params=urlencode(params), payload="", cookie="")
            
                headers = {
                    'User-Agent': user_agent,
                    'x-tt-passport-csrf-token': secret,
                    'content-type': "application/x-www-form-urlencoded; charset=UTF-8",
                    'x-argus': x_args["x-argus"],
                    'x-gorgon': x_args["x-gorgon"],
                    'x-khronos': x_args["x-khronos"],
                    'x-ladon': x_args["x-ladon"],
                }
                try:
                    url ="https://api22-normal-c-alisg.tiktokv.com/passport/email/bind_without_verify/"
                    response = session.post(url, params=params, data=payload, headers=headers).text#;print(response)
                    if '1023' in response:
                        return {'status':'Good','Dev': 'Mustafa', 'Telegram': '@D_B_HH'}            
                    else:
                        return {'status':'Bad','Dev': 'Mustafa', 'Telegram': '@D_B_HH'} 
                except Exception as e:
                    return {'status':'Error','Info':e,'Dev': 'Mustafa', 'Telegram': '@D_B_HH'}
                    pass    
    def GetUsers(self): 
        agent=str(generate_user_agent())
        faker = Faker()
        faker1 = Faker('ru_RU')
        faker2 = Faker('fa')
        faker3 = Faker('en')
        faker4 = Faker('zh')
        faker5 = Faker('ar')
        faker6 = Faker('ko_KR')
        cl = '1234567890qwertyuiopasdfghjklzxcvbnm.'
        num = '6789'
    #    while True:
        mu = faker.user_name()
        bh = faker1.user_name()
        ch = faker2.user_name()
        dh = faker3.user_name()
        hh = faker4.user_name()
        gh = faker5.user_name()
        bu = faker6.user_name()
        gg = random.choice([       "абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
        'अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहक्षत्रज्ञ',  
     ])
        keyword = ''.join((random.choice(gg) for i in range(random.randrange(3, 15))))
        rng = int("".join(random.choice(num) for _ in range(1)))
        name = "".join(random.choice(cl) for _ in range(rng))
        user = random.choice([mu, bh, ch, dh, hh, gh, bu, name])
        res = requests.get('https://www.tiktok.com/api/search/general/preview/', params={'WebIdLastTime': str(int(time.time())),'aid': '1988','app_language': 'ar','app_name': 'tiktok_web','browser_language': 'en-US','browser_name': 'Mozilla','browser_online': 'true','browser_platform': 'Linux armv81','browser_version': agent,'channel': 'tiktok_web','cookie_enabled': 'true','data_collection_enabled': 'false','device_id': '73' + ''.join(random.choices('0123456789', k=16)),'device_platform': 'web_pc','focus_state': 'true','from_page': 'search','history_len': '3','is_fullscreen': 'false','is_page_visible': 'true','keyword': user,'odinId': '73' + ''.join(random.choices('0123456789', k=16)),'os': 'linux','priority_region': '','referer': '','region': 'DE','screen_height': '780','screen_width': '360','tz_name': 'Asia/Aden','user_is_login': 'false','webcast_language': 'ar',}, headers={'authority': 'www.tiktok.com','accept': '*/*','accept-language': 'ar-YE,ar;q=0.9,en-YE;q=0.8,en-US;q=0.7,en;q=0.6','referer': f'https://www.tiktok.com/search?q={user}&t={str(int(time.time() * 1000))}','sec-ch-ua': '"Not)A;Brand";v="24", "Chromium";v="116"','sec-ch-ua-mobile': '?0','sec-ch-ua-platform': '"Linux"','sec-fetch-dest': 'empty','sec-fetch-mode': 'cors','sec-fetch-site': 'same-origin','user-agent': agent,}).json()
        if 'sug_list' in res:
              for users in res['sug_list']:
                  user = users['content']
                  if ' ' in user:
                      user = user.replace(' ', '')
                  email =  user
                  return {'status':'Good','UserName':email,'Dev':'Mustafa','Telegram':'@D_B_HH'}
    
    def GetLevel(self, username):
        username = username.strip().lstrip('@')
        url = f'https://www.tiktok.com/@{username}'
        headers = {'User-Agent': str(generate_user_agent())}

        try:  
            response = requests.get(url, headers=headers)  
            if '{"userInfo":{' in response.text:  
                # محاولة استخراج معرف المستخدم من كتلة userInfo
                match = re.search(r'"userInfo":\{.*?"id":"([^"]+)"', response.text)  
                if match:  
                    user_id = match.group(1)  
            elif '"user":{"id":"' in response.text:  
                # محاولة استخراج معرف المستخدم من كتلة user
                match = re.search(r'"user":{"id":"([^"]+)"', response.text)  
                if match:  
                    user_id = match.group(1)  
            else:
                user_id = None

            # الرجوع إلى API tikwm.com إذا فشل الاستخراج المباشر
            if not user_id:
                api_url = f"https://www.tikwm.com/api/user/info?unique_id={username}"  
                api_response = requests.get(api_url)  
                if api_response.status_code == 200:  
                    data = api_response.json()  
                    if data.get("code") == 0 and "data" in data:  
                        user_id = data["data"]["user"]["id"]  

            if not user_id:
                return None, None
            #print(f"معرف المستخدم لـ @{username}: {user_id}")
            user_details, raw_response = self.get_tiktok_user_details(user_id)

            if user_details and user_details.get('status_code') == 0:  
                data = user_details.get('data', {})  
                badge_list = data.get('badge_list', [])  
                for badge in badge_list:  
                    combine = badge.get('combine', {})  
                    if combine and 'text' in combine:  
                        text_data = combine.get('text', {})  
                        if 'default_pattern' in text_data:  
                            aa = text_data.get('default_pattern')  
                            return {'status':'Good','Level':text_data['default_pattern'],'Dev':'Mustafa','Telegram':'@D_B_HH'}
                return user_id, user_details  
            else:
                return {'status':'Bad','Dev':'Mustafa','Telegram':'@D_B_HH'}
                #print("فشل في الحصول على تفاصيل المستخدم أو الكود يحتاج تجديد.")  
                return user_id, None  

        except Exception as e:  
            #print(f"حدث خطأ أثناء الحصول على معرف المستخدم: {e}")
            return {'status':'Bad','Info':e,'Dev':'Mustafa','Telegram':'@D_B_HH'}  
            return None, None
    def get_tiktok_user_details(self, user_id, custom_headers=None, custom_params=None):
        """
        يحصل على تفاصيل المستخدم من TikTok باستخدام معرف المستخدم.
        """
        url = "https://webcast22-normal-c-alisg.tiktokv.com/webcast/user/"

        # استخدام رؤوس افتراضية إذا لم يتم توفير رؤوس مخصصة  
        headers = {  
            "Host": "webcast22-normal-c-alisg.tiktokv.com",  
            "cookie": "store-idc=alisg; passport_csrf_token=20e9da8b0e16abaa45d4ce2ad75a1325; passport_csrf_token_default=20e9da8b0e16abaa45d4ce2ad75a1325; d_ticket=913261767c3f16148c133796e661c1d83cf5d; multi_sids=7464926696447099909%3A686e699e8bbbc4e9f5e08d31c038c8e4; odin_tt=e2d5cd703c2e155d572ad323d28759943540088ddc6806aa9a9b48895713be4b585e78bf3eb17d28fd84247c4198ab58fab17488026468d3dde38335f4ab928ad1b9bd82a2fb5ff55da00e3368b4d215; cmpl_token=AgQQAPMsF-RPsLemUeAYPZ08_KeO5HxUv5IsYN75Vg; sid_guard=686e699e8bbbc4e9f5e08d31c038c8e4%7C1751310846%7C15552000%7CSat%2C+27-Dec-2025+19%3A14%3A06+GMT; uid_tt=683a0288ad058879bbc16d3b696fa815e1d72c050bdb2d14b824141806068417; uid_tt_ss=683a0288ad058879bbc16d3b696fa815e1d72c050bdb2d14b824141806068417; sid_tt=686e699e8bbbc4e9f5e08d31c038c8e4; sessionid=686e699e8bbbc4e9f5e08d31c038c8e4; sessionid_ss=686e699e8bbbc4e9f5e08d31c038c8e4; store-country-code=eg; store-country-code-src=uid; tt-target-idc=alisg; ttwid=1%7Cmdx9QyT3L35S3CFNpZ_6a1mG2Q3hbfWvwQh6gY5hjhw%7C1751310949%7C253ef523ddc8960c5f52b286d8ce0afc2623ec081a777dac3ba5606ecdc1bd40; store-country-sign=MEIEDPH3p6xlgJXYVovbBgQgMf22gnCf0op7iOSSy6oKKB7paF60OVLAsxbGkh6BUGAEEF0aMxzItZZ03IrkjedsuYY; msToken=Srtgt7p6ncYXI8gph0ecExfl9DpgLtzOynFNZjVGLkKUjqV0J1JI8aBoE8ERmO5f43HQhtJxcU2FeJweSbFIlIOADOHP_z75VvNeA2hp5LN1JZsKgj-wymAdEVJt",  
            "x-tt-pba-enable": "1",  
            "x-bd-kmsv": "0",  
            "x-tt-dm-status": "login=1;ct=1;rt=1",  
            "live-trace-tag": "profileDialog_batchRequest",  
            "sdk-version": "2",  
            "x-tt-token": "034865285659c6477b777dec3ab5cd0aa70363599c1acde0cd4e911a51fed831bdb2ec80a9a379e8e66493471e519ccf05287299287a55f0599a72988865752a3668a1a459177026096896cf8d50b6e8b5f4cec607bdcdee5a5ce407e70ce91d52933--0a4e0a20da4087f3b0e52a48822384ac63e937da36e5b0ca771f669a719cf633d66f8aed12206a38feb1f115b80781d5cead8068600b779eb2bba6c09d8ae1e6a7bc44b46b931801220674696b746f6b-3.0.0",  
            "passport-sdk-version": "6031490",  
            "x-vc-bdturing-sdk-version": "2.3.8.i18n",  
            "x-tt-request-tag": "n=0;nr=011;bg=0",  
            "x-tt-store-region": "eg",  
            "x-tt-store-region-src": "uid",  
            "rpc-persist-pyxis-policy-v-tnc": "1",  
            "x-ss-dp": "1233",  
            "x-tt-trace-id": "00-c24dca7d1066c617d7d3cb86105004d1-c24dca7d1066c617-01",  
            "user-agent": "com.zhiliaoapp.musically/2023700010 (Linux; U; Android 11; ar; SM-A105F; Build/RP1A.200720.012; Cronet/TTNetVersion:f6248591 2024-09-11 QuicVersion:182d68c8 2024-05-28)",  
            "accept-encoding": "gzip, deflate, br",  
            "x-tt-dataflow-id": "671088640"  
        }  

        if custom_headers:  # دمج الرؤوس المخصصة  
            headers.update(custom_headers)  

        # استخدام معلمات افتراضية إذا لم يتم توفير معلمات مخصصة  
        params = {  
            "user_role": '{"7464926696447099909":1,"7486259459669820432":1}',  
            "request_from": "profile_card_v2",  
            "sec_anchor_id": "MS4wLjABAAAAiwBH59yM2i_loS11vwxZsudy4Bsv5L_EYIkYDmxgf-lv3oZL4YhQCF5oHQReiuUV",  
            "request_from_scene": "1",  
            "need_preload_room": "false",  
            "target_uid": user_id,  
            "anchor_id": "246047577136308224",  
            "packed_level": "2",  
            "need_block_status": "true",  
            "current_room_id": "7521794357553400594",  
            "device_platform": "android",  
            "os": "android",  
            "ssmix": "a",  
            "_rticket": "1751311566864",  
            "cdid": "808876f8-7328-4885-857d-8f15dd427861",  
            "channel": "googleplay",  
            "aid": "1233",  
            "app_name": "musical_ly",  
            "version_code": "370001",  
            "version_name": "37.0.1",  
            "manifest_version_code": "2023700010",  
            "update_version_code": "2023700010",  
            "ab_version": "37.0.1",  
            "resolution": "720*1382",  
            "dpi": "280",  
            "device_type": "SM-A105F",  
            "device_brand": "samsung",  
            "language": "ar",  
            "os_api": "30",  
            "os_version": "11",  
            "ac": "wifi",  
            "is_pad": "0",  
            "current_region": "IQ",  
            "app_type": "normal",  
            "sys_region": "IQ",  
            "last_install_time": "1751308971",  
            "timezone_name": "Asia/Baghdad",  
            "residence": "IQ",  
            "app_language": "ar",  
            "timezone_offset": "10800",  
            "host_abi": "armeabi-v7a",  
            "locale": "ar",  
            "content_language": "ar,",  
            "ac2": "wifi",  
            "uoo": "1",  
            "op_region": "IQ",  
            "build_number": "37.0.1",  
            "region": "IQ",  
            "ts": "1751311566",  
            "iid": "7521814657976928001",  
            "device_id": "7405632852996097552",  
            "openudid": "c79c40b21606bf59",  
            "webcast_sdk_version": "3610",  
            "webcast_language": "ar",  
            "webcast_locale": "ar_IQ",  
            "es_version": "3",  
            "effect_sdk_version": "17.6.0",  
            "current_network_quality_info": '{"tcp_rtt":16,"quic_rtt":16,"http_rtt":584,"downstream_throughput_kbps":1400,"quic_send_loss_rate":-1,"quic_receive_loss_rate":-1,"net_effective_connection_type":3,"video_download_speed":1341}'  
        }  

        if custom_params:  # دمج المعلمات المخصصة  
            params.update(custom_params)  

        try:  
            # توقيع الطلب باستخدام SignerPy
            up = get(params=params)  
            def parse_cookie_string(cookie_string):  
                cookie_dict = {}  
                for item in cookie_string.split(';'):  
                    if item.strip():  
                        try:  
                            key, value = item.strip().split('=', 1)  
                            cookie_dict[key.strip()] = value.strip()  
                        except ValueError:  
                            cookie_dict[item.strip()] = ''  
                return cookie_dict  
            cookie_dict = parse_cookie_string(headers["cookie"])  
            sg = sign(params=up, cookie=cookie_dict)  

            headers.update({  
                'x-ss-req-ticket': sg['x-ss-req-ticket'],  
                'x-ss-stub': sg['x-ss-stub'],  
                'x-argus': sg["x-argus"],  
                'x-gorgon': sg["x-gorgon"],  
                'x-khronos': sg["x-khronos"],  
                'x-ladon': sg["x-ladon"],  
            })  
            headers["accept-encoding"] = "identity"  
            response = requests.get(url, headers=headers, params=params)  

            try:  
                json_data = response.json()  
                if json_data.get('status_code') != 0:  
                    return "الكود يحتاج تجديد (قد يكون بسبب انتهاء صلاحية الكوكيز أو التوقيع)"  

                # معالجة البيانات المتدفقة (إذا كانت موجودة)  
                streamed_content = ""  
                for line in response.iter_lines():  
                    if line:  
                        decoded_line = line.decode('utf-8')  
                        if decoded_line.startswith('data: '):  
                            json_part = decoded_line[6:]  
                            try:  
                                data_part = json.loads(json_part)  
                                if 'choices' in data_part and len(data_part['choices']) > 0:  
                                    delta = data_part['choices'][0].get('delta', {})  
                                    if 'content' in delta and delta['content']:  
                                        streamed_content += delta['content']  
                            except json.JSONDecodeError:  
                                continue  
                if streamed_content:  
                    print(f"محتوى متدفق: {streamed_content}")  

                return json_data, response  
            except json.JSONDecodeError:  
                return  "الكود يحتاج تجديد (فشل في فك تشفير JSON)" 
                return None, response  
            except Exception as e:  
                return f"حدث خطأ أثناء معالجة الاستجابة: {e}"  
                return None, response  

        except Exception as e:  
            return f"حدث خطأ أثناء إرسال الطلب: {e}"
            return None, None
    def GetUser(self,es):
        secret = secrets.token_hex(16)
        xor_email=self.xor(es)
        params = {
            "request_tag_from": "h5",
            "fixed_mix_mode": "1",
            "mix_mode": "1",
            "account_param": xor_email,
            "scene": "1",
            "device_platform": "android",
            "os": "android",
            "ssmix": "a",
            "type": "3736",
            "_rticket": str(round(random.uniform(1.2, 1.6) * 100000000) * -1) + "4632",
            "cdid": str(uuid.uuid4()),
            "channel": "googleplay",
            "aid": "1233",
            "app_name": "musical_ly",
            "version_code": "370805",
            "version_name": "37.8.5",
            "manifest_version_code": "2023708050",
            "update_version_code": "2023708050",
            "ab_version": "37.8.5",
            "resolution": "1600*900",
            "dpi": "240",
            "device_type": "SM-G998B",
            "device_brand": "samsung",
            "language": "en",
            "os_api": "28",
            "os_version": "9",
            "ac": "wifi",
            "is_pad": "0",
            "current_region": "TW",
            "app_type": "normal",
            "sys_region": "US",
            "last_install_time": "1754073240",
            "mcc_mnc": "46692",
            "timezone_name": "Asia/Baghdad",
            "carrier_region_v2": "466",
            "residence": "TW",
            "app_language": "en",
            "carrier_region": "TW",
            "timezone_offset": "10800",
            "host_abi": "arm64-v8a",
            "locale": "en-GB",
            "ac2": "wifi",
            "uoo": "1",
            "op_region": "TW",
            "build_number": "37.8.5",
            "region": "GB",
            "ts":str(round(random.uniform(1.2, 1.6) * 100000000) * -1),
            "iid": str(random.randint(1, 10**19)),
            "device_id": str(random.randint(1, 10**19)),
            "openudid": str(binascii.hexlify(os.urandom(8)).decode()),
            "support_webview": "1",
            "okhttp_version": "4.2.210.6-tiktok",
            "use_store_region_cookie": "1",
            "app_version":"37.8.5"}
        cookies = {
            "passport_csrf_token": secret,
            "passport_csrf_token_default": secret,
            "install_id": params["iid"],
        }
        
        
        
        
        s=requests.session()
        cookies = {
            '_ga_3DVKZSPS3D': 'GS2.1.s1754435486$o1$g0$t1754435486$j60$l0$h0',
            '_ga': 'GA1.1.504663773.1754435486',
            '__gads': 'ID=0cfb694765742032:T=1754435487:RT=1754435487:S=ALNI_MbIZNqLgouoeIxOQ2-N-0-cjxxS1A',
            '__gpi': 'UID=00001120bc366066:T=1754435487:RT=1754435487:S=ALNI_MaWgWYrKEmStGHPiLiBa1zlQOicuA',
            '__eoi': 'ID=22d520639150e74a:T=1754435487:RT=1754435487:S=AA-AfjZKI_lD2VnwMipZE8ienmGW',
            'FCNEC': '%5B%5B%22AKsRol8AtTXetHU2kYbWNbhPJd-c3l8flgQb4i54HStVK8CCEYhbcA3kEFqWYrBZaXKWuO9YYJN53FddyHbDf05q1qY12AeNafjxm2SPp7mhXZaop_3YiUwuo_WHJkehVcl5z4VyD7GHJ_D8nI2DfTX5RfrQWIHNMA%3D%3D%22%5D%5D',
        }
        
        headers = {
            'accept': '*/*',
            'accept-language': 'en,ar;q=0.9,en-US;q=0.8',
            'application-name': 'web',
            'application-version': '4.0.0',
            'content-type': 'application/json',
            'origin': 'https://temp-mail.io',
            'priority': 'u=1, i',
            'referer': 'https://temp-mail.io/',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'x-cors-header': 'iaWg3pchvFx48fY',
        }
        
        json_data = {
            'min_name_length': 10,
            'max_name_length': 10,
        }
        
        response = requests.post('https://api.internal.temp-mail.io/api/v3/email/new', cookies=cookies, headers=headers, json=json_data)
        name=response.json()["email"]
        url = "https://api16-normal-c-alisg.tiktokv.com/passport/account_lookup/email/"
        s.cookies.update(cookies)
        m=SignerPy.sign(params=params,cookie=cookies)
        
        headers = {
          'User-Agent': "com.zhiliaoapp.musically/2023708050 (Linux; U; Android 9; en_GB; SM-G998B; Build/SP1A.210812.016;tt-ok/3.12.13.16)",
          'x-ss-stub':m['x-ss-stub'],
          'x-tt-dm-status': "login=1;ct=1;rt=1",
          'x-ss-req-ticket':m['x-ss-req-ticket'],
          'x-ladon': m['x-ladon'],
          'x-khronos': m['x-khronos'],
          'x-argus': m['x-argus'],
          'x-gorgon': m['x-gorgon'],
          'content-type': "application/x-www-form-urlencoded",
          'content-length': m['content-length'],
        
        }
        
        response = requests.post(url, headers=headers,params=params,cookies=cookies)
        
        if 'data' in response.json():
            try:passport_ticket=response.json()["data"]["accounts"][0]["passport_ticket"]
            except Exception as e:return {'status':e}
        else:
            return {'status':'Bad'}           
        
        name_xor=self.xor(name)
        url = "https://api16-normal-c-alisg.tiktokv.com/passport/email/send_code/"
        params.update({"not_login_ticket":passport_ticket,"email":name_xor})
        m = SignerPy.sign(params=params, cookie=cookies)
        headers = {
            'User-Agent': "com.zhiliaoapp.musically/2023708050 (Linux; U; Android 9; en_GB; SM-G998B; Build/SP1A.210812.016;tt-ok/3.12.13.16)",
            'Accept-Encoding': "gzip",
            'x-ss-stub': m['x-ss-stub'],
            'x-ss-req-ticket': m['x-ss-req-ticket'],
            'x-ladon': m['x-ladon'],
            'x-khronos': m['x-khronos'],
            'x-argus': m['x-argus'],
            'x-gorgon': m['x-gorgon'],
        }
        response = s.post(url, headers=headers, params=params, cookies=cookies)
        
        time.sleep(5)
        cookies = {
            '_ga': 'GA1.1.504663773.1754435486',
            '__gads': 'ID=0cfb694765742032:T=1754435487:RT=1754435487:S=ALNI_MbIZNqLgouoeIxOQ2-N-0-cjxxS1A',
            '__gpi': 'UID=00001120bc366066:T=1754435487:RT=1754435487:S=ALNI_MaWgWYrKEmStGHPiLiBa1zlQOicuA',
            '__eoi': 'ID=22d520639150e74a:T=1754435487:RT=1754435487:S=AA-AfjZKI_lD2VnwMipZE8ienmGW',
            'FCNEC': '%5B%5B%22AKsRol8AtTXetHU2kYbWNbhPJd-c3l8flgQb4i54HStVK8CCEYhbcA3kEFqWYrBZaXKWuO9YYJN53FddyHbDf05q1qY12AeNafjxm2SPp7mhXZaop_3YiUwuo_WHJkehVcl5z4VyD7GHJ_D8nI2DfTX5RfrQWIHNMA%3D%3D%22%5D%5D',
            '_ga_3DVKZSPS3D': 'GS2.1.s1754435486$o1$g0$t1754435503$j43$l0$h0',
        }
        
        headers = {
            'accept': '*/*',
            'accept-language': 'en,ar;q=0.9,en-US;q=0.8',
            'application-name': 'web',
            'application-version': '4.0.0',
            'content-type': 'application/json',
            'origin': 'https://temp-mail.io',
            'priority': 'u=1, i',
            'referer': 'https://temp-mail.io/',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'x-cors-header': 'iaWg3pchvFx48fY'
        }
        
        response = requests.get(
            'https://api.internal.temp-mail.io/api/v3/email/{}/messages'.format(name),
            cookies=cookies,
            headers=headers,
        )
        import re
        try:
            exEm = response.json()[0]
            match = re.search(r"This email was generated for ([\w.]+)\.", exEm["body_text"])
            if match:
                username = match.group(1)
                #print(username)
                return {'status':'Good','username':username,'Dev':'Mustafa','Telegram':'@D_B_HH'}
        except Exception as e:return {'status':'Bad','Info':e,'Dev':'Mustafa','Telegram':'@D_B_HH'}    
        #@staticmethod
 
    def GetInfo(self,username):
        try:
            headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    };url = f"https://www.tiktok.com/@{username}";response = requests.get(url, headers=headers,timeout=10).text;data = response.split('''"userInfo":{"user":{''')[1].split('''</sc''')[0];followers = data.split('"followerCount":')[1].split(',')[0];id = data.split('"id":"')[1].split('"')[0];nickname = data.split('"nickname":"')[1].split('"')[0];following = data.split('"followingCount":')[1].split(',')[0];likes = data.split('"heart":')[1].split(',')[0];ff=f'''
『🔥』ʜɪᴛ ᴛɪᴋᴛᴏᴋ『🔥』
________________________
    User : {username}
    Name : {nickname}
    Id : {id}
________________________
𝙛𝙤𝙡𝙡𝙤𝙬𝙚𝙧𝙨: {followers}
𝙛𝙤𝙡𝙡𝙤𝙬𝙞𝙣𝙜: {following}
𝙡𝙞𝙠𝙚:{likes} 
________________________
BY : @D_B_HH  CH :  @k_1_cc
    '''
            return {'status':'Good','Info':ff,'Dev':'Mustafa','Telegram':'@D_B_HH'}
        except Exception as e:return {'status':'Bad','Dev':'Mustafa','Telegram':'@D_B_HH'}
