from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.core.credentials import AzureKeyCredential  
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizableTextQuery  
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.collection import Collection
from .logger import logger
from dotenv import load_dotenv
import numpy as np
import pymongo
import openai
import asyncio
import time
import os

load_dotenv()

credentials = DefaultAzureCredential()
vault_url = os.getenv("VAULT_URL")
service_endpoint_key = os.getenv("ACS_SERVICE_ENDPOINT_KV")
index_name_key = os.getenv("ACS_INDEX_NAME")
credential_key = os.getenv("CREDENTIAL_KEY")
completion_api_key_kv = os.getenv("COMPLETION_API_KEY_KV")
completion_api_base_kv = os.getenv("COMPLETION_API_BASE_KV")
embedding_api_key_kv = os.getenv("EMBEDDING_API_KEY_KV")
embedding_api_base_kv = os.getenv("EMBEDDING_API_BASE_KV")
api_version_kv = os.getenv("API_VERSION_KV")
history_database = os.getenv("HISTORY_DB")
collection = os.getenv("HISTORY_DB_COLLECTION")

credentials = DefaultAzureCredential()
secret_client = SecretClient(vault_url=vault_url, credential=credentials)
service_endpoint = secret_client.get_secret(service_endpoint_key).value
index_name = secret_client.get_secret(index_name_key).value
completion_api_key = secret_client.get_secret(completion_api_key_kv).value
completion_api_base = secret_client.get_secret(completion_api_base_kv).value
embedding_api_key = secret_client.get_secret(embedding_api_key_kv).value
embedding_api_base = secret_client.get_secret(embedding_api_base_kv).value
key = secret_client.get_secret(credential_key).value


credential = AzureKeyCredential(key)
search_client = SearchClient(endpoint=service_endpoint, index_name=index_name, credential=credential)

openai.api_type = "azure"  
openai.api_version = "2023-07-01-preview"

class Chatbot():
    try:
        db_client = AsyncIOMotorClient(os.getenv("DB_CLIENT_CONNECTION_STRING"))
        logger.log("Connected to MongoDB server successfully")
    except Exception as e:
        logger.log(f"Failed to connect to MongoDB server with error {str(e)}")
        raise Exception(str(e))
    
    conversation_history_collection: Collection = db_client[history_database][collection]
    
    def __init__(self):
        self.history = [{"role": "system", "content": """You are an assistant chatbot. Answer the user\'s query as truthfully as possible.
                               follow the following instructions to answer the query.
                               1) If some context is provided, use it to answer the query.
                               2) if no context is provided, use the history to answer the query.
                               3) If history also does not contains the answer, just say 'I don\'t know'.
                               4) Avoid answering with prefix \'based on the context provided\'."""}]
        
        
    async def get_embedding(self, text):
        """
        Generated openai\'s embedding for given query

        Args:
            text (str): text for which embedding needs to be generated

        Returns:
            List: list of float representing the text in form of embedding
        """
        response = await openai.Embedding.acreate(
            # engine = "text-embedding-ada-002",
            api_key = embedding_api_key,
            api_base = embedding_api_base,
            deployment_id = "genaiada002",
            input = text
        )
        logger.log(f"Embedding generated for query: {text}")
        return response["data"][0]["embedding"]
    
    async def vector_similarity(self, x, y):
        """
        Returns the similarity between two vectors.
        Because OpenAI Embeddings are normalized to length 1, the cosine similarity is the same as the dot product.

        Args:
            x, y: Vectors

        Returns:
            Float: dot product of two vectors
    """
        return np.dot(np.array(x), np.array(y))
    
    
    async def load_history(self, session_id):
        """
        Loading the last 5 QA pair from MongoDB collection, 

        Args:
            session_id (str): session_id for given to user
        """
        documents = await collection.find({"session_id":session_id}).sort([("date-time",pymongo.DESCENDING)]).limit(10)     
        updated_history = []
        async for document in documents:                            
            updated_history.append({"role":"assistant", "content":document["response"]})     
            updated_history.append({"role":"user", "content": document["prompt"]})   
            
        self.history.extend(reversed(updated_history))
    
    
    async def insert_qa_pair(message_id, query, answer):
        """Storing the QA pair to MongoDB collection

        Args:
            message_id (str): message id generated using UUID
            query (str): user\'s query
            answer (str): response generated from LLM.
        """
        document = {"message_id": message_id,
                    "query": query,
                    "response": answer,
                    "time-stamp": time.time()}
        await Chatbot.conversation_history_collection.insert_one(document)
        
    
    async def build_context(self, query): 
        """
        Retrieving the relevant documents from Azure Cognitive Search for the user\'s query
        
        Args:
            query: query asked by user
            
        Returns:
            str: context built by the relevant documents"""  
        vector_query = VectorizableTextQuery(text=query, k=5, fields="embedding") 
        results = await search_client.search(  
        search_text=None,  
        vector_queries= [vector_query],
        select=["text", "filename","embedding"],
    )  
        logger.log("Context retrieved from Azure Cognitive Search")
        context = ""
        embeddings = []
        async for result in results: 
            if self.vector_similarity(result["embedding"], self.get_embedding(query)) < 0.8:
                continue
            context += "Context: " + result['text'] + "\n\n"

        context += f"Query: {query}"
        logger.log("Context Successfully Built")
        return context
    
    
    async def ask_llm(self, query):
        context = await self.build_context(query)
        self.history.append({"role": "user", "content": context})
        response = await openai.ChatCompletion.acreate(
            api_key = completion_api_key,
            api_base = completion_api_base,
            messages = self.history,
            deployment_id = "genaigpt35turbo",
            temperature = 1
        )
        logger.log(f"Answer generated for query: {query}")
        return response["choices"][0]["message"]["content"]
    
