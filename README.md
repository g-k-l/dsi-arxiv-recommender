# DSI Final Project

##Timeline
* 10/3 Monday: Data, Github Ready
* 10/5 Wednesday: Basic Model Done
* 10/7 Friday: Analysis Done
* 10/10 Monday: Presentation Done
* Sometime in between: lecture on presentation
* 10/14 Friday: Code Freeze
* 10/17 Monday: Practice Presentation with Group
* 10/18 Tuesday: More Practice (with half of class)
* 10/19 Wednesday: Practice with next cohort as audience
* 10/20 (TBD) Thursday: Capstone Presentations
* 10/21 Friday: Day off
* 10/24-10/28: Interview prep. Course review. Graduation.

###Tips
* The data-modeling-analysis-presentation loop should be completed ASAP.
* No live demo allowed on presentation.
* Always do what you set out to do for the day.

## Progress Log
###9/28/2016:
- Made the decision to try to run Doc2Vec on arXiv corpus (~190 GB of text)
- Setup conda environment and AWS EC2 for mining arXiv metadata
- Worked on script (harvest.py) to take the metadata from arXiv OAI.
- Decided that harvest.py should contain processing before moving the data to S3.

###9/29/2016:
####Goals: 
  - DATABASE. PROPOSAL.
  - Parse metadata XML into JSON. Store in DB on AWS. (PRIORITY)
  - Find out whether it would be possible to match the raw text with the metadata via file name and perm. link.
  - Ultimately: Combine the raw text and metadata within a single DB entry

####Completed:
  - Submitted Final Project Proposal
  - XML getter is running on aws_remote. It will take about 6 hours to grab ~1.1 million files.
  - Started a PSQL database. Now we just need to populate it.

###9/30/2016:
####Goals:
- Final Assessment!
- Parse metadata XML and store into PSQL.
- Write a script to process the source files

####Completed:
- Completed the script to parse and insert data into Postgres.
- Currently inserting rows into Postgres (one at a time since I couldn't get multithreading to work)

###10/1/2016:
####Goals:
- Begin collecting the arXiv source files
- Write a script that unpacks and organizes the arXiv source files
- Write a script that streams data from Postgres for Doc2Ve
- Do a Doc2Vec test run with a subset of the metadata (~100000) (Possibly impossible)
####Completed:
- Finished populating database, with the exception of a few pieces of missing data
- Obtained all of the source files. Currently unpacking.
- Started the training process for the prototype model. The model is trained on abstracts only.

###10/2/2016:
####Goals:

####Completed:


##Updates and Comments
- ~8:40 AM 9/30/2016: The number of XML files is around ~850k currently. The process is still running. Also, it took a non-trivial amount of time to count the number of files in the directory.
- ~12:20 AM 10/1/2016: Currently inserted 10000 rows into Postgres.
- ~9:20 AM 10/1/2016: The row count is now ~590,000
- ~1:00 PM 10/1/2016: Discovered that titles are missing for all entries. Fixing. Note all other columns have been properly populated. Also running a model on 5000 abstracts as a test. This took ~10 secs on a 4 core EC2 instance.
- ~1:10 PM 10/1/2016: Found the bug in xml_parser.py. When getting title using a root from an elementtree i.e. title = root.find('...'). Even though title.text contains the title string, bool(title) returns False. Hence the get\_title function always returns None, causing me grief. Fix: use if title is not None instead.
- ~2:30 PM 10/1/2016: finished a script for fixing the titles. Currently running.
- ~8:00 PM 10/1/2016: Started training first model. Unpacking source files. Completed database population.

##Misc. Notes
- arXiv changed its identifier scheme on March 2007. See https://arxiv.org/help/arxiv_identifier
- Since SciExplorer is built on post-2007 papers, its parser only handles the new scheme.
- Therefore we will need to write a parser for the old scheme.
- Turns out it is not necessary to write a new parser.
- http://s3tools.org/usage
- It is possible to populate a DB much more quickly than inserting one row at a time https://www.postgresql.org/docs/current/static/populate.html but so far I can't seem to get it to work.

AWS PostgreSQL DB:
psql --host=arxivpsql.cctwpem6z3bt.us-east-1.rds.amazonaws.com --port=5432 --username=root --password --dbname=arxivpsql

ALTER USER "user_name" WITH PASSWORD 'new_password';

Put files into folder batches:
find . -maxdepth 1 -type f |head -1000|xargs cp -t $destdir

Links:
http://docs.aws.amazon.com/quickstart/latest/mongodb/architecture.html

http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-using-volumes.html

http://www.aclweb.org/anthology/E14-3011

https://en.support.wordpress.com/markdown-quick-reference/

http://markdownlivepreview.com/
