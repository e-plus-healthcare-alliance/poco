import json
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError


#items_path = "/Users/jacobfan/projects/ElasticSearchDemo/data/201312/items.json"


def load_items(items_path):
    f = open(items_path, "r")
    for line in f.readlines():
        item = json.loads(line)
        yield item
    f.close()


# TODO: handling elasticsearch.exceptions.ConnectionError
# TODO: check elasticsearch array search problem
def run(items_path):
    count = 0
    print "Begin Loading ..."
    items = load_items(items_path)
    es = Elasticsearch()
    try:
        es.indices.delete("item-index")
    except NotFoundError:
        pass
    # TODO: use bulk
    for item in items:
        count += 1
        if (count % 50) == 0:
            print count
        #item["item_name_suggest"] = item["item_name"]
        del item["_id"]
        item["categories"] = " ".join(item["categories"])
        res = es.index(index='item-index', doc_type='item', id=item["item_id"], body=item)
        #print item
    es.indices.refresh(index='item-index')
    print "Finish Loading"
