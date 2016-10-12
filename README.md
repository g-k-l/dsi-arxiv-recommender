#Community Detection with arXiv Document Vectors







##Pipeline

This project seeks to expand on [sepehr125's project](https://github.com/sepehr125/arxiv-doc2vec-recommender), an arXiv article recommender powered by [Doc2Vec](https://arxiv.org/pdf/1405.4053v2.pdf). One of Sepehr's findings is that document vectors and their cosine distance form a weighted graph. Therefore it is possible to build a dense network out of the Doc2Vec document vectors with each document as nodes and their pairwise cosine distance as edge weights. The ultimate goal of my project is to build this dense graph and extract information that may provide insight into the aforementioned question. 



####Data
The article metadata was obtained via [arXiv's OAI-PMH interface](https://arxiv.org/help/oa/index). These files are in xml format and are well-formatted and "clean." More specifically, each element within the files is clearly and consistently labeled. The following is an example of a metadata file.

```
<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:dc="http://purl.org/d    c/elements/1.1/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.openarch    ives.org/OAI/2.0/" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.ope    narchives.org/OAI/2.0/oai_dc.xsd"> 
<dc:title>Photoionization of the fullerene ion C60+</dc:title>
<dc:creator>Polozkov, R. G.</dc:creator>
<dc:creator>Ivanov, V. K.</dc:creator>
<dc:creator>Solov'yov, A. V.</dc:creator>
<dc:subject>Physics - Atomic and Molecular Clusters</dc:subject>
<dc:subject>Physics - Atomic Physics</dc:subject>
<dc:description>  Photoionization cross section of the fullerene ion C60+ has been calculated within a single-electron approximation and also by using a consistent many-body
theory accounting for many-electron correlations.
</dc:description>
<dc:description>Comment: 8 pages, 3 figures</dc:description>
<dc:date>2004-11-26</dc:date>
<dc:type>text</dc:type>
<dc:identifier>http://arxiv.org/abs/physics/0411239</dc:identifier>
<dc:identifier>doi:10.1088/0953-4075/38/24/001</dc:identifier>
</oai_dc:dc>
```

The article source files were obtained via [arXiv's s3 bucket](https://arxiv.org/help/bulk_data_s3). According to arXiv, the total size of the source files was ~190 GB around Feb. 2012. However, after unpacking all the files, the total was ~600 GB and numbered just below ~1.2 million articles. Though I had expected the 2012 statistics to be outdated, the difference in size was still somewhat surprising. 

```



```
###Tools

###Models

Doc2Vec model trained with full content: `s3://arxivdoc2vecmodel`.

##Future Work
- Talk about Spark, RowMatrix, GraphX, and Scala
- Talk about different strategies for parsing the
-

###

###
