#!/bin/bash

# fetch metadata on the source file chunks (these can be  PDF file, or a gzipped TeX, DVI, PostScript or HTML)
aws s3api get-object --request-payer requester --bucket arxiv --key src/arXiv_src_manifest.xml  ./src-metadata/arXiv_src_manifest.xml
# fetch metadata on the pdf file chunks
aws s3api get-object --request-payer requester --bucket arxiv --key pdf/arXiv_pdf_manifest.xml  ./src-metadata/arXiv_pdf_manifest.xml
