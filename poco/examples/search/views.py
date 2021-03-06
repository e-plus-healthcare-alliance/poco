#encoding=utf8

import json
import re
from django.shortcuts import render, render_to_response, redirect
from django.template import RequestContext
from django.http import HttpResponse
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticutils import S, F
from django.core.paginator import Paginator
from common.api_client import APIClient


import jieba
def preprocess_query_str(query_str):
    result = []
    keywords = [keyword for keyword in query_str.split(" ") if keyword.strip() != ""]
    for keyword in keywords:
        cutted_keyword = " ".join(["%s" % term for term in jieba.cut_for_search(keyword)])
        result.append(cutted_keyword)
    return result


# refs: http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/query-dsl-bool-query.html
def construct_query(query_str, for_filter=False):
    splitted_keywords = " ".join(preprocess_query_str(query_str)).split(" ")
    match_phrases = []
    for keyword in splitted_keywords:
        match_phrases.append({"match_phrase": {"item_name_standard_analyzed": keyword}})

    if for_filter:
        query = {
            "bool": {
                "must": match_phrases
            }
        }
    else:
        query = {
            "bool": {
                "must": match_phrases,
                "should": [
                    {'match': {'item_name': {"boost": 2.0, 
                                             'query': splitted_keywords,
                                             'operator': "and"}}}
                ]
            }
        }

    return query

def addFilterToFacets(s, facets):
    filter = s.build_search().get("filter", None)
    if filter:
        facets["facet_filter"] = filter
    return filter

def _getSubCategoriesFacets(cat_id, s):
    if cat_id is None:
        regex = r"null__.*"
    else:
        regex = r"%s__.*" % cat_id
    result = {'terms': {'regex': regex, 'field': 'categories', 'size': 20}}
    #result = {'terms': {'field': 'categories', 'size': 20}}
    addFilterToFacets(s, result)
    return result




def v_index(request):
    query_str = request.GET.get("q", "")
    page_num = request.GET.get("p", "1")
    cat = request.GET.get("cat", None)
    op = request.GET.get("op", None)

    if cat is not None and cat.strip() == "":
        cat = None

    try:
        page_num = int(page_num)
    except TypeError:
        page_num = 1

    if op=="u":
        sort_fields = ["price"]
    elif op=="d":
        sort_fields = ["-price"]
    else:
        sort_fields = []

    if cat:
        category = CATEGORY_MAP_BY_ID.get(cat, None)
    else:
        category = CATEGORY_TREE

    api_client = APIClient(settings.API_PREFIX_FOR_SEARCH_DEMO)
    body = {
       "api_key": settings.API_KEY_FOR_SEARCH_DEMO,
       "q": query_str,
       "page": page_num,
       "sort_fields": sort_fields,
       "facets": {"categories": {"mode": "DIRECT_CHILDREN"}},
       "highlight": True
    }

    if cat is not None:
        body["filters"] = {"categories": [cat]}

    result = api_client("public/search/", None,
               body=body)

    breadcrumbs = get_breadcrumbs(category)
    if result["info"]["current_page"] > 1:
        prev_page = result["info"]["current_page"] - 1
    else:
        prev_page = None

    if result["info"]["current_page"] < result["info"]["num_pages"]:
        next_page = result["info"]["current_page"] + 1
    else:
        next_page = None

    return render_to_response("demo-index.html", 
            {"result": result,
             "prev_page": prev_page, "next_page": next_page,
             "query_str": query_str, "category": category,
             "breadcrumbs": breadcrumbs,
             "settings": settings,
             "op": op}, 
            RequestContext(request))



def get_breadcrumbs(category):
    curr_category = category
    breadcrumbs = []
    while curr_category:
        breadcrumbs.append({"category": curr_category, "active": False})
        if curr_category["id"] is not None:
            curr_category = CATEGORY_MAP_BY_ID[curr_category["parent_id"]]
        else:
            break
    breadcrumbs.reverse()
    if breadcrumbs:
        breadcrumbs[-1]["active"] = True
    return breadcrumbs


