from sentence_transformers import SentenceTransformer
import numpy as np
import json

class LightEmbeddingClassifier:
    def __init__(self, metadata_path, model_name='all-MiniLM-L6-v2'):
        """Initialize with the smallest effective model (80MB)"""
        # Load metadata
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)
        
        # Load model - this is the smallest useful model
        self.model = SentenceTransformer(model_name)
        
        # Prepare collections and tags
        self.collections = []
        self.collection_embeddings = []
        self.tags = []
        self.tag_embeddings = []
        
        # Create collection embeddings
        unique_collections = set()
        for metadata in self.metadata.values():
            if 'Collection' in metadata:
                collection = metadata['Collection']
                if collection not in unique_collections:
                    unique_collections.add(collection)
                    self.collections.append(collection)
        
        if self.collections:
            self.collection_embeddings = self.model.encode(self.collections)
        
        # Create tag embeddings
        unique_tags = set()
        for metadata in self.metadata.values():
            if 'Tags' in metadata:
                for tag in metadata['Tags']:
                    if tag not in unique_tags:
                        unique_tags.add(tag)
                        self.tags.append(tag)
        
        if self.tags:
            self.tag_embeddings = self.model.encode(self.tags)
    
    def classify(self, prompt, threshold=0.5, max_results=3):
        """Classify prompt using embeddings similarity"""
        results = {'collections': [], 'tags': []}
        
        # Encode prompt
        prompt_embedding = self.model.encode(prompt)
        
        # Match collections
        if len(self.collections) > 0:
            similarities = np.inner(prompt_embedding, self.collection_embeddings)
            indices = np.argsort(similarities)[-max_results:][::-1]
            
            for idx in indices:
                if similarities[idx] >= threshold:
                    results['collections'].append(self.collections[idx])
        
        # Match tags
        if len(self.tags) > 0:
            similarities = np.inner(prompt_embedding, self.tag_embeddings)
            indices = np.argsort(similarities)[-max_results:][::-1]
            
            for idx in indices:
                if similarities[idx] >= threshold:
                    results['tags'].append(self.tags[idx])
        
        return results