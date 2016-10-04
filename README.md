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
- Play around with adam, our first model. It was trained only with the abstracts and titles of the articles. I should also mention that no preprocessing was done on the input (i.e. no stemming, removing stopwords, and other good ideas).
- Consider some decision processes for the recommender, and possibly implement one.
- Read papers on Word2Vec as implicit matrix factorization.

####Completed:
- Played around with adam.
- Clarified clustering process.

###10/3/2016:
- Begin pushing article content to Postgres.
- Work on clustering document vectors for the first model (adam).

####Completed:
- Began the process of pushing article content to Postgres. This is going to take a very long time. I hope nothing bad happens.



###10/4/2016:
- There were many difficulties today. I underestimated the task of properly parsing latex files. Generally speaking it is a fairly difficult task with high variance in results. More specifically, some files will be stripped bare while others remain extremely noisy. I expect very little of the processed data will be usable (say ~10%).
- Clustering in high dimensions is very slow and difficult (curse of dimensionality). It takes roughly 1 hour to run a 15-cluster KMeans++ on the first model. Assuming the computational complexity scales linearly with clusters, it will take ~13-15 hours to train a 200-cluster KKmeans++ model. This is not necessarily prohibitive, but I think we can run a Spark cluster to reduce this run time significantly.
- And I am writing this on a lab computer because I left my laptop charger at home. Great way to start the day, I know.
####Goals:
- Start a Spark cluster and investigate hierarchical clustering/graph-based community detection.
- Examine the decision process of SciExplorer's recommendation system.
- Monitor the progress of processing the latex files and upload to postgres.
####Completed:
- !
- !
- !



##Updates and Comments
- ~8:40 AM 9/30/2016: The number of XML files is around ~850k currently. The process is still running. Also, it took a non-trivial amount of time to count the number of files in the directory.
- ~12:20 AM 10/1/2016: Currently inserted 10000 rows into Postgres.
- ~9:20 AM 10/1/2016: The row count is now ~590,000
- ~1:00 PM 10/1/2016: Discovered that titles are missing for all entries. Fixing. Note all other columns have been properly populated. Also running a model on 5000 abstracts as a test. This took ~10 secs on a 4 core EC2 instance.
- ~1:10 PM 10/1/2016: Found the bug in xml_parser.py. When getting title using a root from an elementtree i.e. title = root.find('...'). Even though title.text contains the title string, bool(title) returns False. Hence the get\_title function always returns None, causing me grief. Fix: use if title is not None instead.
- ~2:30 PM 10/1/2016: finished a script for fixing the titles. Currently running.
- ~8:00 PM 10/1/2016: Started training first model. Unpacking source files. Completed database population.
- ~1:20 PM 10/3/2016: Unpacking complete. Processing content and putting it on postgres (very slow... will take days to finish. how to make this faster?)
- ~4:30 PM 10/3/2016: Pushing content to postgres is unbearably slow. The estimate is that it will take over 2 weeks to finish (not good...). Running KMeans clustering on abstracts is going very slowly as well. We are looking at days here. Potential solutions: use a strong machine or setup spark cluster.
- 5:30 PM 10/3/2016: Decided to shift the postgres pushing job to a more powerful EC2 instance. Priority starting now should be to launch a spark cluster that can do the clustering job (single machine takes ~1 hour to run 15 kmeans clusters, that means ~15 hours to run 200 kmean clusters. That is stupid.)
- 10:30 AM 10/4/2016: Realized that hierarchical clustering cannot be easily parallelized, hence there is currently not Spark implementation. Proceeding with KMeans for 200 clusters. If I can get the centroids, I can have a more effective way of filtering out papers.

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

~/spark-1.5.0-bin-hadoop1/ec2/spark-ec2 -k large_test -i ~/.ssh/large_test.pem -r us-east-1 -s 6 --copy-aws-credentials --ebs-vol-size=64 launch my_cluster

scp -i ~/.ssh/large_test.pem ~/spark-aws root@ec2-52-87-192-172.compute-1.amazonaws.com/root/.

Links:
http://docs.aws.amazon.com/quickstart/latest/mongodb/architecture.html

http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-using-volumes.html

http://www.aclweb.org/anthology/E14-3011

https://en.support.wordpress.com/markdown-quick-reference/

http://markdownlivepreview.com/
