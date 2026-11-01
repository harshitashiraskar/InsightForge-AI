import os
import pandas as pd
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

def main():
    print("🚀 Starting Automated Text-to-SQL Pipeline...")

    # 1. Initialize Ollama LLM
    llm = ChatOllama(model="qwen2.5-coder:7b", temperature=0, num_ctx=2048)

    # 2. Load CSV File
    csv_file_path = "sample_sales.csv"
    if not os.path.exists(csv_file_path):
        pd.DataFrame({
            'order_id': [101, 102, 103],
            'product_category': ['Electronics', 'Clothing', 'Home'],
            'revenue': [1200, 450, 300]
        }).to_csv(csv_file_path, index=False)

    df_user = pd.read_csv(csv_file_path)
    engine = create_engine("sqlite:///:memory:")
    df_user.to_sql('dataset', con=engine, if_exists='replace', index=False)
    db = SQLDatabase(engine)

    # 3. Schema RAG Vector Indexing
    embeddings = FastEmbedEmbeddings()
    table_documents = [
        Document(
            page_content=f"Table Name: {table}\nSchema:\n{db.get_table_info([table])}",
            metadata={"table_name": table}
        ) for table in db.get_usable_table_names()
    ]
    vector_store = Chroma.from_documents(table_documents, embedding=embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 1})

    # 4. Define Chains
    prompt = PromptTemplate.from_template("""
    You are an expert SQL developer. Write a valid SQLite query for the question. Output ONLY SQL in markdown tags.
    Schema: {schema}
    Question: {question}
    """)
    chain = prompt | llm | StrOutputParser()

    # 5. Execute Question
    question = "What is the total revenue by product category?"
    print(f"\n❓ Question: {question}")

    relevant_docs = retriever.invoke(question)
    retrieved_schema = "\n\n".join([doc.page_content for doc in relevant_docs])
    
    raw_response = chain.invoke({"schema": retrieved_schema, "question": question})
    sql_query = raw_response.replace("```sql", "").replace("```", "").strip()

    print(f"\n⚡ Generated SQL:\n{sql_query}\n")
    
    result_df = pd.read_sql_query(sql_query, engine)
    print("📊 Execution Results:")
    print(result_df)

if __name__ == "__main__":
    main()


 