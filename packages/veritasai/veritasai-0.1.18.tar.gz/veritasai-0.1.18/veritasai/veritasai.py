import json
from .claim_extractor import claim_extractor
from .claim_verifier import claim_verifier
from .evidence_retriever import evidence_retriever
import pandas as pd
class veritasai:
    def __init__(self,EXBASE_ID="unsloth/mistral-7b-instruct-v0.2-bnb-4bit",EXADAPTER_ID="SYX/mistral_based_claim_extractor",EXprompt=None,VRBASE_ID="unsloth/llama-3-8b-Instruct-bnb-4bit", VRADAPTER_ID="SYX/llama3_based_claim_verifier",VRprompt=None):
        self.ce = claim_extractor(EXBASE_ID,EXADAPTER_ID)
        self.cv = claim_verifier(VRBASE_ID,VRADAPTER_ID,VRprompt)
        self.er = evidence_retriever()
    def extract_claims(self,reports,knowledgebase,language = "english",top_n=5,score_limit=0.5,score_function=None):
        if score_function is None:
            score_function = self.er.cos_sim2
        fact_checks=[]
        for report in reports:
            text_out, claims = self.ce.extract_claims(report,language = language)
            hits = self.er.evidence_search(claims, knowledgebase, top_n,score_function,score_limit)
            fact_check=[]
            for i in range(len(claims)):
                sentences=[]
                for hit in hits[i]:
                    sentences.append(hit["sentence"])
                raw, parsed = self.cv.verify_claim(claims[i],sentences)
                fact_check.append({"claim":claims[i], "evidence":sentences, "labels":parsed})
            fact_checks.append({"report":report,"fact_check":fact_check})
        rows=[]
        for i in range(len( fact_checks)):
            fact = fact_checks[i]["fact_check"]
            countSupported=0
            countRefuted=0
            countInsufficient=0 
            for j in range(len(fact)):
                labels=fact[j]["labels"]
                sflag=False
                rflag=False
                for l in labels:
                    if(l["label"].upper() == "SUPPORTED"):
                        sflag=True
                    elif(l["label"].upper() == "REFUTED"):
                        rflag=True
                if(rflag):
                    countRefuted+=1
                elif(sflag):
                    countSupported+=1
                else:
                    countInsufficient+=1
            rows.append({
                "report_id": i,
                "total_claims": len(fact),
                "count_supported": countSupported,
                "count_refuted": countRefuted,
                "count_insufficient": countInsufficient,
            })
        df = pd.DataFrame(rows)
        return df,fact_checks
