import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
class claim_extractor:
    def __init__(self, BASE_ID="unsloth/mistral-7b-instruct-v0.2-bnb-4bit", ADAPTER_ID="SYX/mistral_based_claim_extractor",):
        
        # ---- Device & dtype
        self.device_map = "auto"  # spreads layers across available GPUs if needed
        self.torch_dtype = torch.float16  # good default for 4-bit quant bases
        
        # ---- Load tokenizer from the base
        self.tokenizer = AutoTokenizer.from_pretrained(BASE_ID, use_fast=True, trust_remote_code=True)
        
        # ---- Load the 4-bit base (bitsandbytes)
        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_ID,
            device_map=self.device_map,
            torch_dtype=self.torch_dtype,
            trust_remote_code=True,
        )
        
        # ---- Attach the PEFT adapter
        if(ADAPTER_ID is None):
            self.model = base_model
        else:
            self.model = PeftModel.from_pretrained(base_model, ADAPTER_ID)
        self.model.eval()

    # ---- Simple Mistral-Instruct prompt helper
    def format_inst(self,content: str) -> str:
    # Mistral Instruct (v0.2) accepts [INST] ... [/INST] by default
        return f"<s>[INST] {content.strip()} [/INST]"
    
    # ---- Claim extraction helper
    def extract_claims(self,text: str,language: str = "english", max_new_tokens: int = 512, temperature: float = 0.1, top_p: float = 0.80):
        prompt = (
        "Extract clear, verifiable claims from the passage below. "
        f"Return them as a numbered list and in {language} language.\n\n"
        f"Passage:\n{text}"
        )
        input_ids = self.tokenizer(self.format_inst(prompt), return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            out = self.model.generate(
                **input_ids,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=temperature,
                top_p=top_p,
                repetition_penalty=1.1,
                eos_token_id=self.tokenizer.eos_token_id,
            )
        text_out = self.tokenizer.decode(out[0], skip_special_tokens=True)
        # Optional light parsing into a list of bullet points / numbers
        text = text_out.split("[/INST]",1)[1]
        claims = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            # naive: lines that look like numbered bullets or dashes
            if line[:1].isdigit() or line[:2].isdigit() or line.startswith(("-", "•")):
                # remove leading numbering like "1. " or "- "
                cleaned = line.lstrip("•-").lstrip()
                if cleaned and cleaned[0].isdigit():
                    # e.g., "1. claim"
                    cleaned = cleaned.split(".", 1)[-1].strip()
                claims.append(cleaned or line)
        return text_out, claims
    
