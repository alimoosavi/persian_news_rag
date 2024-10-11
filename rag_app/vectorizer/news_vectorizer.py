import os
import pandas as pd
import torch
from rag_app.models import News
from transformers import BertTokenizer, BertModel


class NewsVectorizer:
    BATCH_SIZE = 10000
    CACHE_DIR = "./model_cache"  # Specify your cache directory

    def __init__(self, logger):
        # Create cache directory if it doesn't exist
        os.makedirs(self.CACHE_DIR, exist_ok=True)

        # Load tokenizer and model from the cache directory
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased', cache_dir=self.CACHE_DIR)
        self.model = BertModel.from_pretrained('bert-base-multilingual-cased', cache_dir=self.CACHE_DIR)
        self.logger = logger

    @classmethod
    def get_batch(cls):
        queryset = (News
                    .objects
                    .filter(has_processed=False)
                    .order_by('-date')
                    .values('id', 'title', 'body')[:cls.BATCH_SIZE])

        return pd.DataFrame(list(queryset))

    def get_embeddings(self, texts):
        inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1)

    def run(self):
        while True:
            batch_df = self.get_batch()
            if batch_df.empty:  # Check if the batch is empty
                break

            batch_df['embedding'] = batch_df['body'].apply(lambda x: self.get_embeddings(x).numpy())
            print(batch_df)
            break
