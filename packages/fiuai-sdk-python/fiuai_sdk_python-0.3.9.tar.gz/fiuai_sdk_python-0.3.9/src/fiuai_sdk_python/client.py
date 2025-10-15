import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import json
from urllib.parse import quote
from typing import Any, Literal

from .util import get_client_config, is_initialized
from .error import FiuaiGeneralError, FiuaiAuthError
from logging import getLogger
from .type import UserProfile
from .profile import UserProfileInfo
from .auth import AuthHeader
from .resp import parse_response, ApiResponse


logger = getLogger(__name__)

class NotUploadableException(FiuaiGeneralError):
	def __init__(self, doctype):
		self.message = "The doctype `{1}` is not uploadable, so you can't download the template".format(doctype)
    



class FiuaiSDK(object):
    def __init__(self, 
        username: str, 
        url: str,
        auth_tenant_id: str,
        current_company: str,
        impersonation: str=None,
        # auth_type: Literal["internal", "password"]="password",
        max_api_retry: int=3,
        timeout: int=5,
        verify: bool=False
    ):
        self.username = username
    
        self.headers = None
        self.verify = verify
        self.url = url
        self.max_api_retry = max_api_retry

        self.client = httpx.Client(
            verify=self.verify,
            timeout=timeout,
            follow_redirects=True,
            proxy=None
        )

        # match self.auth_type:
        #     case "internal":
        #         self.headers
        #     case "password":
        #         if username == "" or password == "":
        #             raise FiuaiGeneralError("Username and password are required")
                
        #         self.headers["Fiuai-Internal-Auth"] = "false"
        #         self._login(username, password)
        #     case _:
        #         raise FiuaiGeneralError(f"Invalid auth type: {self.auth_type}")
        self.headers = AuthHeader(
            x_fiuai_user=username, 
            x_fiuai_auth_tenant_id=auth_tenant_id, 
            x_fiuai_current_company=current_company, 
            x_fiuai_impersonation=impersonation or "",
            )

        
    # def _login(self, username: str, password: str):
    #     r = self.client.post(self.url, data={
	# 		'cmd': 'login',
	# 		'usr': username,
	# 		'pwd': password
	# 	}, headers=self.headers)

    #     if r.json().get('message') == "Logged In":
    #         self.can_download = []
    #         logger.info(f"Login to {self.url} success")

    #         ### 获取cookie
    #         self.headers["Fiuai-Internal-Company"] = r.cookies.get("current_company")
    #         self.headers["Fiuai-Internal-Tenant"] = r.cookies.get("tenant")
    #         return r.json()
    #     else:
    #         raise FiuaiAuthError(f"Login failed: {r.json().get('message')}")
    
    # def _logout(self):
    #     logger.info(f"Logout from {self.url}")
    #     if self.auth_type == "password":
    #         # internal login 不需要logout
    #         self.client.get(self.url, params={"cmd": "logout"}, headers=self.headers)


    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        # self._logout()
        self.client.close()
        # self.logout()

   
    def get_avaliable_company(self, page: int=1, page_size: int=20) -> ApiResponse:
        r = self.client.get(self.url + "/api/method/fiuai.network.doctype.company.company.get_available_companies", params={"page": page, "page_size": page_size})
        
        return self.post_process(r)
    
    def swith_company(self, tenant: str = "", company: str = "") -> ApiResponse:

        self.headers.x_fiuai_auth_tenant_id = tenant
        self.headers.x_fiuai_current_company = company

        if company == "":
            raise FiuaiAuthError("Company is required when using password auth")

        if tenant == "":
            raise FiuaiAuthError("Tenant is required when using internal auth")
            
        # else:
        #     r = self.client.post(self.url + "/api/method/frappe.sessions.change_current_company",
		# 	data={"auth_company_id": company})
        #     if r.status_code != 200:
        #         logger.error(f"Switch company failed: {r.json().get('message')}")
        #         # raise FiuaiAuthError(f"Switch company failed: {r.json().get('message')}")
        #         return False
        #     else:
        #         return True
    
    def get_tenant(self) -> ApiResponse:
        return self.headers.x_fiuai_auth_tenant_id
    
    def get_company(self) -> ApiResponse:
        return self.headers.x_fiuai_current_company
            
    # def get_v2_api(self, uri, params={}):
        
    #     print(f"22222, ", self.headers.model_dump())
    #     res = self.client.get(self.url + '/api/v2/' + uri.lstrip('/'), params=params, headers=self.headers.model_dump())
    #     return self.post_process(res)


    def get_user_profile_info(self, user_id: str=None) -> ApiResponse:
        """获取详细的用户信息"""
        if not user_id:
            user_id = self.headers.x_fiuai_user

        res = self.client.get(self.url + f"/api/v2/internal/user/profile/{user_id}", headers=self.headers.model_dump(by_alias=True))

        profile_response = self.post_process(res)

        if profile_response.is_success():
            try:
                profile_response.data = UserProfileInfo.model_validate(profile_response.data)
            except Exception as e:
                profile_response.error = str(e)
                profile_response.error_code = "PROFILE_FORMAT_ERROR"
                return profile_response
            return profile_response
        else:
            return profile_response


   
    def internal_post_req(self, uri, postdata={}) -> ApiResponse:
        res = self.client.post(self.url + '/api/v2/internal/' + uri.lstrip('/'), data=postdata, headers=self.headers.model_dump(by_alias=True))
        return self.post_process(res)

    def internal_get_req(self, uri, params={}) -> ApiResponse:
        res = self.client.get(self.url + '/api/v2/internal/' + uri.lstrip('/'), params=params, headers=self.headers.model_dump(by_alias=True))
        return self.post_process(res)
    
    def internal_create(self, data={}) -> ApiResponse:
        res = self.client.post(self.url + '/api/v2/internal/doctype/create', data={"data":json.dumps(data, ensure_ascii=False)}, headers=self.headers.model_dump(by_alias=True))
        return self.post_process(res)

    def internal_get(self, doctype, name, fields=None, filters=None) -> ApiResponse:
        d = {
            "doctype": doctype,
            "name": name,
        }
        if fields:
            d["fields"] = json.dumps(fields)
        if filters:
            d["filters"] = json.dumps(filters)
        res = self.client.get(self.url + '/api/v2/internal/doctype/get', params=d, headers=self.headers.model_dump(by_alias=True))
        return self.post_process(res)

    def internal_get_list(self, doctype, filters=None, fields=None, limit_start=0, limit_page_length=20, order_by=None) -> ApiResponse:
        d = {
                    "doctype": doctype, 
                    "limit_start":limit_start,
                    "limit_page_length":limit_page_length,
                }
        if filters:
            d["filters"] = json.dumps(filters)
        if fields:
            d["fields"] = json.dumps(fields)
        if order_by:
            d["order_by"] = order_by
        res = self.client.get(
            self.url + '/api/v2/internal/doctype/get_list', 
            params=d, 
            headers=self.headers.model_dump(by_alias=True))
        return self.post_process(res)

    
    def internal_update(self, data={}) -> ApiResponse:
        res = self.client.post(self.url + '/api/v2/internal/doctype/update', data={"data":json.dumps(data, ensure_ascii=False)}, headers=self.headers.model_dump(by_alias=True))
        return self.post_process(res)

    def internal_delete(self, doctype, name) -> ApiResponse:
        res = self.client.post(self.url + '/api/v2/internal/doctype/delete', data={"doctype": doctype, "name":name}, headers=self.headers.model_dump(by_alias=True))
        return self.post_process(res)

    def internal_submit(self, doctype, name) -> ApiResponse:
        res = self.client.post(self.url + '/api/v2/internal/doctype/submit', data={"doctype": doctype, "name":name}, headers=self.headers.model_dump(by_alias=True))
        return self.post_process(res)
    
    def internal_cancel(self, doctype, name) -> ApiResponse:
        res = self.client.post(self.url + '/api/v2/internal/doctype/cancel', data={"doctype": doctype, "name":name}, headers=self.headers.model_dump(by_alias=True))
        return self.post_process(res)


    def get_meta(self, doctype: str) -> ApiResponse:
        res = self.client.get(self.url + '/api/v2/internal/doctype/meta/' + doctype, headers=self.headers.model_dump(by_alias=True))
      
        return self.post_process(res)
    

    def post_process(self, response) -> ApiResponse:
        """
        处理API响应，使用结构化的错误处理系统
        
        Args:
            response: httpx响应对象
            
        Returns:
            Any: 成功时返回数据，失败时抛出异常
            
        Raises:
            FiuaiGeneralError: 当API返回错误时
            FiuaiAuthError: 当认证相关错误时
        """
        # 使用resp.py中的统一解析函数
        api_response = parse_response(response)
        
        return api_response


def get_client(username: str, auth_tenant_id: str, current_company: str, impersonation: str=None)-> FiuaiSDK:
    """
    获取FiuaiSDK客户端, 需要提取调用init_fiuai()初始化
    使用方式有两种:
    1. 使用密码认证, 需要在调用的的时候传入username和password
    2. 使用内部认证, 需要在初始化的时候传入tokens, 调用时传入username
    """
    # 检查是否已初始化
    if not is_initialized():
        raise ValueError("FiuaiSDK not initialized. Please call init_fiuai() first.")
    
    client_config = get_client_config()
    

    return FiuaiSDK(
        url=client_config.url,
        username=username,
        auth_tenant_id=auth_tenant_id,
        current_company=current_company,
        impersonation=impersonation,
        max_api_retry=client_config.max_api_retry,
        timeout=client_config.timeout,
        verify=client_config.verify,
    )
