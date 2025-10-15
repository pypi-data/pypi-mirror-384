# -*- coding: UTF-8 -*-

import sys
from curl_cffi import requests
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from loguru import logger

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

import warnings
warnings.filterwarnings("ignore")


class KohlCheckBalanceParams(BaseModel):
    giftCardNumber: str
    giftCardPin: str
    g_recaptcha_response: str  # 使用下划线命名，便于代码提示
    
    def to_api_dict(self) -> dict:
        """转换为API需要的字典格式"""
        data = self.dict()
        # 处理特殊字段的命名
        if 'g_recaptcha_response' in data:
            data['g-recaptcha-response'] = data.pop('g_recaptcha_response')
        return data

class LululemonCheckBalanceParams(BaseModel):
    cardNumber: str
    pin: str

class WbiParams(BaseModel):
    cardNoH: str
    pinNoH: str
    g_recaptcha_response: str

    def to_api_dict(self) -> dict:
        """转换为API需要的字典格式"""
        data = self.dict()
        # 处理特殊字段的命名
        if 'g_recaptcha_response' in data:
            data['g-recaptcha-response'] = data.pop('g_recaptcha_response')
        return data

class DicksCheckBalanceParams(BaseModel):
    cardNumber: str
    pin: str

class FinishlineCheckBalanceParams(BaseModel):
    giftCardNumber: str
    giftCardPin: str

class FootlockerCheckBalanceParams(BaseModel):
    svcNumber: str
    svcPIN: str

class ReiCheckBalanceParams(BaseModel):
    giftCardNumber: str
    pin: str

class One4AllCheckBalanceParams(BaseModel):
    card_number: str
    card_cvv: str

class SaksCheckBalanceParams(BaseModel):
    token: str
    gcNumber: str
    gcPin: str

class CoachCheckBalanceParams(BaseModel):
    cardNumber: str
    pin: str

class FandangoCheckBalanceParams(BaseModel):
    code: str
    pin: str

class ColumbiaCheckBalanceParams(BaseModel):
    giftCertID: str
    giftCertPin: str

class HomeDepotCheckBalanceParams(BaseModel):
    card_number: str
    pin: str

class EtsyRegisterParams(BaseModel):
    first_name: str
    email: str
    password: str

class PrizepicksLoginParams(BaseModel):
    email: str
    password: str

class FifaLoginParams(BaseModel):
    email: str
    password: str

class AuspostTrackParams(BaseModel):
    tracking_ids: List[str]

class NorseSearchFlightsParams(BaseModel):
    currency: str
    departureDate: str
    returnDate: str
    destinations: str
    isOneWay: str
    origins: str
    residency: str
    adult: int
    partner: str

class ScootBookingParams(BaseModel):
    recordLocator: str
    firstName: str
    lastName: str
    origin: str
    destination: str
    hcaptchaToken: str
    isHcaptchaEnabled: bool

class MyPrepaidValidateParams(BaseModel):
    code: str

class PBandaiCartParams(BaseModel):
    cookies: Dict[str, Any]
    order: str
    model_no: str
    modelname: str

class MicrosoftCreateParams(BaseModel):
    BirthDate: str
    FirstName: str
    LastName: str
    MemberName: str
    Password: str

class GodaddyLoginParams(BaseModel):
    password: str
    username: str

class UltimateDiningLoginParams(BaseModel):
    email: str
    password: str

class FlightInfo(BaseModel):
    departurePort: str
    departureDate: str
    arrivalPort: str

class PassengerInfo(BaseModel):
    passengerType: str
    passengerSubType: Optional[str] = None
    quantity: int

class AjetAvailabilityParams(BaseModel):
    flights: List[FlightInfo]
    passengers: List[PassengerInfo]
    tripType: str

class AjetPnrLoginParams(BaseModel):
    bookingId: str
    surname: str
    recaptchaToken: str

class AjetGetBookingDetailParams(BaseModel):
    bookingId: str
    surname: str
    recaptchaToken: str

class AttCheckParams(BaseModel):
    userId: str
    domain: str

class EasyjetFindParams(BaseModel):
    bookingReference: str
    passengerLastName: str