def _extractSuggestedTerms(res, name):
    suggested_keywords = res["facets"][name]
    if suggested_keywords["total"] > 0:
        hits_total = res["hits"]["total"]
        half_hits_total = hits_total / 2.0
        # Fillter out terms which does not help to further narrow down results
        terms = [term for term in suggested_keywords["terms"] if term["count"]  < hits_total]
        # Filter out terms which is
        #TODO
        #terms.sort(lambda a,b: cmp(abs(a["count"] - half_hits_total), abs(b["count"] - half_hits_total)))
        return terms
    else:
        return []


def _getMoreSuggestions(query_str):
    splitted_keywords = " ".join(preprocess_query_str(query_str))
    query = construct_query(query_str)
    filter = {"term": {"available": True}}
    facets = {'keywords': {'terms': {'field': 'keywords',
                                      'size': 10},
                           "facet_filter": filter},
              'categories': {'terms': {'regex': r'\d{4}', 'field': 'categories', 'size': 5},
                             "facet_filter": filter}
             }
    es = Elasticsearch()
    res = es.search(index="item-index", 
                    search_type="count",
                    body={"query": query,
                                              "facets": facets,
                                              "filter": filter})
    suggested_categories = _extractSuggestedTerms(res, "categories")
    suggested_categories = suggested_categories[:2]
    return _extractSuggestedTerms(res, "keywords"), suggested_categories


def _tryAutoComplete(es, kw_prefix):
    es = Elasticsearch()
    res = es.suggest(index="item-index", body={"kw": {"text": kw_prefix, "completion": {"field": "keyword_completion"}}})
    options = res["kw"][0]["options"]
    suggested_texts = [option["text"] for option in options]
    return suggested_texts

# TODO: limit g. single letter
def _getQuerySuggestions(es, query_str):
    split_by_wspace = [kw.strip() for kw in query_str.split(" ") if kw.strip()]

    if len(split_by_wspace) > 0:
        kw_prefix = split_by_wspace[-1]
        possible_last_keywords = _tryAutoComplete(es, kw_prefix)
        completed_forms = []
        # TODO: use msearch
        for kw in possible_last_keywords:
            completed_form = (" ".join(split_by_wspace[:-1]) + " " + kw).strip()
            query = construct_query(completed_form, for_filter=True)
            res = es.search(index="item-index",
                                    search_type="count",
                                    body={"query": query,
                                    "filter": {"term": {"available": True}}})
            count = res["hits"]["total"]
            if count > 0:
                completed_forms.append({"type": "completion",
                                        "value": u"%s" % completed_form,
                                        "count": count})

        # also suggest more keywords
        if re.match(r"[a-zA-Z0-9]{1}", kw_prefix) is None: # not suggest for last keyword with only one letter/digit
            suggested_keywords, suggested_categories = _getMoreSuggestions(query_str)

            completed_forms_categories = []
            for suggested_term in suggested_categories:
                category_id = suggested_term["term"]
                category = CATEGORY_MAP_BY_ID.get(category_id, None)
                if category:
                    breadcrumbs = get_breadcrumbs(category)[1:]
                    breadcrumbs_str = " > ".join([cat["category"]["name"] for cat in breadcrumbs])
                    completed_forms_categories.append({"type": "facet", 
                                            "field_name": "categories",
                                            "facet_label": breadcrumbs_str,
                                            "value": query_str,
                                            "category_id": category_id,
                                            "count": suggested_term["count"]
                                            })

            completed_forms = completed_forms_categories + completed_forms

            for suggested_term in suggested_keywords:
                skip = False
                for sk in split_by_wspace:
                    if sk in suggested_term["term"] or suggested_term["term"] in sk:
                        skip = True
                        break
                if skip:
                    continue
                query = query_str + " " + suggested_term["term"]
                completed_forms.append({"type": "more_keyword",
                                        "value": u"%s" % query,
                                        "count": suggested_term["count"]
                                        })
        return completed_forms
    else:
        return []


def v_ajax_auto_complete_term(request):
    query_str = request.GET.get("term", "").strip()
    es = Elasticsearch()
    suggested_texts = _getQuerySuggestions(es, query_str)
    return HttpResponse(json.dumps(suggested_texts))


