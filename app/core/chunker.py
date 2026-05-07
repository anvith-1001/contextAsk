import re

class Chunker:
    def __init__(self, chunk_size=500, overlap=50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def clean_text(self, text: str):
        text = re.sub(r'\s+', ' ', text)      
        text = re.sub(r'\n+', ' ', text)    
        text = text.strip()
        return text

    def chunk(self, text: str):
        text = self.clean_text(text)

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]

            if chunk.strip():
                chunks.append(chunk)

            start += self.chunk_size - self.overlap

        return chunks