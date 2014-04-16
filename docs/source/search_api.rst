Search API
==========

路径: /v1.6/search/

HTTP方法: GET

传入参数
---------

=============    ==========  ===============================   =============================================
参数名           是否必填    默认值                            描述                                         
=============    ==========  ===============================   =============================================
q                是                                            用户输入的查询内容                           
page             否          1                                 返回查询结果的页码                           
sort_fields      否          [] (根据搜索结果相关度排序)       根据哪些字段排序。升序：直接填写字段名;降序：在字段名前加"-"。                 
filters          否          []                                根据哪些字段值来过滤结果（具体见下面的示例）
highlight        否          False                             是否在结果中加亮标记匹配的关键词
api_key          是                                            分配给用户站点的api key
=============    ==========  ===============================   =============================================

注：
    1. filters:
        1. "categories"字段只接受0或1个值，不接受多个值。
        2. 实施过程中，需要确定哪些字段用来过滤。测试数据集中，仅price, market_price, categories，item_id和available可用来过滤。
        3. available 默认为[true]，即如果不在filter中指定available，则仅仅返回有售的产品。
    2. sort_fields:
        1. 实施过程中，需要确定哪些字段用来排序。测试数据集中，仅price和market_price可用来排序。

返回结果
---------

==============    ===============================
名称               说明
==============    ===============================
records            搜索到的产品
info               包含和此次结果相关的一系列信息，详见示例。
info["facets"]     info中的facets包含在事先配置好的若干维度上的结果数，详见示例。
errors             错误信息。正常情况下为{}。
==============    ===============================

注：
    1. info["facets"]中，"categories"部分返回的是目前选定分类的子分类（或顶级分类，如果没有分类选定）的结果数。

示例
-----

注：
    1. 请使用相应站点的api_key

请求::

    curl -X GET 'http://search.tuijianbao.net/api/v1.6/search/' \
         -H 'Content-Type: application/json' \
         -d '{
            "api_key": "123456",
            "q": "bb",
            "sort_fields": ["-price", "-market_price"],
            "page": 1,
            "highlight": true,
            "filters": {
                "categories": ["17"],
                "price": {
                    "type": "range",
                    "from": 15.00,
                    "to": 150.00
                }
            }
         }'

说明：
    1. filters: price是根据范围过滤。

结果::

    {
        "records": [{
                "item_id": "FA123355",
                "item_name": "贝亲",
                "categories": [1255, 125588]
                "price": 12.50,
                "image_link": "http://example.com/images/123456.jpg",
                "item_link":  "http://example.com/products/1233/"
            }],
        "info": {
                "current_page": 1,
                "num_pages": 5,
                "per_page": 20,
                "total_result_count": 100,
                "facets": {
                    "categories": [
                        {"label": "饮料", "id": "2255", "count": 15}
                        {"label": "童装", "id": "3721", "count": 8}
                        ]
                }
            },
        "errors": {}
    }

说明：
    1. current_page: 当前结果页页码
    2. num_pages: 搜索结果总页数
    3. per_page: 每页有多少结果
    4. total_result_count: 搜索结果总数
    5. facets: 示例中的facets是显示在搜索结果中，包含哪些不同分类（category），各分类有多少搜索结果。