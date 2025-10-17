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
from .context import get_current_headers
from typing import Dict, Any, Optional


logger = getLogger(__name__)

class NotUploadableException(FiuaiGeneralError):
	def __init__(self, doctype):
		self.message = "The doctype `{1}` is not uploadable, so you can't download the template".format(doctype)
    



class FiuaiSDK(object):
    def __init__(self, 
        url: str,
        username: str = None,
        auth_tenant_id: str = None,
        current_company: str = None,
        company_unique_no: str = None,
        # auth_type: Literal["internal", "password"]="password",
        max_api_retry: int=3,
        timeout: int=5,
        verify: bool=False
    ):
        self.username = username
        self.auth_tenant_id = auth_tenant_id
        self.current_company = current_company
        self.company_unique_no = company_unique_no
        self.verify = verify
        self.url = url
        self.max_api_retry = max_api_retry

        self.client = httpx.Client(
            verify=self.verify,
            timeout=timeout,
            follow_redirects=True,
            proxy=None
        )

        # 默认的 AuthHeader，优先使用传入的参数，否则从上下文获取
        self.headers = AuthHeader(
            x_fiuai_user=username or "", 
            x_fiuai_auth_tenant_id=auth_tenant_id or "", 
            x_fiuai_current_company=current_company or "", 
            x_fiuai_impersonation="",
            x_fiuai_unique_no=company_unique_no or current_company or "",  # 优先使用 company_unique_no
            x_fiuai_trace_id="",
            )
        
        # 临时 headers 存储，用于 set_temp_header 方法
        self._temp_headers = {}

    def _get_merged_headers(self, extra_headers: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        获取合并后的请求头，自动注入 AuthData 中除了 sid 以外的所有字段
        
        Args:
            extra_headers: 额外的请求头，会覆盖默认值
            
        Returns:
            Dict[str, str]: 合并后的请求头字典
        """
        # 获取当前上下文的 headers
        context_headers = get_current_headers()
        
        # 从上下文构建 AuthData 相关的 headers
        auth_headers = {}
        if context_headers:
            # 映射 AuthData 字段到 HTTP headers，优先使用初始化参数
            current_company_value = self.current_company or context_headers.get("x-fiuai-current-company", self.headers.x_fiuai_current_company)
            company_unique_no_value = self.company_unique_no or context_headers.get("x-fiuai-unique-no", self.headers.x_fiuai_unique_no)
            # 如果 company_unique_no 没有值，使用 current_company 的值
            if not company_unique_no_value:
                company_unique_no_value = current_company_value
                
            auth_headers.update({
                "x-fiuai-user": self.username or context_headers.get("x-fiuai-user", self.headers.x_fiuai_user),
                "x-fiuai-auth-tenant-id": self.auth_tenant_id or context_headers.get("x-fiuai-auth-tenant-id", self.headers.x_fiuai_auth_tenant_id),
                "x-fiuai-current-company": current_company_value,
                "x-fiuai-impersonation": context_headers.get("x-fiuai-impersonation", self.headers.x_fiuai_impersonation),
                "x-fiuai-unique-no": company_unique_no_value,
                "x-fiuai-trace-id": context_headers.get("x-fiuai-trace-id", self.headers.x_fiuai_trace_id),
                "x-fiuai-client": context_headers.get("x-fiuai-client", self.headers.x_fiuai_client),
                "x-fiuai-lang": context_headers.get("x-fiuai-lang", self.headers.x_fiuai_lang),
                "accept-language": context_headers.get("accept-language", self.headers.accept_language),
            })
        else:
            # 如果没有上下文，使用初始化参数或默认的 headers
            current_company_value = self.current_company or self.headers.x_fiuai_current_company
            company_unique_no_value = self.company_unique_no or self.headers.x_fiuai_unique_no
            # 如果 company_unique_no 没有值，使用 current_company 的值
            if not company_unique_no_value:
                company_unique_no_value = current_company_value
                
            auth_headers = {
                "x-fiuai-user": self.username or self.headers.x_fiuai_user,
                "x-fiuai-auth-tenant-id": self.auth_tenant_id or self.headers.x_fiuai_auth_tenant_id,
                "x-fiuai-current-company": current_company_value,
                "x-fiuai-impersonation": self.headers.x_fiuai_impersonation,
                "x-fiuai-unique-no": company_unique_no_value,
                "x-fiuai-trace-id": self.headers.x_fiuai_trace_id,
                "x-fiuai-client": self.headers.x_fiuai_client,
                "x-fiuai-lang": self.headers.x_fiuai_lang,
                "accept-language": self.headers.accept_language,
            }
        
        # 应用临时 headers（优先级高于上下文，低于 extra_headers）
        if self._temp_headers:
            auth_headers.update(self._temp_headers)
        
        # 合并 extra_headers（优先级最高）
        if extra_headers:
            auth_headers.update(extra_headers)
        
        return auth_headers

    def set_temp_header(self, 
                       auth_tenant_id: Optional[str] = None,
                       auth_company_id: Optional[str] = None, 
                       user_id: Optional[str] = None,
                       company_unique_no: Optional[str] = None) -> None:
        """
        设置临时请求头，这些值会在本地请求中替换对应的header，但不覆盖context中的值
        
        Args:
            auth_tenant_id: 临时租户ID
            auth_company_id: 临时公司ID（会自动设置 company_unique_no = auth_company_id）
            user_id: 临时用户ID
            company_unique_no: 临时公司唯一编号
        """
        if auth_tenant_id is not None:
            self._temp_headers["x-fiuai-auth-tenant-id"] = auth_tenant_id
        
        if auth_company_id is not None:
            self._temp_headers["x-fiuai-current-company"] = auth_company_id
            # 实现 company_unique_no = auth_company_id
            self._temp_headers["x-fiuai-unique-no"] = auth_company_id
        
        if user_id is not None:
            self._temp_headers["x-fiuai-user"] = user_id
        
        if company_unique_no is not None:
            if auth_company_id:
                self._temp_headers["x-fiuai-unique-no"] = auth_company_id
            else:
                self._temp_headers["x-fiuai-unique-no"] = company_unique_no

    def clear_temp_headers(self) -> None:
        """清除所有临时请求头"""
        self._temp_headers.clear()

        
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

   
    def get_avaliable_company(self, page: int=1, page_size: int=20, extra_headers: Optional[Dict[str, Any]] = None) -> ApiResponse:
        headers = self._get_merged_headers(extra_headers)
        r = self.client.get(self.url + "/api/method/fiuai.network.doctype.company.company.get_available_companies", 
                           params={"page": page, "page_size": page_size}, 
                           headers=headers)
        
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


    def get_user_profile_info(self, user_id: str=None, extra_headers: Optional[Dict[str, Any]] = None) -> ApiResponse:
        """获取详细的用户信息"""
        if not user_id:
            user_id = self.headers.x_fiuai_user

        headers = self._get_merged_headers(extra_headers)
        res = self.client.get(self.url + f"/api/v2/internal/user/profile/{user_id}", headers=headers)

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


   
    def internal_post_req(self, uri, postdata={}, extra_headers: Optional[Dict[str, Any]] = None) -> ApiResponse:
        headers = self._get_merged_headers(extra_headers)
        res = self.client.post(self.url + '/api/v2/internal/' + uri.lstrip('/'), data=postdata, headers=headers)
        return self.post_process(res)

    def internal_get_req(self, uri, params={}, extra_headers: Optional[Dict[str, Any]] = None) -> ApiResponse:
        headers = self._get_merged_headers(extra_headers)
        res = self.client.get(self.url + '/api/v2/internal/' + uri.lstrip('/'), params=params, headers=headers)
        return self.post_process(res)
    
    def internal_create(self, data={}, extra_headers: Optional[Dict[str, Any]] = None) -> ApiResponse:
        headers = self._get_merged_headers(extra_headers)
        res = self.client.post(self.url + '/api/v2/internal/doctype/create', data={"data":json.dumps(data, ensure_ascii=False)}, headers=headers)
        return self.post_process(res)

    def internal_get(self, doctype, name, fields=None, filters=None, extra_headers: Optional[Dict[str, Any]] = None) -> ApiResponse:
        d = {
            "doctype": doctype,
            "name": name,
        }
        if fields:
            d["fields"] = json.dumps(fields)
        if filters:
            d["filters"] = json.dumps(filters)
        headers = self._get_merged_headers(extra_headers)
        res = self.client.get(self.url + '/api/v2/internal/doctype/get', params=d, headers=headers)
        return self.post_process(res)

    def internal_get_list(self, doctype, filters=None, fields=None, limit_start=0, limit_page_length=20, order_by=None, 
                         extra_headers: Optional[Dict[str, Any]] = None) -> ApiResponse:
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
        headers = self._get_merged_headers(extra_headers)
        res = self.client.get(
            self.url + '/api/v2/internal/doctype/get_list', 
            params=d, 
            headers=headers)
        return self.post_process(res)

    
    def internal_update(self, data={}, extra_headers: Optional[Dict[str, Any]] = None) -> ApiResponse:
        headers = self._get_merged_headers(extra_headers)
        res = self.client.post(self.url + '/api/v2/internal/doctype/update', data={"data":json.dumps(data, ensure_ascii=False)}, headers=headers)
        return self.post_process(res)

    def internal_delete(self, doctype, name, extra_headers: Optional[Dict[str, Any]] = None) -> ApiResponse:
        headers = self._get_merged_headers(extra_headers)
        res = self.client.post(self.url + '/api/v2/internal/doctype/delete', data={"doctype": doctype, "name":name}, headers=headers)
        return self.post_process(res)

    def internal_submit(self, doctype, name, extra_headers: Optional[Dict[str, Any]] = None) -> ApiResponse:
        headers = self._get_merged_headers(extra_headers)
        res = self.client.post(self.url + '/api/v2/internal/doctype/submit', data={"doctype": doctype, "name":name}, headers=headers)
        return self.post_process(res)
    
    def internal_cancel(self, doctype, name, extra_headers: Optional[Dict[str, Any]] = None) -> ApiResponse:
        headers = self._get_merged_headers(extra_headers)
        res = self.client.post(self.url + '/api/v2/internal/doctype/cancel', data={"doctype": doctype, "name":name}, headers=headers)
        return self.post_process(res)


    def get_meta(self, doctype: str, extra_headers: Optional[Dict[str, Any]] = None) -> ApiResponse:
        headers = self._get_merged_headers(extra_headers)
        res = self.client.get(self.url + '/api/v2/internal/doctype/meta/' + doctype, headers=headers)
      
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


def get_client(username: str = None, auth_tenant_id: str = None, current_company: str = None, company_unique_no: str = None) -> FiuaiSDK:
    """
    获取FiuaiSDK客户端, 需要提取调用init_fiuai()初始化
    
    Args:
        username: 用户名（如果提供，优先使用此值而不是上下文）
        auth_tenant_id: 租户ID（如果提供，优先使用此值而不是上下文）
        current_company: 当前公司（如果提供，优先使用此值而不是上下文）
        company_unique_no: 公司唯一编号（如果提供，优先使用此值而不是上下文）
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
        company_unique_no=company_unique_no,
        max_api_retry=client_config.max_api_retry,
        timeout=client_config.timeout,
        verify=client_config.verify,
    )
