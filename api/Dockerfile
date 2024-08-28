FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.9
RUN yum update -y && yum install -y \
    libxml2-devel \
    libxslt-devel \
    gcc \
    gcc-c++ \
    make \
    && yum clean all
RUN pip install "sumy[LSA]" lxml_html_clean && \
    python -c "import nltk; nltk.download('punkt_tab',download_dir='$LAMBDA_TASK_ROOT')"
RUN pip install boto3==1.35.5
# copy function
COPY app.py ${LAMBDA_TASK_ROOT}
RUN chmod 644 ${LAMBDA_TASK_ROOT}/app.py
# set the CMD to your handler
CMD [ "app.handler" ]