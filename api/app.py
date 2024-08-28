import traceback
import os
from sumy.parsers.html import HtmlParser
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from sumy.nlp.stemmers import Stemmer
import nltk
from nltk.tokenize import PunktTokenizer
from sumy.utils import get_stop_words
import json
import zipfile
import boto3
from botocore.exceptions import ClientError


REQUIRED_TOKEN = os.getenv("TOKEN")
LANGUAGE = "english"
SENTENCES_COUNT = 10


def query_bedrock_and_summarize(text):
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
    )
    # model configuration
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    model_kwargs = {
        "max_tokens": 2048,
        "temperature": 0.1,
        "top_k": 250,
        "top_p": 1,
        "stop_sequences": ["\n\nHuman"],
    }
    # input configuration
    prompt = f"Please summarize and clarify the following text in a concise manner:\n\n{text}"
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "system": "You are a honest and helpful bot.",
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": prompt}]},
        ],
    }
    body.update(model_kwargs)
    # invoke
    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps(body),
    )
    # process response
    result = (
        json.loads(response.get("body").read()).get("content", [])[0].get("text", "")
    )
    return result


def handler(event, context):
    try:
        # check that its a post request
        if event.get("requestContext", {}).get("http", {}).get("method") != "POST":
            return {"statusCode": 401, "body": "unauthorized"}
        # check that there's an auth header
        auth_header = event.get("headers", {}).get("authorization")
        if not auth_header:
            return {"statusCode": 401, "body": "unauthorized"}
        # check for a Bearer <token>
        try:
            token = auth_header.split(" ")[1]
        except:
            return {"statusCode": 401, "body": "unauthorized"}
        # check token matches the REQUIRED_TOKEN
        if token != REQUIRED_TOKEN:
            return {"statusCode": 401, "body": "unauthorized"}

        # this line is because we are installing punkt_tab into the lambda working directory
        # and we want ntlk to be able to find it
        nltk.data.path.append(os.getcwd())

        # this override is here because ntlk has an issue right now with pickling and
        # this specific function in Tokenizer needed to be revised to use punkt_tab and not punkt
        class ModifiedTokenizer(Tokenizer):
            def _get_sentence_tokenizer(self, language):
                if language in self.SPECIAL_SENTENCE_TOKENIZERS:
                    return self.SPECIAL_SENTENCE_TOKENIZERS[language]
                try:
                    return PunktTokenizer(language)
                except (LookupError, zipfile.BadZipfile) as e:
                    raise LookupError(
                        "NLTK tokenizers are missing or the language is not supported.\n"
                        """Download them by following command: python -c "import nltk; nltk.download('punkt_tab')"\n"""
                        "Original error was:\n" + str(e)
                    )

        # get url passed to function
        url = json.loads(event.get("body", "{}")).get("url")
        # use `sumy` to do the summarization magic
        parser = HtmlParser.from_url(url, ModifiedTokenizer(LANGUAGE))
        stemmer = Stemmer(LANGUAGE)
        summarizer = Summarizer(stemmer)
        summarizer.stop_words = get_stop_words(LANGUAGE)
        summary = summarizer(parser.document, SENTENCES_COUNT)
        result = " ".join(str(sentence) for sentence in summary)
        # refine result with bedrock
        result = query_bedrock_and_summarize(result)
        # return result
        return {
            "statusCode": 200,
            "headers": {"content-type": "application/json"},
            "body": {"result": result},
        }
    except:
        traceback.print_exc()
        return {
            "statusCode": 200,
            "headers": {"content-type": "application/json"},
            "body": {"result": traceback.format_exc()},
        }
