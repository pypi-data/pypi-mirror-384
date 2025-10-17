# -- coding: utf-8 --
# Project: fiuaiapp
# Created Date: 2025 05 Tu
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

# const
AI_ALLOWED_DOCTYPE_META = [
    "Contract", 
    "Contract Item", 
    "Bank Transaction",
    "Bank Statement",
    # "invoice"
    ]
USED_COUNTRY_LIST =  ["China", "United States", "Japan", "Thailand", "India", "Indonesia", "Malaysia", "Philippines", "Singapore", "South Korea", "United Kingdom", "Vietnam"]
USED_LANGUAGE_LIST = ["zh", "en", "ja", "th", "id", "ms", "ph", "sg", "kr", "uk", "vn"]
from .type import (
    UOM, 
    Currency, 
    Country,
    Language,
    DocTypeMeta,
    DocField,
    DocFieldType,
    
)
from typing import List
from logging import getLogger

from .client import FiuaiSDK

from .util import get_int_value

logger = getLogger(__name__)



def load_uom_data(client: FiuaiSDK)-> List[UOM]:
    """
    从frappe获取uom数据
    """
    uom_list_response = client.internal_get_list(doctype="UOM", fields=["name", "uom_name", "common_code"])
    if not uom_list_response.is_success():
        return []
    
    uom_list = uom_list_response.data
    if not uom_list:
        return []
    
    return [UOM(name=uom["name"], uom_name=uom["uom_name"], common_code=uom["common_code"]) for uom in uom_list]

def load_currency_data(client: FiuaiSDK)-> List[Currency]:
    """
    从frappe获取currency数据
    """
    currency_list_response = client.internal_get_list(
        doctype="Currency", 
        filters={"enabled": 1},
        fields=["name", "currency_name", "fraction_units", "smallest_currency_fraction_value"]
        )
    if not currency_list_response.is_success():
        return []
    
    currency_list = currency_list_response.data
    if not currency_list:
        return []
    
    return [Currency(name=currency["name"], currency_name=currency["currency_name"], fraction_units=currency["fraction_units"], smallest_currency_fraction_value=currency["smallest_currency_fraction_value"]) for currency in currency_list]

def load_country_data(client: FiuaiSDK)-> List[Country]:
    """
    从frappe获取country数据
    """
    country_list_response = client.internal_get_list(
        doctype="Country", 
        filters={"name": ["in", USED_COUNTRY_LIST]},
        fields=["name", "code"]
    )
    if not country_list_response.is_success():
        return []
    
    country_list = country_list_response.data
    if not country_list:
        return []
    
    return [Country(name=country["name"], code=country["code"]) for country in country_list]

def load_language_data(client: FiuaiSDK)-> List[Language]:
    """
    从frappe获取language数据
    """
    language_list_response = client.internal_get_list(
        doctype="Language", 
        filters={"name": ["in", USED_LANGUAGE_LIST]},
        fields=["name", "language_name"]
    )
    if not language_list_response.is_success():
        return []
    
    language_list = language_list_response.data
    if not language_list:
        return []
    
    return [Language(name=language["name"], language_name=language["language_name"]) for language in language_list]

def load_doctype_meta(client: FiuaiSDK, doctype: str, max_api_retry: int = 3, only_has_prompt: bool = True, show_hidden: bool = False)-> DocTypeMeta:
    """
    从frappe获取doctype数据
    """

    retry_count = 0
    doc_meta = None
    while retry_count < max_api_retry:
            
        doc_meta = _get_meta(client, doctype, only_has_prompt, show_hidden)
        
        if doc_meta:
            break
        else:
            retry_count += 1
           
    return doc_meta        

def _get_meta(client: FiuaiSDK, doctype: str, only_has_prompt: bool = True, show_hidden: bool = False) -> DocTypeMeta | None:
    try:
        m_response = client.get_meta(doctype)
        if not m_response.is_success():
            return None
        
        m = m_response.data
        if not m:
            return None
        
        if m is None:
            return None

        _fields = []
        links = []
        child_docs = []
        for _f in m["fields"]:
            field_name = _f["fieldname"]
            field_type = _f["fieldtype"]
            field_prompt = _f.get("field_prompt", None)
            options_str = _f.get("options", None)
            hidden = get_int_value("hidden", _f)
            reqd = get_int_value("reqd", _f)
            mandatory = get_int_value("mandatory", _f)
            read_only = get_int_value("read_only", _f)
            in_list_view = get_int_value("in_list_view", _f)
            in_mobile_view = get_int_value("in_mobile_view", _f)
            description = _f.get("description", "")
            custom_query = _f.get("custom_query", None)
            link_filters = _f.get("link_filters", None)
            precision = get_int_value("precision", _f)
            length = get_int_value("length", _f)


            ### 格式转化

            
            options = []

            match field_type:
                case "Select":
                    if not options_str:
                        # raise ValueError(f"empty option str for select field {field_name}")
                        # TODO: 解决异常
                        options = []
                    else:
                        options = options_str.split("\n")
                case "Link":
                    links.append(options_str)
                    options.append(options_str)
                case "Table":
                    child_docs.append(options_str)
                    options.append(options_str) 
                case _:
                    pass


            if field_prompt == "" and only_has_prompt:
                # 仅有prompt的field才是应该关心的字段，降低复杂度
                continue
            if hidden == 1 and not show_hidden:
                continue
            
            
            # 将字符串类型的 field_type 转换为 DocFieldType 枚举
            try:
                fieldtype_enum = DocFieldType(field_type)
            except ValueError:
                # 如果找不到对应的枚举值，使用 Data 作为默认值
                fieldtype_enum = DocFieldType.Data
            
            _fields.append(DocField(
                fieldname=field_name, 
                description=description,
                fieldtype=fieldtype_enum, 
                hidden=True if hidden == 1 else False,
                read_only=True if read_only == 1 else False,
                reqd=True if reqd == 1 else False,
                options=options,
                field_prompt=field_prompt,
                mandatory=True if mandatory == 1 else False,
                in_list_view=True if in_list_view == 1 else False,
                in_mobile_view=True if in_mobile_view == 1 else False,
                custom_query=custom_query,
                link_filters=link_filters,
                precision=precision,
                length=length,
                # ai_recognition_value=AiRecognitionValue(value=None, confidence=0, ai_comment="")
            ))
        
        # links, child 去重
        links = list(set(links))
        child_docs = list(set(child_docs))

        doc_meta = DocTypeMeta(
                name=doctype, 
                doctype_prompts=m.get("doctype_prompts", ""), 
                fields=_fields,
                link_docs=links,
                child_docs=child_docs
            )
        return doc_meta
    except Exception as e:
        logger.error(f"load doctype {doctype} meta failed: {e}")
        return None
        
        
def load_all_allowed_doctype_meta(client: FiuaiSDK, only_has_prompt: bool = True, show_hidden: bool = False)-> List[DocTypeMeta]:
    """
    从frappe获取doctype数据
    """
    r = []
    for _d in AI_ALLOWED_DOCTYPE_META:
        m = load_doctype_meta(client, _d, only_has_prompt, show_hidden)
        if not m:
            continue
        r.append(m)
    return r
