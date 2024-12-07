from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
import json
from typing import Dict, List

class ConversationStore:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = Chroma(
            collection_name="conversation_history",
            embedding_function=self.embeddings,
            persist_directory="./conversation_store"
        )
    
    def add_interaction(self, qa_details: Dict):
        # Create a document that combines all relevant information
        text = f"""
        Question: {qa_details['user_input']}
        SQL Query: {qa_details['sql_queries']}
        Answer: {qa_details['final_answer']}
        """
        
        # Add metadata for filtering
        metadata = {
            "type": "conversation",
            "timestamp": qa_details.get('timestamp', ''),
            "question": qa_details['user_input']
        }
        
        doc = Document(page_content=text, metadata=metadata)
        self.vectorstore.add_documents([doc])
        self.vectorstore.persist()
    
    def get_relevant_history(self, current_question: str, k: int = 3) -> List[str]:
        # Search for relevant previous conversations
        results = self.vectorstore.similarity_search(
            current_question,
            k=k,
            filter={"type": "conversation"}
        )
        return [doc.page_content for doc in results] 