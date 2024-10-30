# lamnda用
FROM public.ecr.aws/lambda/python:3.12

COPY src/*.py requirements.txt ./

RUN pip install -r ./requirements.txt

CMD ["src.main.handler"]