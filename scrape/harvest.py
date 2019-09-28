# -*- coding: utf-8 -*-
'''
Harvest metadata of arXiv papers by incremental date range.

The protocol for arXiv's metadata registry is defined by the
Open Archives Initiative (OAI):

https://www.openarchives.org/OAI/2.0/openarchivesprotocol.htm#FlowControl

Docs: http://arxiv.org/help/oa/index
Requires: https://pypi.python.org/pypi/oaiharvest
'''

from datetime import date, datetime, timedelta
from io import BytesIO
import os
import subprocess
import sys

from lxml import etree, objectify
import urllib3

if sys.version_info.major < 3:
    raise RuntimeError("Python 3 Required")


BASE_URL = "http://export.arxiv.org/oai2"


def get_start_date():
    http = urllib3.PoolManager()
    res = http.request("GET", BASE_URL, fields={"verb": "Identify"})
    parser = etree.XMLParser(ns_clean=True)
    root = etree.parse(BytesIO(res.data), parser).getroot()
    find_path = objectify.ObjectPath("OAI-PMH.Identify.earliestDatestamp")
    return datetime.strptime(find_path(root).text, "%Y-%m-%d").date()


def get_end_date():
    return date.today()


def get_dir_path(start_date, end_date):
    metadata_path = os.path.join(os.getcwd(), "metadata")
    if not os.path.isdir(metadata_path):
        os.mkdir(metadata_path)
    dir_path = os.path.join(metadata_path, "%s_%s" % (start_date, end_date))
    return dir_path


def main(start_date=None):
    if start_date is None:
        start_date = get_start_date()
    end_date = get_end_date()
    delta = timedelta(days=30)

    current_date = start_date
    while current_date < end_date:
        dir_path = get_dir_path(current_date, current_date + delta)

        from_, until = current_date, current_date + delta
        if from_ > end_date and until > end_date:
            break
        dir_name = "%s_%s" % (from_, until)

        print("**********Processing batch: %s************" % (dir_name))
        try:
            subprocess.run(["oai-harvest", "--from", str(from_),
                            "--until", str(until), "-d", dir_path,
                            BASE_URL], check=True)
            subprocess.run(["tar", "cvfz", dir_path + ".tgz",
                            "-C", "metadata", dir_name])
            subprocess.run(["rm", "-r", dir_path])
        except subprocess.CalledProcessError as ex:
            with open("./error.log", "w") as f:
                f.write("failed during batch %s" % (dir_name))
            raise ex
        else:
            current_date += delta


if __name__ == "__main__":
    if len(sys.argv) > 1:
        start_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
        main(start_date)
    else:
        main(None)

# args move_to_s3 = "aws s3 mv ../tmp s3://arxivmetadata --recursive"
# os.system(move_to_s3)
