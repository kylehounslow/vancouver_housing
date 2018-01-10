FROM ubuntu:16.04

RUN apt-get update
RUN apt-get install -y software-properties-common # for add-apt-repository
RUN apt-get install -y curl bash-completion
RUN apt-get install -y git
RUN apt-get install -y imagemagick
# install python3.6
RUN add-apt-repository ppa:jonathonf/python-3.6
RUN apt-get update
RUN apt-get install -y build-essential python3.6 python3.6-dev python3-pip python3.6-venv
# update pip
RUN python3.6 -m pip install pip --upgrade
RUN python3.6 -m pip install wheel
# install jupyter and widgets
RUN python3.6 -m pip install jupyter
RUN python3.6 -m pip install ipyleaflet
# enable widgets
RUN jupyter nbextension enable --py widgetsnbextension --sys-prefix && \
    jupyter nbextension enable --py --sys-prefix ipyleaflet

# install numpy before tensorflow (in requirements.txt)
RUN python3.6 -m pip install numpy
# install tensorflow deps
RUN apt-get install -y graphviz libgraphviz-dev
#install requirements.txt
COPY requirements.txt /home/digitalist/requirements.txt
RUN python3.6 -m pip install -r /home/digitalist/requirements.txt

# install xgboost
RUN git clone --recursive https://github.com/dmlc/xgboost
RUN cd xgboost && make -j$(nproc) && cd python-package && python3.6 setup.py install

#some env vars to fix bug with Click lib in python3
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# uninstall some libs to trim down image size
RUN apt-get remove -y g++ gcc ssh make curl build-essential
RUN apt-get clean autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/

# notebook env setup
EXPOSE 8888
ENV PYTHONPATH=/home/digitalist
