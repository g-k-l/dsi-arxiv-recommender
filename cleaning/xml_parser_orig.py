# -*- coding: utf-8 -*-
import psycopg2
import os
from xml.etree import ElementTree as ET
from datetime import datetime
import argparse

"""
The Open Archives Initiative (OAI) is the provider
of metadata scraped by our harvester in XML format.
The XML files are here parsed for relevant fields,
and inserted into a database.
Example use of this script:
    $ python xml_to_postgres.py path/to/xml_dir arxiv_db
would parse files in xml_dir for the following fields:
- title
- authors
- subject
- abstract
- last_submitted
- arxiv_id
and insert into a PostgreSQL database.
Note: The database must already exist!
See harvest.py for more information on how XML files were retrieved.
Below is a sample XML file.
<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.openarchives.org/OAI/2.0/" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
 <dc:title>Dimensionality and dynamics in the behavior of C. elegans</dc:title>
 <dc:creator>Stephens, Greg J</dc:creator>
 <dc:creator>Johnson-Kerner, Bethany</dc:creator>
 <dc:creator>Bialek, William</dc:creator>
 <dc:creator>Ryu, William S</dc:creator>
 <dc:subject>Quantitative Biology - Other Quantitative Biology</dc:subject>
 <dc:description>  A major challenge in analyzing animal behavior is to discover some underlying
simplicity in complex motor actions. Here we show that the space of shapes
adopted by the nematode C. elegans is surprisingly low dimensional, with just
four dimensions accounting for 95% of the shape variance, and we partially
reconstruct "equations of motion" for the dynamics in this space. These
dynamics have multiple attractors, and we find that the worm visits these in a
rapid and almost completely deterministic response to weak thermal stimuli.
Stimulus-dependent correlations among the different modes suggest that one can
generate more reliable behaviors by synchronizing stimuli to the state of the
worm in shape space. We confirm this prediction, effectively "steering" the
worm in real time.
</dc:description>
 <dc:description>Comment: 9 pages, 6 figures, minor corrections</dc:description>
 <dc:date>2007-05-11</dc:date>
 <dc:date>2007-05-16</dc:date>
 <dc:type>text</dc:type>
 <dc:identifier>http://arxiv.org/abs/0705.1548</dc:identifier>
 <dc:identifier>PLoS Comput Biol 4(4): e1000028 (2008)</dc:identifier>
 <dc:identifier>doi:10.1371/journal.pcbi.1000028</dc:identifier>
 </oai_dc:dc>
"""


def get_fields(file_path):
    """This calls helper functions below to
    gather fields from XML file into a tuple.
    This tuple is used as input to
    PostgreSQL INSERT command later.
    Prevents error being raised
    by exiting early if file is not XML.
    Args:
        file_path (str): Path to XML file

    Returns:
        tuple: (title, authors, subject,
                abstract, last_submitted, arxiv_id)
        bool: False if file is not xml
    """

    if not file_path.endswith('.xml'):
        return False

    tree = ET.parse(file_path)
    root = tree.getroot()

    title = get_title(root)
    authors = get_authors(root)
    subject = get_subject(root)
    abstract = get_abstract(root)
    last_submitted = get_date(root)
    arxiv_id = get_arxivid(root)

    return (title, authors, subject, abstract, last_submitted, arxiv_id)


def get_title(root):
    """
    Args:
        root (Element): ElementTree root element

    Returns:
        str: title
        None: if no match is found
    Note: calling .text on a nonexisting match raises error,
    so we use a check to skip
    """
    tag = '{http://purl.org/dc/elements/1.1/}title'
    title = root.find(tag)
    if type(title) == ET.Element:
        return title.text


def get_authors(root, sep='|'):
    """
    Args:
        root (Element): ElementTree root element
        sep (str): character to separate authors

    Returns:
        str: authors ('creator' field in XML),
            separated by given separator
        None: if no match is found
    """
    tag = '{http://purl.org/dc/elements/1.1/}creator'
    authors = root.findall(tag)
    if authors:
        # TODO: switch this with a postgres array object...
        authors = sep.join([el.text for el in authors])
        return authors


