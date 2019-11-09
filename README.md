# Interdisciplinary Recommendation with Doc2Vec

This project seeks to expand on [sepehr125's project](https://github.com/sepehr125/arxiv-doc2vec-recommender), an arXiv article recommender powered by [Doc2Vec](https://arxiv.org/pdf/1405.4053v2.pdf), implemented by [Gensim](https://radimrehurek.com/gensim/models/doc2vec.html). One of Sepehr's findings is that document vectors in Doc2Vec and their pairwise cosine distance form a weighted graph. Therefore it is possible to build a dense network out of the Doc2Vec document vectors with the documents as nodes and their pairwise cosine distance as edge weights. A key idea of this project is to build this dense graph and extract information that may provide insight into the aforementioned question.


## Data
The article metadata was obtained via [arXiv's OAI-PMH interface](https://arxiv.org/help/oa/index). These files are in xml format and are well-formatted and "clean." More specifically, each element within the files is clearly and consistently labeled. Here is an [example](/examples/oai-arXiv.org-0704.0031.oai_dc.xml) of a metadata file.

The article source files were obtained via [arXiv's s3 bucket](https://arxiv.org/help/bulk_data_s3). According to arXiv, the total size of the source files was ~190 GB around Feb. 2012. However, after unpacking all the files, the total was ~600 GB and numbered just below ~1.2 million articles. Though I had expected the 2012 statistics to be outdated, the difference in size was still somewhat surprising.

Parsing the [source files](/examples/1208.0007) is much trickier than parsing the metadata because the files were laced with LaTeX and postscript. I opted to use [OpenDetex](https://github.com/pkubowicz/opendetex) for this purpose after testing on a small subset of documents, for which it worked reasonably well, extracting most of the article content with occasional mishaps. Beyond that, I also removed lines which contain fewer than 6 words via regex. From many trials and error, I found this process to be effective and simple enough that the process can be completed within the time constraint of this project. However, if there is a place to improve on, it would be parsing the source files.

My final recommendation model does not use the Doc2Vec model trained on the full articles due to time constraints. However, the model is available on a S3 bucket `s3://arxivdoc2vecmodel` for anyone to access. It would be an interesting and natural next step to try to build the recommendation model with this Doc2Vec model.


## Pipeline
The metadata was parsed and placed in a Postgres database first. Then the content of the articles were cleaned with the process mentioned in the previous section and uploaded to the same database. Then the Doc2Vec model is trained using the information from the database, including title, abstract, and content. The trained model contains the low-dimensional vector representation of each document, which is what we called "document vectors." The model that I trained set these document vectors to 100 components each.

## The Model
As mentioned briefly before, because these document vectors reside in the same vector space, it is possible to compare them using some kind of distance metric, typically cosine distance. The original idea of building and analyzing the entire dense graph with cosine distance as the edges was deemed infeasible because such a graph contains hundreds of billions of edges. I attempted to subset the number of edges by eliminating those below a certain threshold of similarity but the computation remains intractable. My next attempt was stratified sampling: taking 10% of the document vectors from each of the 146 subject classified by arXiv. I was able to create this graph but analyzing it with community detection remains difficult due to size.

The final model compares each article to the "centers" of each of the 146 subjects. These centers are calculated taking the average of all of the document vectors in that subject. When two subjects are selected, the model returns the articles which are most similar to both subjects: this similarity is determined by the product of the document vector's cosine similarity to each of the two subjects (the document vector is not considered if its similarity to each subject is negative). I also created an webapp for the recommender:


##Ideas for Further Exploration
Certainly with more resources and computing power, it would be an interesting undertaking to analyze the full network of document vectors, perhaps even including other information such as citation counts, authors, and universities into the graph. The Doc2Vec model itself can also be tuned so that it uses a greater number of dimensions for representing the vectors. Finally, as mentioned in the data section, having a consistent and reliable method of extracting content from latex files can go a long way to increasing the quality of the vector representations.
