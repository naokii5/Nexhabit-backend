# lambda web adapter
FROM public.ecr.aws/lambda/python:3.12
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 /lambda-adapter /opt/extensions/lambda-adapter

# 依存関係
RUN pip install --upgrade pip
COPY src/ requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt

# 実行
ENTRYPOINT ["uvicorn"]
CMD [ "main:app", "--host", "0.0.0.0", "--port", "8080"]

