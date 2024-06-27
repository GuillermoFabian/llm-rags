import requests
from datetime import datetime
from elasticsearch import Elasticsearch
import tiktoken

# Fetch documents
docs_url = 'https://github.com/DataTalksClub/llm-zoomcamp/blob/main/01-intro/documents.json?raw=1'
docs_response = requests.get(docs_url)
documents_raw = docs_response.json()

documents = []

for course in documents_raw:
    course_name = course['course']

    for doc in course['documents']:
        doc['course'] = course_name
        documents.append(doc)

print(documents[0])

es_client = Elasticsearch('http://localhost:9200')  
print(es_client.info())


index_settings = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "text": {"type": "text"},
            "section": {"type": "text"},
            "question": {"type": "text"},
            "course": {"type": "keyword"} 
        }
    }
}



query = "How do I execute a command in a running docker container?"

index_name = 'faq'
if not es_client.indices.exists(index=index_name):
    es_client.indices.create(index=index_name, body=index_settings)

for doc in documents:
    res = es_client.index(index=index_name, body=doc)
    print(res)


search_query = {
    "size": 5,
    "query": {
        "bool": {
            "must": {
                "multi_match": {
                    "query": query,
                    "fields": ["question^4", "text"],
                    "type": "best_fields"
                }
            }
            }
        }
    }


search_query_filtered = {
    "size": 5,
    "query": {
        "bool": {
            "must": {
                "multi_match": {
                    "query": query,
                    "fields": ["question^4", "text"],
                    "type": "best_fields"
                }
            },
            "filter": {
                "term": {
                    "course": "machine-learning-zoomcamp"
                }
            }
        }
    }
}

res = es_client.search(index=index_name, body=search_query_filtered)



if res['hits']['hits']:
    most_similar_result = res['hits']['hits'][0]
    print("Most similar result score:", most_similar_result['_score'])


if len(res['hits']['hits']) >= 3:
    third_result = res['hits']['hits'][2]
    print("Third question:", third_result['_source']['question'])




context_entries = []
for hit in res['hits']['hits']:
    context_entries.append(f"Q: {hit['_source']['question']}\nA: {hit['_source']['text']}")

context = "\n\n".join(context_entries)

print(context)


prompt_template = """
You're a course teaching assistant. Answer the QUESTION based on the CONTEXT from the FAQ database.
Use only the facts from the CONTEXT when answering the QUESTION.

QUESTION: {question}

CONTEXT:
{context}
""".strip()

question = "How do I execute a command in a running docker container?"
prompt = prompt_template.format(question=question, context=context)


print("Length of the resulting prompt:", len(prompt))


encoding = tiktoken.encoding_for_model("gpt-4o")
tokens = encoding.encode(prompt)
num_tokens = len(tokens)

print("Number of tokens in the prompt:", num_tokens)