class EurowingsBookingParams(BaseModel):
    identificationType: str
    locale: str
    processId: str
    bookingCode: str
    passengerLastName: str

class FastPeopleSearchParams(BaseModel):
    name: str
    address: str

class HiltonTokenParams(BaseModel):
    app_id: str

class HiltonCustomerParams(BaseModel):
    access_token: str

class KoreanAirLoginParams(BaseModel):
    userId: str
    password: str

class MaerskTokenParams(BaseModel):
    x_acm_username: str
    x_acm_password: str

    def to_api_dict(self) -> dict:
        """转换为API需要的字典格式"""
        data = self.dict()
        # 处理特殊字段的命名
        if 'x_acm_username' in data:
            data['x-acm-username'] = data.pop('x_acm_username')
        if 'x_acm_password' in data:
            data['x-acm-password'] = data.pop('x_acm_password')
        return data

class MarriottLoginParams(BaseModel):
    email: str
    password: str

class MarriottEnrollParams(BaseModel):
    email: str

class PokemonLoginParams(BaseModel):
    email: str
    password: str
    rechapchToken: str

class PokemonLotteryListParams(BaseModel):
    cookies: Dict[str, str]

class PokemonApplyLotteryParams(BaseModel):
    cookies: Dict[str, str]
    itemPrizeId: str
    jwt_token: str
    lotteryGroupId: str

class SephoraCheckBalanceParams(BaseModel):
    gcNumber: str
    gcPin: str
    captchaToken: str

class TextnowLoginParams(BaseModel):
    username: str
    password: str

class WalmartCheckBalanceParams(BaseModel):
    cardNumber: str
    pin: str

class WalmartCaCheckBalanceParams(BaseModel):
    cardNumber: str
    pin: str

class WalmartWalletParams(BaseModel):
    cookies: Dict[str, str]

class FlightSegment(BaseModel):
    arrivalStation: str
    departureDate: str
    departureStation: str

class WizzairSearchParams(BaseModel):
    adultCount: int
    childCount: int
    flightList: List[FlightSegment]
    infantCount: int
    isFlightChange: bool
    wdc: bool

class HmCheckBalanceParams(BaseModel):
    cardPin: str
    cardNumber: str


def run_unlocker(
    user_token: str,
    site: str,
    action: str,
    params: dict,
    user_agent: Optional[str] = None,
    proxy: Optional[str] = None,
    mode: Literal["generate", "cache"] = "cache",
    timeout: int = 60,
    branch: Optional[str] = None,
    auth: bool = False, 
    internal_host: bool = True,
    developer_id: Optional[str] = None,
    debug: bool = False
) -> dict:
    for k, v in list(params.items()):
        if callable(v):
            params[k] = v()
    
    headers = {
        'user-token': user_token
    }
    if developer_id:
        headers["Developer-Id"] = developer_id
    
    json_data = {
        'href': "https://" + site + "/",
        'action': action,
        'params': params,
        'user_agent': user_agent,
        'proxy': proxy
    }
    if mode == "generate":
        json_data["mode"] = "generate"
    
    if auth is True:
        json_data["is_auth"] = True
    
    if branch:
        json_data["branch"] = branch
    
    if internal_host:
        api = "http://api.nocaptcha.cn/api/wanda/site/unlocker"
    else:
        api = "http://api.nocaptcha.io/api/wanda/site/unlocker"
    
    resp = requests.post(api, headers=headers, json=json_data, timeout=timeout).json()
    if debug:
        logger.debug(resp)
        
    return resp


