#Community Detection with arXiv Document Vectors







##Pipeline

This project seeks to expand on [sepehr125's project](https://github.com/sepehr125/arxiv-doc2vec-recommender), an arXiv article recommender powered by [Doc2Vec](https://arxiv.org/pdf/1405.4053v2.pdf), implemented by [Gensim](https://radimrehurek.com/gensim/models/doc2vec.html). One of Sepehr's findings is that document vectors in Doc2Vec and their pairwise cosine distance form a weighted graph. Therefore it is possible to build a dense network out of the Doc2Vec document vectors with the documents as nodes and their pairwise cosine distance as edge weights. The ultimate goal of my project is to build this dense graph and extract information that may provide insight into the aforementioned question.


##Data
The article metadata was obtained via [arXiv's OAI-PMH interface](https://arxiv.org/help/oa/index). These files are in xml format and are well-formatted and "clean." More specifically, each element within the files is clearly and consistently labeled. Here is an [example](/examples/oai-arXiv.org-0704.0031.oai_dc.xml) of a metadata file.

The article source files were obtained via [arXiv's s3 bucket](https://arxiv.org/help/bulk_data_s3). According to arXiv, the total size of the source files was ~190 GB around Feb. 2012. However, after unpacking all the files, the total was ~600 GB and numbered just below ~1.2 million articles. Though I had expected the 2012 statistics to be outdated, the difference in size was still somewhat surprising.

Parsing the [source files](/examples/1208.0007) is much trickier than parsing the metadata because the files were laced with LaTeX and postscript. I opted to use [OpenDetex](https://github.com/pkubowicz/opendetex) for this purpose after testing on a small subset of documents, for which it worked reasonably well, extracting most of the article content with occasional mishaps. Beyond that, I also removed lines which contain fewer than 6 words via regex. From many trials and error, I found this process to be effective and simple enough that the process can be completed within the time constraint of this project. However, if there is a place to improve on, it would be parsing the source files.

My final recommendation model does not use the Doc2Vec model trained on the full articles due to time constraints. However, the model is available on a S3 bucket `s3://arxivdoc2vecmodel` for anyone to access. It would be an interesting and natural next step to try to build the recommendation model with this Doc2Vec model.


###Tools

###Models

Doc2Vec model trained with full content: `s3://arxivdoc2vecmodel`.

##Future Work
- Talk about Spark, RowMatrix, GraphX, and Scala
- Talk about different strategies for parsing the
- asdf

###

###
