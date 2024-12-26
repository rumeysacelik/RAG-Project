from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a polite chatbot. Rephrase the question based on context, ensuring it is standalone. "
     "Always maintain a respectful and professional tone. Do not include inappropriate or offensive content."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", "Use the following context to answer the query: {context}"),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

