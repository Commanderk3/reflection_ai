import config
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)

qdrant = QdrantClient(
    url=config.QDRANT_URL,
    api_key=config.QDRANT_API_KEY,
)

vectorstore = QdrantVectorStore(
    client=qdrant,
    collection_name="mb_docs",
    embedding=embeddings
)

relevance_threshold = 0.3  # distance metric, so lower is more relevant

def getContext(query):
    results = vectorstore.similarity_search_with_score(query, k=3)
    relevant_docs = [(doc, score) for doc, score in results if score > relevance_threshold]
    
    print("Scores:", [score for _, score in results])
    
    if relevant_docs:
        rag_context = " ".join(doc.page_content for doc, _ in relevant_docs)
        return rag_context
    else:
        return None

print(getContext("hi"))