#encoding=utf8
import copy


CATEGORIES = {
    "12": {"name": "分类12", "parent_id": "null"},
        "1201": {"name": "分类12-01", "parent_id": "12"},
            "120101": {"name": "分类12-01-01", "parent_id": "1201"},
            "120102": {"name": "分类12-01-02", "parent_id": "1201"},
        "1202": {"name": "分类12-02", "parent_id": "12"},
    "15": {"name": "分类15", "parent_id": "null"},
        "1501": {"name": "分类15-01", "parent_id": "15"}
    }
for id, category in CATEGORIES.items():
    category["type"] = "category"
    category["id"] = id

BRANDS = {
    "22": {
        "name": "雀巢"
    },
    "23": {
        "name": "能恩"
    },
    "24": {
        "name": "智多星"
    }
}
for id, brand in BRANDS.items():
    brand["type"] = "brand"
    brand["id"] = id
    brand['brand_logo'] = 'http://logo.com/%s' % id


ITEMS = []
ITEMS.append({
            "type": "product",
            "available": True,
            "item_id": "I123",
            "item_name": "雀巢奶粉",
            "item_spec": "itemspec1",
            "item_link": "http://example.com/I123/",
            "brand": "22",
            "item_level": 5,
            "item_comment_num": 15,
            "origin_place": 0,
            "categories": ["12", "1202"],
            "tags": ["老人"],
            "description": "描述A 描述B",
            "sku": "SKU10052",
            "stock": 10,
            "factory": "雀巢工厂",
            "dosage": "针剂",
            "prescription_type": 3,
            'item_sub_title': '奶粉副标题',
            'channel': '1269e'
            })
ITEMS += [{
            "type": "product",
            "item_id": "I124",
            "item_name": "能恩超级",
            "item_link": "http://example.com/I124/",
            "brand": "23",
            "item_level": 3,
            "item_comment_num": 10,
            "origin_place": 1,
            "categories": ["12", "1201", "120101"],
            "tags": ["小孩", "妇女"],
            "stock": 10,
            "factory": "能恩工厂",
            "sell_num": 3,
            "dosage": "粉剂",
            'item_sub_title': '能恩副标题',
            "prescription_type": 3,
            "channel": '1269a'
            },
            {
            "type": "product",
            "item_id": "I125",
            "item_name": "能恩奶粉",
            "item_link": "http://example.com/I125/",
            "brand": "23",
            "item_level": 3,
            "item_comment_num": 10,
            "origin_place": 0,
            "categories":["12", "1201", "120102"],
            "tags": ["老人", "小孩"],
            "stock": 10,
            "factory": "能恩工厂",
            "sell_num": 10,
            "dosage": "片剂",
            'item_sub_title': '能恩副标题',
            "prescription_type": 5,
            "channel": '1269e'
            },
            {
            "type": "product",
            "item_id": "I126",
            "item_name": "智多星童话故事365",
            "item_link": "http://example.com/I126/",
            "brand": "24",
            "item_level": 3,
            "item_comment_num": 10,
            "origin_place": 0,
            "categories":["15", "1501"],
            "tags": ["小孩"],
            "stock": 10,
            "factory": "智多星工厂",
            "sell_num": 4,
            "dosage": "针剂",
            'item_sub_title': '智多星标题',
            "prescription_type": 6,
            "channel": '1269e'
            }
            ]

def getItems(item_ids=None):
    result = []
    for item in ITEMS:
        if item_ids is None or item["item_id"] in item_ids:
            copied_item = copy.deepcopy(item)
            copied_item["categories"] = [CATEGORIES[category_id] for category_id in copied_item["categories"]]
            copied_item["brand"] = BRANDS[copied_item["brand"]]
            result.append(copied_item)
    return result
