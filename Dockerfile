# Author: Mitchell Then

FROM ubuntu:17.10

RUN apt-get update -q && apt-get install -qy \
    python3 \
    python3-pip && \
    bash -c "apt-get install -qy --no-install-recommends texlive-{base,bibtex-extra,extra-utils,generic-recommended,fonts-recommended,font-utils,latex-base,latex-recommended,latex-extra,pictures,pstricks,science} perl-tk purifyeps chktex latexmk dvipng xindy dvidvi fragmaster lacheck latexdiff libfile-which-perl dot2tex tipa prosper"

COPY requirements.txt /root/requirements.txt

RUN pip3 install -r requirements.txt

COPY make_pdfs.py /root/make_pdfs.py

WORKDIR /data
VOLUME [ "/data" ]