def get_subject(root):
    """
    Args:
        root (Element): ElementTree root element

    Returns:
        str: The first subject tag
        None: if no match is found
    Note: calling .text on a nonexisting match raises error,
    so we use an if statement to skip
    """
    tag = '{http://purl.org/dc/elements/1.1/}subject'
    subject = root.find(tag)
    if type(subject) == ET.Element:
        return subject.text


def get_abstract(root):
    """
    There are two elements with the `description` tag name.
    The longer one is the abstract.
    Args:
        root (Element): ElementTree root element

    Returns:
        str: The longer field named "description"
        bool: False if file is not xml
    """
    tag = '{http://purl.org/dc/elements/1.1/}description'
    descriptions = root.findall(tag)
    if descriptions:
        abstract = max([el.text for el in descriptions], key=len)
        return abstract


def get_arxivid(root):
    """
    The arxiv id is hidden among several fields all
    with the tag name "identifier".
    Fortunately, the arxiv id is the full URL at arxiv.org
    for the abstract, so we can identify them checking
    if they contain 'arxiv.org'
    Args:
        root (Element): ElementTree root element

    Returns:
        str: URL of abstract on arxiv.org
        None: if no identifier looking like an arxiv URL exists
    """
    tag = '{http://purl.org/dc/elements/1.1/}identifier'
    ids = root.findall(tag)
    if ids:
        for el in ids:
            if el.text.startswith('http://arxiv.org/abs/'):
                return el.text


def get_date(root):
    """
    Submission dates are all recorded as strings
    We parse them as datetime, and return the latest one.
    Args:
        root (Element): ElementTree root element

    Returns:
        datetime: last submitted date in Y-m-d format
        None: if no match is found
    """

    tag = '{http://purl.org/dc/elements/1.1/}date'
    date_list = root.findall(tag)
    if date_list:
        dates = [datetime.strptime(el.text, "%Y-%m-%d").date() for el in date_list]
        return (max(dates))


def chunker(seq, size):
    """
    Split up a list into chunks.
    This is good for processing files in batches
    """
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


if __name__ == '__main__':
    """This script requires an existing database and a folder
    of XML files to parse.
    It will create a table if none exists, and parse all files
    to insert into the database.
    If the file has already been inserted, it will skip without
    an error, but there is a performance cost when such
    exceptions are caught, so it is recommended to either drop
    existing tables and re-insert fresh from the files, or
    place new files in a separate directory from those already
    inserted.
    """

    parser = argparse.ArgumentParser(description=
        'Parses xml files for fields and inserts into database')
    parser.add_argument('data_dir', help="Path to data folder holding XML files from OAI")
    parser.add_argument('dbname', help="Name of **existing** postgres database.")
    args = parser.parse_args()

    filenames = os.listdir(args.data_dir)
    with psycopg2.connect(dbname=args.dbname) as conn:
        with conn.cursor() as cur:

            sql_create = """CREATE TABLE IF NOT EXISTS articles (
                        index serial PRIMARY KEY,
                        title text,
                        authors text,
                        subject text,
                        abstract text,
                        last_submitted date,
                        arxiv_id text UNIQUE
                    )"""
            cur.execute(sql_create)
            conn.commit()

            """
            Prepare to insert rows in batches
            Using batches helps speed tremendously (~100x)
            """
            batch_size = 1000
            batch_num = 1
            # there's some way of using unnest here
            # that's probably faster
            query_template = """
                INSERT INTO articles
                (title, authors, subject, abstract, last_submitted, arxiv_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
            print("Processing %d files in batches of %d..."%(len(filenames), batch_size))
            for batch in chunker(filenames, batch_size):
                skips = 0
                for fname in batch:
                    file_path = os.path.join(args.data_dir, fname)
                    values = get_fields(file_path)
                    try:
                        cur.execute(query_template, values)
                    except psycopg2.IntegrityError:
                        # record already exists
                        skips += 1
                        conn.rollback()
                        continue
                """Done with batch.
                Commit batch to disk to free memory"""
                conn.commit()

                print("batch %d, skipped %d"%(batch_num, skips))
                batch_num += 1
