#! /bin/bash

export $( grep -vE "^(#.*|\s*)$" .env )


# build and push ecr image
docker build -t sumy .
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com 
aws ecr create-repository --repository-name sumy --region $REGION > /dev/null
docker tag sumy:latest $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/sumy:latest
docker push $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/sumy:latest

# deploy lambda
aws iam create-role --role-name "sumy_role" --assume-role-policy-document file://trust_policy.json > /dev/null
sleep 5
aws iam attach-role-policy --role-name "sumy_role" --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole > /dev/null
aws iam attach-role-policy --role-name "sumy_role" --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess > /dev/null
aws lambda create-function --function-name "sumy" --package-type Image --code ImageUri=$ACCOUNT.dkr.ecr.$REGION.amazonaws.com/sumy:latest --role "arn:aws:iam::${ACCOUNT}:role/sumy_role" --timeout 180 --memory-size 2048  --environment Variables={TOKEN="${TOKEN}"} > /dev/null
sleep 5
# create function url
aws lambda create-function-url-config \
    --function-name sumy \
    --auth-type NONE \
    --cors '{"AllowOrigins": ["*"], "AllowMethods": ["*"], "AllowHeaders": ["*"], "AllowCredentials": false}' > /dev/null
aws lambda add-permission \
    --function-name sumy \
    --statement-id FunctionURLAllowPublicAccess \
    --action lambda:InvokeFunctionUrl \
    --principal "*" \
    --function-url-auth-type NONE > /dev/null