async def async_run_unlocker(
    user_token: str,
    site: str,
    action: str,
    params: dict,
    user_agent: Optional[str] = None,
    proxy: Optional[str] = None,
    mode: Literal["generate", "cache"] = "cache",
    timeout: int = 60,
    branch: Optional[str] = None,
    auth: bool = False, 
    internal_host: bool = True,
    developer_id: Optional[str] = None,
    debug: bool = False
) -> dict:
    for k, v in list(params.items()):
        if callable(v):
            params[k] = v()
    
    headers = {
        'user-token': user_token
    }
    if developer_id:
        headers["Developer-Id"] = developer_id
    
    json_data = {
        'href': "https://" + site + "/",
        'action': action,
        'params': params,
        'user_agent': user_agent,
        'proxy': proxy
    }
    if mode == "generate":
        json_data["mode"] = "generate"
    
    if auth is True:
        json_data["is_auth"] = True
    
    if branch:
        json_data["branch"] = branch
    
    if internal_host:
        api = "http://api.nocaptcha.cn/api/wanda/site/unlocker"
    else:
        api = "http://api.nocaptcha.io/api/wanda/site/unlocker"
    
    async with requests.AsyncSession() as session:
        resp = (await session.post(api, headers=headers, json=json_data, timeout=timeout)).json()
        
    if debug:
        logger.debug(resp)
    
    return resp


