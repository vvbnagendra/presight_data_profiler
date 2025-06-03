# Chat with dataframe via LLM

import pandas as pd
from pandasai import SmartDataframe
from data_quality.ollama_llm_adapter import OllamaLLM
import streamlit as st


# def get_smart_df(df: pd.DataFrame):
#     llm = Ollama(model="mistral")  # or "llama2", "gemma", etc.
#     return SmartDataframe(df, config={"llm": llm})

def get_smart_df(df: pd.DataFrame):

# Initialize the LocalLLM with Ollama's API
    # ollama_llm = LocalLLM(api_base="http://localhost:11434/v1", model="llama3")
    # llm = LocalLLM(model="mistral")  # or "llama2", "gemma", etc.
    llm_model = OllamaLLM()
    print("Buchiki")
    return SmartDataframe(df, config={"llm": llm_model})


# # Sample DataFrame
# df = pd.DataFrame({
#     "product": ["A", "B", "C"],
#     "sales": [100, 200, 150]
# })

# # Initialize custom LLM
# llm = OllamaLLM()

# # Wrap the DataFrame with SmartDataframe from PandasAI
# sdf = SmartDataframe(df, config={"llm": llm})

# # Ask a natural language question
# result = sdf.chat("Which product has the highest sales?")
# print("Answer from Ollama:", result)
