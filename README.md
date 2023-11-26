# Openai Chatbot

- This chatbot is built with openai's apis. Purpose of this chatbot is to answer user's query related to some topic. 
- documents for the topic is/need to be indexed in Azure Cognitive Search's index.
- conversation is saved in MongoDB's database collection
- Since there are token limits for llm models, chatbot is set to load the last 5 QA pairs from database.
- The FastAPI framework is utilized to build the API, and all methods in the chatbot class are asynchronous to handle concurrent requests efficiently.

## Features

- Chatbot takes maximum of 10 seconds to answer the user's query
- Chatbot can remember upto last 5 question-answer pair. We can increase this limit by opting for llm that can take more number of tokens.
  eg, gpt-4-32k which has 32000 tokens and thus can take much more prompt(input) in it for the completion.

## Prerequisites
- Python 3.7 or higher
- Azure Cognitive Search service
- MongoDB database
- OpenAI API key


## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Abhishek271099/openai-chatbot.git

2. install the dependencies by following command
    `pip install -r requirements.txt`

3. modify the paramenters in .env file

4. run the app by following command
    `uvicorn main:app`
or 
    `uvicorn main:app --reload`

  flag --reload lets you make changes in source code and automatically reflects in app by pressing CTRL + S.
