from common.mongo_client import getMongoClient
from common.site_manage_utils import create_site


def run(site_id, site_name):
    answer = raw_input("Do you want to create the site: '%s' with site_name '%s'?(enter 'yes' to continue)" % (site_id, site_name))
    if answer == "yes":
        mongo_client = getMongoClient()
        site_record = create_site(mongo_client, site_id, site_name, 3600 * 24)
        print "Site %s created. " % site_id
        print "api_key=%s" % site_record["api_key"]
        print "site_token=%s" % site_record["site_token"]
    else:
        print "Exit without action."
