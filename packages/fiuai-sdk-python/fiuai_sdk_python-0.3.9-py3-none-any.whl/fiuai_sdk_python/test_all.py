# -- coding: utf-8 --
# Project: fiuai_sdk_python
# Created Date: 2025 10 Th
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI


from fiuai_sdk_python import get_client, init_fiuai
from rich import print


def pre():
    init_fiuai(
        url="https://fiuai.local",
        max_api_retry=3,
        timeout=5,
        verify=False,
    )


pre()

def test_normal_client():
    """测试正常客户端功能"""
    client = get_client(
        # username="assistant@fiuai.com",
        username="fiuai_1@test.com",
        auth_tenant_id="8888888888888888888",
        current_company="911101087890100001",
    )
    
    assert client is not None
    assert client.get_tenant() == "8888888888888888888"
    assert client.get_company() == "911101087890100001"

    profile = client.get_user_profile_info() 
    # print("\n=== 用户档案信息 ===")
    # print(profile)
    # print("==================\n")
    assert profile is not None


    all = client.internal_get_list(
        doctype="Contract",
        limit_page_length=20,
        fields=["name", "contract_no", "grand_total"],
        filters=[["contract_no", "=", "FXT20250520"]]
    )
    print(all)

    # assert len(all) == 2


    # name = all[0]["name"]
    
    # c = client.internal_get(
    #     doctype="Contract",
    #     name=name
    # )


    # c["contract_no"] = "taest112"
    # new = client.internal_create(c)



if __name__ == "__main__":
    """直接运行测试"""
    print("开始运行测试...")
    test_normal_client()
    print("测试完成！")
    