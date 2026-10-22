import os
import boto3
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

REGION = os.environ.get("AWS_REGION", "eu-central-1")
KB_ID = os.environ["KB_ID"]
MODEL_ID = os.environ["MODEL_ID"]

agent = boto3.client("bedrock-agent-runtime", region_name=REGION)
brt = boto3.client("bedrock-runtime", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)

SYSTEM = (
    "You answer questions using ONLY the numbered sources provided. "
    "Cite sources like [1] or [2] after the claims they support. "
    "If the sources don't contain the answer, say you couldn't find it in the documents."
)

def presign(uri):
    if not uri or not uri.startswith("s3://"):
        return None
    bucket, key = uri[5:].split("/", 1)
    return s3.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=300
    )

def answer(question):
    r = agent.retrieve(
        knowledgeBaseId=KB_ID,
        retrievalQuery={"text": question},
        retrievalConfiguration={"managedSearchConfiguration": {"numberOfResults": 6}},
    )
    results = r.get("retrievalResults", [])
    if not results:
        return "I couldn't find anything relevant in the documents.", []
    ctx = "\n\n".join(f"[{i+1}] {x['content']['text']}" for i, x in enumerate(results))
    resp = brt.converse(
        modelId=MODEL_ID,
        system=[{"text": SYSTEM}],
        messages=[{"role": "user", "content": [{"text": f"Sources:\n{ctx}\n\nQuestion: {question}"}]}],
        inferenceConfig={"maxTokens": 800, "temperature": 0.2},
    )
    text = resp["output"]["message"]["content"][0]["text"]
    links = []
    for i, x in enumerate(results):
        uri = x.get("location", {}).get("s3Location", {}).get("uri")
        url = presign(uri)
        if url:
            links.append(f"[{i+1}] [{uri.split('/')[-1]}]({url})")
    return text, links

st.title("Ask your documents")
if "history" not in st.session_state:
    st.session_state.history = []

for role, content in st.session_state.history:
    st.chat_message(role).markdown(content)

if q := st.chat_input("Ask a question about your PDFs"):
    st.chat_message("user").markdown(q)
    with st.spinner("Searching..."):
        text, links = answer(q)
    reply = text + ("\n\n**Sources**  \n" + "  \n".join(links) if links else "")
    st.chat_message("assistant").markdown(reply)
    st.session_state.history += [("user", q), ("assistant", reply)]
