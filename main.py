from fastapi import FastAPI
from src.datamodel import InputQuery
from src.chatbot import *
from src.logger import logger
from uuid import uuid4
from dotenv import load_dotenv
import time

load_dotenv()
collection = os.getenv("HISTORY_DB_COLLECTION")
app = FastAPI()

@app.api_route("/return_output", methods=["POST"])
async def root(data: InputQuery):
    try:
        chatbot = Chatbot()
        logger.log("Chatbot successfully initiated")
    except Exception as e:
        logger.error(f"Failed to initialize the instance of chatbot with error: {e}")
    query = data.query
    session_id = data.session_id
    await chatbot.load_history(session_id)
    
    try:
        message_id = str(uuid4())
        answer = await chatbot.ask_llm(query)
        chatbot.insert_qa_pair(message_id, query, answer)
        logger.log(f"Inserted QA pair at collection: {collection}") 
               
        output = {"session_id": session_id,
                  "message_id": message_id,
                  "query": query,
                  "response": answer,
                  }
        return output
    
    except Exception as e:
        logger.error(f"Failed to answer the query with error: {e}")
        raise Exception(str(e))
    
    