class Unlocker:
    
    def __init__(
        self, 
        user_token: str, 
        auth: bool = False,
        branch: Optional[str] = None,
        internal_host: bool = True,
        developer_id: Optional[str] = None,
        timeout: int = 60,
        debug: bool = False
    ):
        """
        @param user_token: 账号 token
        @param auth: 是否包月
        @param branch: 分支名
        @param internal_host: 是否国内域名
        @param developer_id: 开发者 id
        @param timeout: 超时时间: 秒
        @param debug: 是否输出结果
        """
        self._user_token = user_token
        self._auth = auth
        self._branch = branch
        self._internal_host = internal_host
        self._developer_id = developer_id
        self._timeout = timeout
        self._debug = debug
    
    def kohls_checkbalance(
        self, 
        params: KohlCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Kohl's 查卡"""
        return run_unlocker(
            self._user_token, 'www.kohls.com', 'checkbalance', params.to_api_dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    def lululemon_checkbalance(
        self, 
        params: LululemonCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Lululemon 查卡"""
        return run_unlocker(
            self._user_token, 'shop.lululemon.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def wbi_servlet(
        self, 
        params: WbiParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Adidas 查卡"""
        return run_unlocker(
            self._user_token, 'wbiprod.storedvalue.com', 'wb_servlet', params.to_api_dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def dicks_checkbalance(
        self, 
        params: DicksCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Dick's Sporting Goods 查卡"""
        return run_unlocker(
            self._user_token, 'www.dickssportinggoods.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def finishline_checkbalance(
        self, 
        params: FinishlineCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Finish Line 查卡"""
        return run_unlocker(
            self._user_token, 'www.finishline.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def footlocker_checkbalance(
        self, 
        params: FootlockerCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Foot Locker 查卡"""
        return run_unlocker(
            self._user_token, 'self._user_token, www.footlocker.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def rei_checkbalance(
        self, 
        params: ReiCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """REI 查卡"""
        return run_unlocker(
            self._user_token, 'www.rei.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def one4all_checkbalance(
        self, 
        params: One4AllCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """One4All 查卡"""
        return run_unlocker(
            self._user_token, 'www.one4all.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def saks_checkbalance(
        self, 
        params: SaksCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Saks Fifth Avenue 查卡"""
        return run_unlocker(
            self._user_token, 'www.saksfifthavenue.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def coach_checkbalance(
        self, 
        params: CoachCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Coach 查卡"""
        return run_unlocker(
            self._user_token, 'www.coach.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def fandango_checkbalance(
        self, 
        params: FandangoCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Fandango 查卡"""
        return run_unlocker(
            self._user_token, 'tickets.fandango.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def columbia_checkbalance(
        self, 
        params: ColumbiaCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Columbia 查卡"""
        return run_unlocker(
            self._user_token, 'www.columbia.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def homedepot_checkbalance(
        self, 
        params: HomeDepotCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Home Depot 查卡"""
        return run_unlocker(
            self._user_token, 'www.homedepot.com', 'recipient_experience_checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def etsy_register(
        self, 
        params: EtsyRegisterParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Etsy 注册"""
        return run_unlocker(
            self._user_token, 'www.etsy.com', 'register', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def prizepicks_login(
        self, 
        params: PrizepicksLoginParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """PrizePicks 登录"""
        return run_unlocker(
            self._user_token, 'app.prizepicks.com', 'login', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def fifa_login(
        self, 
        params: FifaLoginParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """FIFA 登录"""
        return run_unlocker(
            self._user_token, 'auth.fifa.com', 'login', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def auspost_track(
        self, 
        params: AuspostTrackParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Auspost 追踪"""
        return run_unlocker(
            self._user_token, 'auspost.com.au', 'track', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def norse_search_flights(
        self, 
        params: NorseSearchFlightsParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Norse 搜索航班"""
        return run_unlocker(
            self._user_token, 'connections.flynorse.com', 'search_flights', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def scoot_booking_retrieval(
        self, 
        params: ScootBookingParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Scoot 预订检索"""
        return run_unlocker(
            self._user_token, 'manage.flyscoot.com', 'booking_retrieval', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def myprepaid_validate(
        self, 
        params: MyPrepaidValidateParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """MyPrepaid 验证"""
        return run_unlocker(
            self._user_token, 'myprepaidcenter.com', 'validate_virtual_code', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def pbandai_cart_add(
        self, 
        params: PBandaiCartParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """P-Bandai 购物车添加"""
        return run_unlocker(
            self._user_token, 'p-bandai.jp', 'pb_cart_add', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def microsoft_create_account(
        self, 
        params: MicrosoftCreateParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Microsoft 创建账户"""
        return run_unlocker(
            self._user_token, 'signup.live.com', 'create_account', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def godaddy_login(
        self, 
        params: GodaddyLoginParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """GoDaddy 登录"""
        return run_unlocker(
            self._user_token, 'sso.godaddy.com', 'login', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

 
    def ultimatedining_login(
        self, 
        params: UltimateDiningLoginParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Ultimate Dining 登录"""
        return run_unlocker(
            self._user_token, 'theultimatediningcard.ca', 'login', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
 
    def ajet_getavailability(
        self, 
        params: AjetAvailabilityParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Ajet 查机票"""
        return run_unlocker(
            self._user_token, 'www.ajet.com', 'getavailability', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def ajet_pnr_login(
        self, 
        params: AjetPnrLoginParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Ajet 查机票"""
        return run_unlocker(
            self._user_token, 'www.ajet.com', 'pnr_login', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def ajet_get_booking_detail(
        self, 
        params: AjetGetBookingDetailParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Ajet 查机票"""
        return run_unlocker(
            self._user_token, 'www.ajet.com', 'get_booking_detail', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
        
    def att_check_availability(
        self, 
        params: AttCheckParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """AT&T 查机票"""
        return run_unlocker(
            self._user_token, 'www.att.com', 'check_availability', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def easyjet_find_booking(
        self, 
        params: EasyjetFindParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """EasyJet 查找预订"""
        return run_unlocker(
            self._user_token, 'www.easyjet.com', 'find_booking', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
        
    def eurowings_openbooking(
        self, 
        params: EurowingsBookingParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Eurowings 打开预订"""
        return run_unlocker(
            self._user_token, 'www.eurowings.com', 'openbooking', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def fastpeoplesearch_search(
        self, 
        params: FastPeopleSearchParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """FastPeopleSearch 搜索"""
        return run_unlocker(
            self._user_token, 'www.fastpeoplesearch.com', 'search_people', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def hilton_get_token(
        self, 
        params: HiltonTokenParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Hilton 获取令牌"""
        return run_unlocker(
            self._user_token, 'www.hilton.com', 'get_web_guest_token', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def hilton_new_customer(
        self, 
        params: HiltonCustomerParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Hilton 新客户"""
        return run_unlocker(
            self._user_token, 'www.hilton.com', 'new_customer', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def koreanair_login(
        self, 
        params: KoreanAirLoginParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Korean Air 登录"""
        return run_unlocker(
            self._user_token, 'www.koreanair.com.cn', 'cn_login', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def maersk_get_token(
        self, 
        params: MaerskTokenParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Maersk 获取令牌"""
        return run_unlocker(
            self._user_token, 'www.maersk.com', 'get_access_token', params.to_api_dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def marriott_login(
        self, 
        params: MarriottLoginParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Marriott 登录"""
        return run_unlocker(
            self._user_token, 'www.marriott.com', 'login', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def marriott_enroll(
        self, 
        params: MarriottEnrollParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Marriott 注册"""
        return run_unlocker(
            self._user_token, 'www.marriott.com', 'enroll', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def pokemon_login(
        self, 
        params: PokemonLoginParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Pokemon Center 登录"""
        return run_unlocker(
            self._user_token, 'www.pokemoncenter-online.com', 'login', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def pokemon_get_lottery_list(
        self, 
        params: PokemonLotteryListParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Pokemon Center 获取抽奖列表"""
        return run_unlocker(
            self._user_token, 'www.pokemoncenter-online.com', 'get_lottery_list', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def pokemon_apply_lottery(
        self, 
        params: PokemonApplyLotteryParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Pokemon Center 申请抽奖"""
        return run_unlocker(
            self._user_token, 'www.pokemoncenter-online.com', 'apply_lottery', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def sephora_checkbalance(
        self, 
        params: SephoraCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Sephora 查卡"""
        return run_unlocker(
            self._user_token, 'www.sephora.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def textnow_login(
        self, 
        params: TextnowLoginParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """TextNow 登录"""
        return run_unlocker(
            self._user_token, 'www.textnow.com', 'login', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def walmart_checkbalance(
        self, 
        params: WalmartCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Walmart 查卡"""
        return run_unlocker(
            self._user_token, 'www.walmart.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def walmart_ca_checkbalance(
        self, 
        params: WalmartCaCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Walmart Canada 查卡"""
        return run_unlocker(
            self._user_token, 'www.walmart.ca', 'ca_checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def walmart_get_wallet(
        self, 
        params: WalmartWalletParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Walmart 获取钱包"""
        return run_unlocker(
            self._user_token, 'www.walmart.com', 'get_wallet_payments', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def wizzair_search_flights(
        self, 
        params: WizzairSearchParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Wizzair 搜索航班"""
        return run_unlocker(
            self._user_token, 'www.wizzair.com', 'search_flights', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    def hm_checkbalance(
        self, 
        params: HmCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """H&M 查卡"""
        return run_unlocker(
            self._user_token, 'www2.hm.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
        

class AsyncUnlocker:
    
    def __init__(
        self, 
        user_token: str, 
        auth: bool = False,
        timeout: int = 60,
        branch: Optional[str] = None,
        internal_host: bool = True,
        developer_id: Optional[str] = None,
        debug: bool = False
    ):
        """
        @param user_token: 账号 token
        @param auth: 是否包月
        @param branch: 分支名
        @param internal_host: 是否国内域名
        @param developer_id: 开发者 id
        @param timeout: 超时时间: 秒
        @param debug: 是否输出结果
        """
        self._user_token = user_token
        self._auth = auth
        self._branch = branch
        self._internal_host = internal_host
        self._developer_id = developer_id
        self._timout = timeout
        self._debug = debug
        
    async def kohls_checkbalance(
        self, 
        params: KohlCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Kohl's 查卡"""
        return await async_run_unlocker(
            self._user_token, 'www.kohls.com', 'checkbalance', params.to_api_dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )

    async def lululemon_checkbalance(
        self, 
        params: LululemonCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Lululemon 查卡"""
        return await async_run_unlocker(
            self._user_token, 'shop.lululemon.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def wbi_servlet(
        self, 
        params: WbiParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Adidas 查卡"""
        return await async_run_unlocker(
            self._user_token, 'wbiprod.storedvalue.com', 'wb_servlet', params.to_api_dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def dicks_checkbalance(
        self, 
        params: DicksCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Dick's Sporting Goods 查卡"""
        return await async_run_unlocker(
            self._user_token, 'www.dickssportinggoods.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def finishline_checkbalance(
        self, 
        params: FinishlineCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Finish Line 查卡"""
        return await async_run_unlocker(
            self._user_token, 'www.finishline.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def footlocker_checkbalance(
        self, 
        params: FootlockerCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Foot Locker 查卡"""
        return await async_run_unlocker(
            self._user_token, 'self._user_token, www.footlocker.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def rei_checkbalance(
        self, 
        params: ReiCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """REI 查卡"""
        return await async_run_unlocker(
            self._user_token, 'www.rei.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def one4all_checkbalance(
        self, 
        params: One4AllCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """One4All 查卡"""
        return await async_run_unlocker(
            self._user_token, 'www.one4all.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def saks_checkbalance(
        self, 
        params: SaksCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Saks Fifth Avenue 查卡"""
        return await async_run_unlocker(
            self._user_token, 'www.saksfifthavenue.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def coach_checkbalance(
        self, 
        params: CoachCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Coach 查卡"""
        return await async_run_unlocker(
            self._user_token, 'www.coach.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def fandango_checkbalance(
        self, 
        params: FandangoCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Fandango 查卡"""
        return await async_run_unlocker(
            self._user_token, 'tickets.fandango.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def columbia_checkbalance(
        self, 
        params: ColumbiaCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Columbia 查卡"""
        return await async_run_unlocker(
            self._user_token, 'www.columbia.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def homedepot_checkbalance(
        self, 
        params: HomeDepotCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Home Depot 查卡"""
        return await async_run_unlocker(
            self._user_token, 'www.homedepot.com', 'recipient_experience_checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def etsy_register(
        self, 
        params: EtsyRegisterParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Etsy 注册"""
        return await async_run_unlocker(
            self._user_token, 'www.etsy.com', 'register', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def prizepicks_login(
        self, 
        params: PrizepicksLoginParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """PrizePicks 登录"""
        return await async_run_unlocker(
            self._user_token, 'app.prizepicks.com', 'login', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def fifa_login(
        self, 
        params: FifaLoginParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """FIFA 登录"""
        return await async_run_unlocker(
            self._user_token, 'auth.fifa.com', 'login', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def auspost_track(
        self, 
        params: AuspostTrackParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Auspost 追踪"""
        return await async_run_unlocker(
            self._user_token, 'auspost.com.au', 'track', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def norse_search_flights(
        self, 
        params: NorseSearchFlightsParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Norse 搜索航班"""
        return await async_run_unlocker(
            self._user_token, 'connections.flynorse.com', 'search_flights', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def scoot_booking_retrieval(
        self, 
        params: ScootBookingParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Scoot 预订检索"""
        return await async_run_unlocker(
            self._user_token, 'manage.flyscoot.com', 'booking_retrieval', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def myprepaid_validate(
        self, 
        params: MyPrepaidValidateParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """MyPrepaid 验证"""
        return await async_run_unlocker(
            self._user_token, 'myprepaidcenter.com', 'validate_virtual_code', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def pbandai_cart_add(
        self, 
        params: PBandaiCartParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """P-Bandai 购物车添加"""
        return await async_run_unlocker(
            self._user_token, 'p-bandai.jp', 'pb_cart_add', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def microsoft_create_account(
        self, 
        params: MicrosoftCreateParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Microsoft 创建账户"""
        return await async_run_unlocker(
            self._user_token, 'signup.live.com', 'create_account', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def godaddy_login(
        self, 
        params: GodaddyLoginParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """GoDaddy 登录"""
        return await async_run_unlocker(
            self._user_token, 'sso.godaddy.com', 'login', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def ultimatedining_login(
        self, 
        params: UltimateDiningLoginParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Ultimate Dining 登录"""
        return await async_run_unlocker(
            self._user_token, 'theultimatediningcard.ca', 'login', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def ajet_getavailability(
        self, 
        params: AjetAvailabilityParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Ajet 查机票"""
        return await async_run_unlocker(
            self._user_token, 'www.ajet.com', 'getavailability', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def att_check_availability(
        self, 
        params: AttCheckParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """AT&T 查机票"""
        return await async_run_unlocker(
            self._user_token, 'www.att.com', 'check_availability', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def easyjet_find_booking(
        self, 
        params: EasyjetFindParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """EasyJet 查找预订"""
        return await async_run_unlocker(
            self._user_token, 'www.easyjet.com', 'find_booking', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def eurowings_openbooking(
        self, 
        params: EurowingsBookingParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Eurowings 打开预订"""
        return await async_run_unlocker(
            self._user_token, 'www.eurowings.com', 'openbooking', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def fastpeoplesearch_search(
        self, 
        params: FastPeopleSearchParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """FastPeopleSearch 搜索"""
        return await async_run_unlocker(
            self._user_token, 'www.fastpeoplesearch.com', 'search_people', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def hilton_get_token(
        self, 
        params: HiltonTokenParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Hilton 获取令牌"""
        return await async_run_unlocker(
            self._user_token, 'www.hilton.com', 'get_web_guest_token', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def hilton_new_customer(
        self, 
        params: HiltonCustomerParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Hilton 新客户"""
        return await async_run_unlocker(
            self._user_token, 'www.hilton.com', 'new_customer', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def koreanair_login(
        self, 
        params: KoreanAirLoginParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Korean Air 登录"""
        return await async_run_unlocker(
            self._user_token, 'www.koreanair.com.cn', 'cn_login', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def maersk_get_token(
        self, 
        params: MaerskTokenParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Maersk 获取令牌"""
        return await async_run_unlocker(
            self._user_token, 'www.maersk.com', 'get_access_token', params.to_api_dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def marriott_login(
        self, 
        params: MarriottLoginParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Marriott 登录"""
        return await async_run_unlocker(
            self._user_token, 'www.marriott.com', 'login', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def marriott_enroll(
        self, 
        params: MarriottEnrollParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Marriott 注册"""
        return await async_run_unlocker(
            self._user_token, 'www.marriott.com', 'enroll', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def pokemon_login(
        self, 
        params: PokemonLoginParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Pokemon Center 登录"""
        return await async_run_unlocker(
            self._user_token, 'www.pokemoncenter-online.com', 'login', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def pokemon_get_lottery_list(
        self, 
        params: PokemonLotteryListParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Pokemon Center 获取抽奖列表"""
        return await async_run_unlocker(
            self._user_token, 'www.pokemoncenter-online.com', 'get_lottery_list', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def pokemon_apply_lottery(
        self, 
        params: PokemonApplyLotteryParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Pokemon Center 申请抽奖"""
        return await async_run_unlocker(
            self._user_token, 'www.pokemoncenter-online.com', 'apply_lottery', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def sephora_checkbalance(
        self, 
        params: SephoraCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Sephora 查卡"""
        return await async_run_unlocker(
            self._user_token, 'www.sephora.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def textnow_login(
        self, 
        params: TextnowLoginParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """TextNow 登录"""
        return await async_run_unlocker(
            self._user_token, 'www.textnow.com', 'login', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def walmart_checkbalance(
        self, 
        params: WalmartCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Walmart 查卡"""
        return await async_run_unlocker(
            self._user_token, 'www.walmart.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def walmart_ca_checkbalance(
        self, 
        params: WalmartCaCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Walmart Canada 查卡"""
        return await async_run_unlocker(
            self._user_token, 'www.walmart.ca', 'ca_checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def walmart_get_wallet(
        self, 
        params: WalmartWalletParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Walmart 获取钱包"""
        return await async_run_unlocker(
            self._user_token, 'www.walmart.com', 'get_wallet_payments', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def wizzair_search_flights(
        self, 
        params: WizzairSearchParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """Wizzair 搜索航班"""
        return await async_run_unlocker(
            self._user_token, 'www.wizzair.com', 'search_flights', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
    
    async def hm_checkbalance(
        self, 
        params: HmCheckBalanceParams, 
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None, 
        mode: Literal["generate", "cache"] = "cache"
    ) -> dict:
        """H&M 查卡"""
        return await async_run_unlocker(
            self._user_token, 'www2.hm.com', 'checkbalance', params.dict(), 
            user_agent=user_agent, proxy=proxy, auth=self._auth, mode=mode, timeout=self._timeout, branch=self._branch, internal_host=self._internal_host, 
            developer_id=self._developer_id, debug=self._debug
        )
