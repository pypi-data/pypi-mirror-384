FROM quay.io/pypa/manylinux2014_aarch64:latest

RUN yum -y update && yum install -y \  
libpcap-devel

ENV PATH="/opt/python/cp310-cp310/bin:${PATH}"  

RUN pip install twine

RUN git clone https://github.com/seladb/PcapPlusPlus.git --branch master && \
cd PcapPlusPlus && \
git checkout 0a843116d6f679f6dcc9f9c3c002ca94b32c227f && \
cmake -S . -DPCAPPP_BUILD_EXAMPLES=OFF -DPCAPPP_BUILD_TESTS=OFF -B build && \
cmake --build build --target install