CATEGORY_TREE = {u'11': {u'1100': {'name': u'\u65b0\u751f\u513f'},
         u'1101': {'name': u'S'},
         u'1102': {'name': u'M'},
         u'1103': {'name': u'L'},
         u'1104': {'name': u'XL'},
         u'1105': {'name': u'XXL'},
         u'1106': {'name': u'\u5e03\u5c3f\u88e4'},
         u'1107': {'name': u'\u62c9\u62c9\u88e4'},
         u'1109': {'name': u'\u9632\u5c3f\u57ab\u5dfe/\u5c3f\u5e03'},
         'name': u'\u5c3f\u88e4'},
 u'12': {u'1200': {'name': u'\u6e7f\u5dfe\\\u7eb8\u5dfe'},
         u'1201': {'name': u'\u5a74\u513f\u62a4\u80a4'},
         u'1202': {'name': u'\u9632\u6652\u9632\u51bb'},
         u'1203': {'name': u'\u62a4\u81c0\u723d\u8eab'},
         u'1204': {'name': u'\u8eab\u4f53\u6e05\u6d01'},
         u'1205': {'name': u'\u6d17\u62a4\u793c\u76d2'},
         u'1206': {'name': u'\u5988\u5988\u7279\u6b8a\u62a4\u7406'},
         u'1207': {'name': u'\u6210\u4eba\u62a4\u80a4\u6e05\u6d01'},
         u'1208': {'name': u'\u6210\u4eba\u7eb8\u5dfe'},
         'name': u'\u6d17\u62a4'},
 u'13': {u'1300': {'name': u'\u6d17\u8863\u6e05\u6d01'},
         u'1302': {'name': u'\u6d17\u6fa1\u7528\u5177'},
         u'1303': {'name': u'\u5c45\u5ba4\u6d88\u6bd2/\u51c0\u5316'},
         u'1304': {'name': u'\u5b89\u5168\u9632\u62a4'},
         u'1305': {'name': u'\u964d\u6e29\u7528\u54c1'},
         u'1306': {'name': u'\u5582\u836f\u5668'},
         u'1308': {'name': u'\u5bb6\u5ead\u836f\u7bb1'},
         u'1309': {'name': u'\u62a4\u7406\u7528\u54c1'},
         u'1310': {'name': u'\u5982\u5395\u7528\u54c1'},
         u'1311': {'name': u'\u8ba1\u91cf\u5668\u5177'},
         u'1312': {'name': u'\u5bb6\u7528\u5c0f\u7535\u5668'},
         u'1313': {'name': u'\u5bb6\u5c45\u6742\u54c1'},
         u'1315': {'name': u'\u6d74\u5ba4\u7528\u54c1'},
         u'1317': {'name': u'\u7c89\u6251/\u76d2'},
         u'1318': {'name': u'\u5b89\u5168\u522b\u9488'},
         'name': u'\u5c45\u5bb6\u65e5\u7528'},
 u'14': {u'1400': {'name': u'\u5976\u74f6'},
         u'1401': {'name': u'\u5976\u5634'},
         u'1402': {'name': u'\u7259\u80f6'},
         u'1403': {'name': u'\u9910\u5177'},
         u'1404': {'name': u'\u5582\u54fa\u6e05\u6d01'},
         u'1405': {'name': u'\u52a0\u70ed\u6d88\u6bd2'},
         u'1406': {'name': u'\u5916\u51fa/\u5b58\u50a8\u7528\u5177'},
         u'1407': {'name': u'\u6c34\u676f/\u58f6'},
         'name': u'\u5582\u517b'},
 u'15': {u'1500': {'name': u'\u4f1e\u63a8\u8f66'},
         u'1501': {'name': u'\u5b66\u6b65\u8f66/\u5e26'},
         u'1502': {'name': u'\u626d\u626d\u8f66'},
         u'1503': {'name': u'\u6ed1\u677f\u8f66'},
         u'1504': {'name': u'\u4e09\u8f6e\u8f66'},
         u'1505': {'name': u'\u7535\u52a8\u8f66'},
         u'1506': {'name': u'\u81ea\u884c\u8f66'},
         u'1507': {'name': u'\u5a74\u7ae5\u5e8a'},
         u'1508': {'name': u'\u9910\u6905'},
         u'1509': {'name': u'\u6447\u6905'},
         u'1510': {'name': u'\u6c7d\u8f66\u5ea7\u6905'},
         'name': u'\u8f66\u5e8a\u6905'},
 u'16': {u'1600': {'name': u'\u7761\u6795'},
         u'1601': {'name': u'\u7761/\u62b1\u888b'},
         u'1602': {'name': u'\u88ab\u8925'},
         u'1603': {'name': u'\u5e8a\u56f4/\u9970\u54c1'},
         u'1604': {'name': u'\u5957\u88c5/\u793c\u76d2'},
         u'1605': {'name': u'\u51c9\u5e2d/\u868a\u5e10'},
         u'1608': {'name': u'\u9762\u5dfe/\u6d74\u5dfe'},
         u'1609': {'name': u'\u5176\u4ed6'},
         'name': u'\u5bdd\u5177'},
 u'17': {u'1700': {'name': u'\xd3\xa4\xd7\xb0'},
         u'1701': {'name': u'\u7ae5\u88c5'},
         u'1702': {'name': u'\u7ae5\u978b'},
         u'1703': {'name': u'\u7ae5\u889c '},
         u'1704': {'name': u'\u7ae5\u5e3d/\u56f4\u5dfe/\u624b\u5957\u53ca\u670d\u9970\u914d\u4ef6'},
         'name': u'\u7ae5\u88c5'},
 u'18': {u'1800': {'name': u'\xb7\xc0\xb7\xf8\xc9\xe4'},
         u'1801': {'name': u'\u5b55\u5987\u88c5'},
         u'1802': {'name': u'\u5b55\u5185\u8863'},
         u'1803': {'name': u'\u5b55\u671f\u62a4\u80a4'},
         u'1805': {'name': u'\u5b55\u4ea7\u671f\u8425\u517b'},
         u'1806': {'name': u'\u4ea7\u540e\u5851\u8eab\u5185\u8863'},
         u'1807': {'name': u'\u4ea7\u540e\u5851\u8eab\u53bb\u7eb9'},
         u'1808': {'name': u'\u5582\u54fa\u7528\u54c1'},
         u'1809': {'name': u'\u54fa\u4e73\u670d\u88c5'},
         u'1810': {'name': u'\u536b\u751f\u5dfe'},
         u'1811': {'name': u'\u4ea7\u57ab/\u5f85\u4ea7\u5305'},
         u'1812': {'name': u'\u5988\u54aa\u5305'},
         u'1813': {'name': u'\u80cc\u5e26'},
         u'1814': {'name': None},
         'name': u'\u5988\u5988\u7528\u54c1'},
 u'19': {u'1900': {'name': u'\u679c\u6c41/\u6c34'},
         u'1901': {'name': u'\u6ce5\u7cca\u7c7b'},
         u'1902': {'name': u'\u51b2\u8c03\u7c7b'},
         u'1903': {'name': u'\u7c73\u7c89/\u83dc\u7c89'},
         u'1904': {'name': u'\u8425\u517b\u9762'},
         u'1905': {'name': u'\u8089\u677e'},
         u'1906': {'name': u'\u957f\u7259\u671f\u98df\u54c1'},
         u'1907': {'name': u'\u513f\u7ae5\u7cd6\u679c'},
         u'1908': {'name': u'\u8c03\u5473\u54c1'},
         u'1909': {'name': u'\u5e72\u679c'},
         'name': u'\u8f85\u98df'},
 u'20': {u'2000': {'name': u'1\u6bb5'},
         u'2001': {'name': u'2\u6bb5'},
         u'2002': {'name': u'3\u6bb5'},
         u'2003': {'name': u'4\u6bb5'},
         u'2004': {'name': u'\u7279\u6b8a\u914d\u65b9\u5976\u7c89'},
         u'2005': {'name': u'\u7f8a\u5976\u7c89'},
         u'2006': {'name': u'\u5b55\u5987\u5976\u7c89'},
         'name': u'\u5976\u7c89'},
 u'21': {u'2100': {'name': u'\u6302\u56fe\u8ba4\u77e5\u5361\u7247'},
         u'2101': {'name': u'\u7acb\u4f53\u89e6\u6478\u4e66'},
         u'2102': {'name': u'\u513f\u6b4c\u7ae5\u8c23\u6545\u4e8b'},
         u'2103': {'name': u'\u62fc\u56fe'},
         u'2104': {'name': u'\u7236\u6bcd\u5fc5\u8bfb'},
         u'2105': {'name': u'CD'},
         u'2106': {'name': u'DVD/VCD'},
         u'2107': {'name': u'\u5988\u5988\u4e13\u7528'},
         u'2108': {'name': u'\u76f8\u6846\u76f8\u518c'},
         u'2109': {'name': u'\u624b\u8db3\u5370'},
         u'2111': {'name': u'\u753b\u7b14'},
         u'2112': {'name': u'\u5199\u5b57\u677f'},
         u'2113': {'name': None},
         'name': u'\u56fe\u4e66\u97f3\u50cf\u7eaa\u5ff5\u54c1 '},
 u'22': {u'2200': {'name': u'\u7537\u5b69\u73a9\u5177'},
         u'2201': {'name': u'\u5973\u5b69\u73a9\u5177'},
         u'2202': {'name': u'\u7259\u80f6\u6447\u94c3'},
         u'2203': {'name': u'\u6bdb\u7ed2\u73a9\u5177'},
         u'2204': {'name': u'\u5e03\u827a\u73a9\u5177'},
         u'2205': {'name': u'\u6e38\u620f\u57ab'},
         u'2206': {'name': u'DIY\u521b\u610f'},
         u'2207': {'name': u'\u62fc\u63d2\u73a9\u5177'},
         u'2208': {'name': u'\u80a2\u4f53\u534f\u8c03'},
         u'2209': {'name': u'\u4e50\u97f3\u73a9\u5177'},
         u'2210': {'name': u'\u667a\u529b\u5f00\u53d1'},
         u'2211': {'name': u'\u7535\u5b50\u73a9\u6559\u5177'},
         u'2212': {'name': u'\u6c99\u6ee9\u73a9\u5177'},
         u'2213': {'name': u'\u620f\u6c34\u73a9\u5177'},
         u'2215': {'name': u'\u5927\u578b\u73a9\u5177'},
         u'2218': {'name': u'\u7403\u7c7b'},
         'name': u'\u73a9\u5177'},
 u'24': {u'2400': {'name': u'DHA\u5065\u8111'},
         u'2401': {'name': u'\u8865\u9499/\u94c1/\u950c\u7852'},
         u'2402': {'name': u'\u7ef4\u751f\u7d20'},
         u'2403': {'name': u'\u521d\u4e73'},
         u'2404': {'name': u'\u6e05\u706b/\u5f00\u80c3'},
         u'2405': {'name': u'\u76ca\u751f\u83cc'},
         u'2406': {'name': u'\u8425\u517b\u7d20'},
         u'2407': {'name': u'\u7eff\u8272\u98df\u7528\u6cb9'},
         'name': u'\u8425\u517b'}}

CATEGORY_TREE["name"] = u"全部资源"

CATEGORY_MAP_BY_ID = {}
def fill_category_to_name(parent_id, id, dict):
    CATEGORY_MAP_BY_ID[id] = dict
    CATEGORY_MAP_BY_ID[id]["parent_id"] = parent_id
    CATEGORY_MAP_BY_ID[id]["id"] = id
    CATEGORY_MAP_BY_ID[id]["children"] = []
    for key in dict.keys():
        if key not in ("name", "parent_id", "id", "children"):
            fill_category_to_name(id, key, dict[key])
            CATEGORY_MAP_BY_ID[id]["children"].append(dict[key])
fill_category_to_name(None, None, CATEGORY_TREE)
