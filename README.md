# fsl_gotSportScrapper


Pip install the required modules into <b>fsl_gotSportScrapper_data</b>
This folder will end up getting a copy of lambda_function when its deployed to AWS.

https://aws.amazon.com/premiumsupport/knowledge-center/lambda-python-package-compatible/

pip install \
    --platform manylinux2014_x86_64 \
    --target=fsl_gotSportScrapper_data \
    --implementation cp \
    --python 3.9 \
    --only-binary=:all: --upgrade \
    requests

pip install \
    --platform manylinux2014_x86_64 \
    --target=fsl_gotSportScrapper_data \
    --implementation cp \
    --python 3.9 \
    --only-binary=:all: --upgrade \
    beautifulsoup4

 Test

https://dev.to/aissalaribi/how-to-use-beautiful-soup-in-aws-lambda-for-web-scrapping-1gh8

https://blog.jakoblind.no/aws-lambda-github-actions/

https://towardsdatascience.com/modern-ci-cd-pipeline-git-actions-with-aws-lambda-serverless-python-functions-and-api-gateway-9ef20b3ef64a


When pushing the zip to AWS the user needs to have permissions
- How to setup https://benoitboure.com/securely-access-your-aws-resources-from-github-actions