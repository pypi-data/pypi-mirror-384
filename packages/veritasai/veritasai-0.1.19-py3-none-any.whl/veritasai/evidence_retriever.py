import torch
from sentence_transformers import SentenceTransformer, util
class evidence_retriever:
    def __init__(self):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
    def dot_score(self,a, b):
        return util.dot_score(a, b)
    def dot_score2(self,a, b):
        return torch.abs(util.dot_score(a,b))
    def cos_sim(self,a, b):
        return util.cos_sim(a, b)
    def cos_sim2(self,a, b):
        return torch.abs(util.cos_sim(a, b))
    def evidence_search(self,query,corpus,top_n=5,score_function=cos_sim2,score_limit=0.7):
        corpus_embeddings = self.embedder.encode(corpus, convert_to_tensor=True)
        corpus_embeddings = corpus_embeddings.to("cuda")
        corpus_embeddings = util.normalize_embeddings(corpus_embeddings)
        query_embeddings = self.embedder.encode(query, convert_to_tensor=True)
        query_embeddings = query_embeddings.to("cuda")
        query_embeddings = util.normalize_embeddings(query_embeddings)
        hits = util.semantic_search(query_embeddings, corpus_embeddings, score_function=score_function)
        data = []
        for i, hit in enumerate(hits):
            dat=[]
            for h in hit[0:top_n]:
                h["sentence"]=corpus[h["corpus_id"]]
                if h["score"]>score_limit:
                    dat.append(h)
            data.append(dat)
        return data