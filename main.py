from fastapi import FastAPI, Request
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_huggingface import HuggingFaceEmbeddings
from retriever import getContext
from sentence_transformers import SentenceTransformer
from fastapi.middleware.cors import CORSMiddleware
import config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or use frontend's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models and embeddings
model = SentenceTransformer(config.EMBEDDING_MODEL)
embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)

llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.0-flash",
    google_api_key=config.GOOGLE_API_KEY,
    temperature=0.7
)

instruction = """
Role: You are a teacher on the MusicBlocks platform, guiding users through deep, analytical discussions that foster conceptual learning and self-improvement. WORD LIMIT: 30.
Guidelines:
1.Structured Inquiry: Ask these in order:
    What did you do?,
    Why did you do it?,
    What approach you used? Why this approach?,
    Ask technical questions based on context. Discuss alternatives. (Ask follow-up questions),
    Were you able to achieve the desired goal? If no, what do you think went wrong? (Ask follow-up questions to clarify),
    What challenges did you face?,
    What did you learn?,
    What's next?

2.Cross question if something is not clear,
3.Try to get to the root of the user's understanding,
4.Avoid repetition. Adapt questions based on context and previous responses.
5.Judge the provided context, if it has context to user query then use it.
6.Keep the conversation on track if the user deviates.
7.Limit your side to 20 dialogues.
8.Focus only on the current project. Ignore past projects.
9.After all questions, ask if they want to continue. If not, give a goodbye message.
"""

messages = [SystemMessage(instruction)]

old_summary = """Let's summarize what we've discussed so far:
You created a project in Music Blocks and made a cool hip-hop beat. You used the Pitch-Drum Matrix to experiment with different rhythms and patterns, which allowed you to think freely and focus on the creative aspect.
You learned that trying different patterns is not the only thing to focus on when creating a beat, and that splitting a note value can lead to some really cool and unique sounds.
You're planning to create a chord progression that suits your beat and wants to enhance or complement its vibe."""

class QueryRequest(BaseModel):
    query: str

@app.post("/chat/")
async def chat(request: QueryRequest):
    query = request.query.strip()
    full_response = ""
    if not query:
        return {"error": "Empty query"}

    relevant_docs = getContext(query)
    # remove in deployment
    if not relevant_docs:
        full_response = "⚠️ No relevant documents found.\n"

    messages.append(HumanMessage(query))
    prompt = combined_input(relevant_docs, messages)

    try:
        result = llm.invoke(prompt)
        full_response += result.content
    except Exception as e:
        return {"error": str(e)}

    messages.append(AIMessage(content=full_response))

    terminate = False
    if len(messages) > 30 and decide_to_terminate(full_response) == "yes":
        terminate = True

    return {
        "response": full_response,
        "terminate": terminate
    }

@app.get("/summary/")
def summary():
    new_summary = generate_summary(messages)
    outcome = analysis(old_summary, new_summary)
    return {
        "new_summary": new_summary.content,
        "outcome": outcome.content
    }

def combined_input(rag, messages):
    conversation_history = ""
    for msg in messages:
        role = "System" if isinstance(msg, SystemMessage) else "User" if isinstance(msg, HumanMessage) else "Assistant"
        conversation_history += f"{role}: {msg.content}\n"
    return f"Context: {rag}\nConversation History:\n{conversation_history}\nAssistant:"

def generate_summary(messages):
    user_queries = [msg.content for msg in messages if isinstance(msg, HumanMessage)]
    assistant_responses = [msg.content for msg in messages if isinstance(msg, AIMessage)]
    summary_prompt = f"""
    Analyze the following conversation and generate a concise summary for the User's learning and takeaways points. Cover User Queries only.
    Add only relevant information in this summary. Write a paragraph under 100 words (detailed).
    User Queries:
    {user_queries}
    Assistant Responses:
    {assistant_responses}
    Summary:
    """
    return llm.invoke(summary_prompt)

def analysis(old_summary, new_summary):
    analysis_prompt = f"""
    Analyze the user's learning by comparing two summaries. Identify key improvements, knowledge growth, and remaining gaps. 
    Provide a constructive, truthful and realistic assessment of their development over time in a paragraph under 50 words, avoiding flattery.
    Previous Summary:
    {old_summary}
    Current Summary:
    {new_summary}
    Learning Outcome:
    """
    return llm.invoke(analysis_prompt)

def decide_to_terminate(response):
    prompt = f"""
    AI Message: "{response}"
    Did the AI say bye to the user? Is the AI saying that the conversation is over and come to an end? 
    (only yes/no)
    """
    decision = llm.invoke(prompt).content.strip().lower()
    return decision
