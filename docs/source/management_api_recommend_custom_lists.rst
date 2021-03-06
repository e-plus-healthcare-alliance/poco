Recommender Custom Lists API
============================

路径: /v1.6/private/recommender/custom_lists

HTTP方法: POST

功能：
    用来添加、更新人工订制推荐列表；支持列出所有人工推荐类型供后台集成。

    这里添加的列表，可以以推荐API中"CustomList"类型的形式推荐给用户。

Authentication
---------------
Items API为非公开api，需要authentication之后才能使用。

认证包括api_key和api_token两个部分。
    1. api_key为公开部分，需要在所有api中作为参数传入；
    2. api_token仅在通过内网调用private api时作为header传入。
    3. api_key和api_token必须相符合才能调用private api。

认证方法：添加Http Header "Authorization" ::

    例如site_token为3693cbdc-358c-41e1-a81e-8279d5b28847，则该Header内容为
    "Token 3693cbdc-358c-41e1-a81e-8279d5b28847"


Recommender Custom Lists
-------------------------

通用传入参数
^^^^^^^^^^^^^^


=============    ==========  ===============================   =============================================
参数名           是否必填    默认值                            描述                                         
=============    ==========  ===============================   =============================================
action           是                                            操作类型；根据操作类型不同，需要的其他入参也会不同
api_key          是                                            分配给用户站点的api key
=============    ==========  ===============================   =============================================

操作类型
^^^^^^^^^^^^^^

目前支持如下的操作类型：

1. set_recommender_items 

说明：设置 "人工订制推荐列表"

=============    ==========  ===============================   =============================================
参数名           是否必填    默认值                            描述                                         
=============    ==========  ===============================   =============================================
item_ids         是                                            推荐 商品ID 列表
type             是                                            人工订制推荐类型
display_name     是                                            人工订制推荐类型的名称，一般用于后台集成时提供一个有意义的中文名字供显示用
=============    ==========  ===============================   =============================================


返回结果


==============    ===============================
名称               说明
==============    ===============================
code              0 - 操作正确完成；1 - 参数有误; 99 - 未知服务器错误。
err_msg           code非0时，错误信息
==============    ===============================

2. get_recommender_items

说明：读取 "人工订制推荐列表"

=============    ==========  ===============================   =============================================
参数名           是否必填    默认值                            描述                                         
=============    ==========  ===============================   =============================================
type             是                                            人工订制推荐类型
=============    ==========  ===============================   =============================================


返回结果


==============    ===============================
名称               说明
==============    ===============================
code              0 - 操作正确完成；1 - 参数有误; 99 - 未知服务器错误。
err_msg           code非0时，错误信息
data              人工订制推荐详细信息
==============    ===============================

结果示例::

    {
        "code": 0,
        "data": {
            "display_name": "人工推荐1",
            "item_ids": [
                "I120",
                "I121",
                "I122",
                "I123",
                "I124"
            ],
            "type": "com-type"
        },
        "err_msg": ""
    }


3. list_recommender_types

说明：列出全部 "人工订制推荐列表"

=============    ==========  ===============================   =============================================
参数名           是否必填    默认值                            描述                                         
=============    ==========  ===============================   =============================================
type             是                                            人工订制推荐类型
=============    ==========  ===============================   =============================================


返回结果


==============    ===============================
名称               说明
==============    ===============================
code              0 - 操作正确完成；1 - 参数有误; 99 - 未知服务器错误。
err_msg           code非0时，错误信息
data              人工订制推荐列表
==============    ===============================

结果示例::

    {
        "code": 0,
        "data": [
            {
                "display_name": "人工推荐1",
                "type": "com-type"
            }
        ],
        "err_msg": 0
    }

