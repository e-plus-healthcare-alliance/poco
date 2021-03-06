Keywords API
=======================

路径: /v1.6/private/keywords/

HTTP方法: POST

功能：
    用来设置置顶关键词列表

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


传入参数
---------


传入参数为一个JSON结构，包括api_key和商品信息字段。目前可传如下字段：

=================  ==========  ===============================   =============================================
参数名             是否必填    默认值                            描述                                         
=================  ==========  ===============================   =============================================
type               是                                            目前仅支持类型："hot"，即更新首页搜索框关键词                    
action             是                                            目前仅支持类型："stick"
category_id        否                                            商品分类ID
keywords           是                                            关键词列表，例如：["关键词1", "关键词2"]
=================  ==========  ===============================   =============================================


返回结果
---------

==============    ===============================
名称               说明
==============    ===============================
code              0 - 操作正确完成；1 - 参数有误; 99 - 未知服务器错误。
err_msg           code非0时，错误信息
==============    ===============================


