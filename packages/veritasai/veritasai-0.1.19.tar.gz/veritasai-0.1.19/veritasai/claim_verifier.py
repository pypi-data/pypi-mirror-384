import json, re, torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
class claim_verifier:
    def __init__(self, BASE_ID="unsloth/llama-3-8b-Instruct-bnb-4bit", ADAPTER_ID="SYX/llama3_based_claim_verifier",prompt=None):
        # BitsAndBytes 4-bit config
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )
        
        self.tokenizer = AutoTokenizer.from_pretrained(BASE_ID, use_fast=True, trust_remote_code=True)
        
        base = AutoModelForCausalLM.from_pretrained(
            BASE_ID,
            device_map="auto",
            trust_remote_code=True,
            quantization_config=bnb_config,
        )
        if(ADAPTER_ID is None):
            self.model = base
        else:
            self.model = PeftModel.from_pretrained(base, ADAPTER_ID)
        self.model.eval()
        if prompt is None:
            self.prompt = ("You are a precise fact-checking assistant. "
                    "Given a CLAIM and EVIDENCE, decide whether the claim is SUPPORTED, REFUTED, or INSUFFICIENT. "
                    "Return JSON: {\"label\": \"SUPPORTED|REFUTED|INSUFFICIENT\", \"rationale\": \"...\"}.")
        else:
            self.prompt = prompt
            

    def build_messages(self,claim: str, evidence: str):
        """
        Use Llama 3 chat template.
        Instruct the model to return compact JSON with one of: SUPPORTED, REFUTED, INSUFFICIENT.
        """
        system = self.prompt
        user = f"CLAIM: {claim}\n\nEVIDENCE:\n{evidence}\n\nRespond with JSON only."
        return [
            {"role": "system", "content": system},
            {"role": "user",   "content": user}
        ]
    
    def generate(self,messages, max_new_tokens=256, temperature=0.0, top_p=0.9):
        # Use the tokenizer's native chat template for Llama 3
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=temperature > 0,
                temperature=temperature,
                top_p=top_p,
                repetition_penalty=1.05,
                eos_token_id=self.tokenizer.eos_token_id,
            )
        text = self.tokenizer.decode(out[0], skip_special_tokens=True)
        return text
    
    def parse_json(self,text: str):
        """
        Best-effort JSON extraction from the model output.
        """
        # First try a direct json.loads
        text=text.split("Respond with JSON only")[1]
        try:
            return json.loads(text)
        except Exception:
            pass
        # Fallback: find JSON block
        m = re.search(r"\{.*\}", text, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return {"raw": text}
        return {"raw": text}
    
    def verify_claim(self,claim: str, evidences, max_new_tokens=256, temperature=0.0, top_p=0.9):
        raws=[]
        parseds=[]
        for evidence in evidences:
            msgs = self.build_messages(claim, evidence)
            raw = self.generate(msgs,max_new_tokens, temperature, top_p)
            parsed = self.parse_json(raw)
            raws.append(raw)
            parseds.append(parsed)
        return raws, parseds