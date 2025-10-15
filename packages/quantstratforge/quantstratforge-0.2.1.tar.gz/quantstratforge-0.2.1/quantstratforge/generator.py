from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch
import os
import ast
import re
from pathlib import Path
from .utils import logger, add_watermark

class StrategyGenerator:
    def __init__(self, model_path=None):
        try:
            if model_path is None:
                possible_paths = [
                    "./quant-strat-forge",
                    "../quant-strat-forge",
                    os.path.expanduser("~/PycharmProjects/YadVansh/StratForge/quant-strat-forge"),
                    "/home/v/PycharmProjects/YadVansh/StratForge/quant-strat-forge"
                ]
                
                model_path = None
                for path in possible_paths:
                    abs_path = os.path.abspath(path)
                    if os.path.exists(abs_path):
                        model_path = abs_path
                        break
                
                if model_path is None:
                    model_path = "./quant-strat-forge"
            
            model_path = os.path.abspath(model_path)
            
            if not os.path.exists(model_path):
                error_msg = (
                    f"❌ Custom model not found at '{model_path}'.\n"
                    f"\n"
                    f"QuantStratForge uses ONLY your custom trained model.\n"
                    f"No external LLMs will be used.\n"
                    f"\n"
                    f"To train your model:\n"
                    f"  1. quantstratforge prepare     # Prepare training data\n"
                    f"  2. quantstratforge train       # Train model locally\n"
                    f"\n"
                    f"Or for federated learning:\n"
                    f"  2. quantstratforge train --federated  # Train with privacy-preserving FL\n"
                    f"\n"
                    f"After training, your model will be saved to: {model_path}"
                )
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            logger.info(f"🔄 Loading YOUR custom SLM model from: {model_path}")
            self.model_path = model_path
            
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                
                if torch.cuda.is_available():
                    from transformers import BitsAndBytesConfig
                    
                    quantization_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4"
                    )
                    
                    self.model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        quantization_config=quantization_config,
                        device_map="auto",
                        low_cpu_mem_usage=True
                    )
                else:
                    self.model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        torch_dtype=torch.float32,
                        device_map=None
                    )
                
                self.generator = pipeline(
                    "text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer
                )
                
                logger.info(f"✅ Custom SLM model loaded successfully from: {model_path}")
                logger.info(f"   Device: {'GPU' if torch.cuda.is_available() else 'CPU'}")
                
            except Exception as e:
                logger.error(f"Failed to load model from {model_path}: {e}")
                logger.error(f"Make sure the model was trained and saved correctly.")
                raise
                
                
        except Exception as e:
            logger.error(f"Generator initialization failure: {e}")
            raise

    def validate_strategy_code(self, code: str) -> tuple[bool, str]:
        try:
            if not code or len(code.strip()) < 20:
                return False, "Code is too short or empty"
            
            if "def strategy_func" not in code:
                return False, "Missing 'def strategy_func' function definition"
            
            ast.parse(code)
            
            if "return" not in code:
                return False, "Missing 'return' statement"
            
            return True, ""
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def extract_function_code(self, text: str) -> str:
        pattern = r'def strategy_func\([^)]*\):[^\n]*\n(?:(?:    |\t)[^\n]*\n)*'
        matches = re.findall(pattern, text, re.MULTILINE)
        
        if matches:
            code = max(matches, key=len)
            return code.strip()
        
        if "def strategy_func" in text:
            start = text.find("def strategy_func")
            rest = text[start:]
            lines = rest.split('\n')
            
            func_lines = [lines[0]]
            for i in range(1, len(lines)):
                line = lines[i]
                if line and not line.startswith((' ', '\t')):
                    if line.startswith('def ') or (not line.startswith('#')):
                        break
                func_lines.append(line)
            
            return '\n'.join(func_lines).strip()
        
        return ""

    def get_fallback_strategy(self, risk_level: str = "medium") -> str:
        strategies = {
            "low": """def strategy_func(df):
    df['MA_50'] = df['Close'].rolling(window=50).mean()
    df['MA_200'] = df['Close'].rolling(window=200).mean()
    signals = (df['MA_50'] > df['MA_200']).astype(int)
    return signals""",
            
            "medium": """def strategy_func(df):
    df['MA_20'] = df['Close'].rolling(window=20).mean()
    df['Returns'] = df['Close'].pct_change()
    df['Momentum'] = df['Returns'].rolling(window=10).mean()
    signals = ((df['Close'] > df['MA_20']) & (df['Momentum'] > 0)).astype(int)
    return signals""",
            
            "high": """def strategy_func(df):
    df['RSI'] = 100 - (100 / (1 + df['Close'].pct_change().rolling(14).mean() / df['Close'].pct_change().rolling(14).std().abs()))
    df['MA_10'] = df['Close'].rolling(window=10).mean()
    signals = ((df['RSI'] < 30) | (df['Close'] > df['MA_10'])).astype(int)
    return signals"""
        }
        
        return strategies.get(risk_level, strategies["medium"])

    def generate(self, input_data: str):
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            max_input_tokens = 1500
            tokens = self.tokenizer.encode(input_data, add_special_tokens=False)
            if len(tokens) > max_input_tokens:
                logger.warning(f"Input too long ({len(tokens)} tokens), truncating to {max_input_tokens}")
                tokens = tokens[:max_input_tokens]
                input_data = self.tokenizer.decode(tokens, skip_special_tokens=True)
            
            prompt = f"""### Instruction:
Generate a Python quantitative trading strategy function.

### Input Data:
{input_data[:500]}

### Required Output Format:
def strategy_func(df):
    return signals

### Strategy Code:
"""
            
            output = self.generator(
                prompt, 
                max_new_tokens=256,
                do_sample=True, 
                temperature=0.7,
                truncation=True,
                max_length=2048
            )[0]["generated_text"]
            
            try:
                generated = output.split("### Strategy Code:")[-1].strip()
                
                strategy = self.extract_function_code(generated)
                
                is_valid, error_msg = self.validate_strategy_code(strategy)
                
                if not is_valid:
                    logger.warning(f"Generated code validation failed: {error_msg}")
                    logger.warning(f"Generated code was: {strategy[:200]}...")
                    
                    risk_level = "medium"
                    if "Risk Level:" in input_data:
                        risk_match = re.search(r'Risk Level:\s*(low|medium|high)', input_data, re.IGNORECASE)
                        if risk_match:
                            risk_level = risk_match.group(1).lower()
                    
                    strategy = self.get_fallback_strategy(risk_level)
                    explanation = f"Using validated {risk_level}-risk strategy (AI generation failed validation: {error_msg})"
                else:
                    explanation = "AI-generated quantitative trading strategy (validated)"
                    
            except Exception as e:
                logger.warning(f"Code extraction failed: {e}")
                risk_level = "medium"
                if "Risk Level:" in input_data:
                    risk_match = re.search(r'Risk Level:\s*(low|medium|high)', input_data, re.IGNORECASE)
                    if risk_match:
                        risk_level = risk_match.group(1).lower()
                
                strategy = self.get_fallback_strategy(risk_level)
                explanation = f"Using validated {risk_level}-risk strategy (extraction error)"
            
            logger.info("Strategy generated successfully")
            return {"strategy_code": strategy, "explanation": add_watermark(explanation)}
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
        finally:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()