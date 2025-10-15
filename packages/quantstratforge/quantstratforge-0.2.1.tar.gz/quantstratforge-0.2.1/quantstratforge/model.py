import torch
import os
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model
import flwr as fl
from datasets import load_from_disk
from .utils import logger

class StrategyModel:
    def __init__(self, model_name="microsoft/phi-2", lora_r=16):
        self.model_name = model_name
        self.lora_r = lora_r
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = None
        self.dataset = None

    def load_model(self):
        try:
            logger.info(f"Loading base model: {self.model_name}")
            
            has_cuda = False
            try:
                has_cuda = torch.cuda.is_available() and torch.cuda.device_count() > 0
            except Exception as cuda_error:
                logger.warning(f"CUDA check failed: {cuda_error}")
                has_cuda = False
            
            logger.info(f"CUDA available: {has_cuda}")
            
            if has_cuda:
                logger.info("Loading model with 8-bit quantization on GPU...")
                try:
                    model = AutoModelForCausalLM.from_pretrained(
                        self.model_name, 
                        load_in_8bit=True, 
                        device_map="auto",
                        trust_remote_code=True
                    )
                except Exception as gpu_error:
                    logger.warning(f"GPU loading failed: {gpu_error}")
                    logger.info("Falling back to CPU...")
                    has_cuda = False
            
            if not has_cuda:
                logger.info("Loading model on CPU (this will use more RAM)...")
                logger.info("⚠️  Training on CPU will be SLOW (4-8 hours). Consider using GPU or smaller model.")
                model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True,
                    trust_remote_code=True
                )
            
            logger.info("Applying LoRA adapters...")
            lora_config = LoraConfig(
                r=self.lora_r, 
                lora_alpha=32, 
                target_modules=["q_proj", "v_proj"], 
                lora_dropout=0.05, 
                bias="none", 
                task_type="CAUSAL_LM"
            )
            
            peft_model = get_peft_model(model, lora_config)
            
            peft_model.enable_input_require_grads()
            
            logger.info(f"✅ Model loaded successfully with LoRA (rank={self.lora_r})")
            
            return peft_model
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            logger.error("Tip: Try using a smaller model like 'gpt2' or 'gpt2-medium'")
            raise

    def tokenize_function(self, examples):
        tokenized = self.tokenizer(examples["text"], truncation=True, padding="max_length", max_length=512)
        tokenized["labels"] = [input_ids[:] for input_ids in tokenized["input_ids"]]
        return tokenized

    def prepare_for_training(self, data_path="./formatted_data"):
        try:
            logger.info(f"Loading dataset from: {data_path}")
            self.dataset = load_from_disk(data_path)
            
            logger.info("Tokenizing dataset...")
            tokenized_dataset = self.dataset.map(self.tokenize_function, batched=True)
            
            columns_to_remove = [col for col in ["text", "label", "sentence"] if col in tokenized_dataset.column_names]
            if columns_to_remove:
                logger.info(f"Removing columns: {columns_to_remove}")
                tokenized_dataset = tokenized_dataset.remove_columns(columns_to_remove)
            
            tokenized_dataset.set_format("torch")
            logger.info(f"✅ Dataset prepared for training ({len(tokenized_dataset)} examples)")
            return tokenized_dataset
        except Exception as e:
            logger.error(f"Training preparation failed: {e}")
            raise

    def get_training_args(self, output_dir="./quant-strat-forge", epochs=3):
        return TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=8,
            warmup_steps=100,
            learning_rate=2e-4,
            fp16=True if torch.cuda.is_available() else False,
            logging_steps=10,
            save_steps=500,
            eval_strategy="no",
            remove_unused_columns=False,
            gradient_checkpointing=True,
        )

    def train_local(self, data_path="./formatted_data", epochs=3):
        try:
            tokenized_dataset = self.prepare_for_training(data_path)
            self.model = self.load_model()
            args = self.get_training_args()
            
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer,
                mlm=False
            )
            
            trainer = Trainer(
                model=self.model, 
                args=args, 
                train_dataset=tokenized_dataset,
                data_collator=data_collator
            )
            
            checkpoint_dir = "./quant-strat-forge"
            resume_checkpoint = None
            if os.path.isdir(checkpoint_dir):
                checkpoints = [
                    os.path.join(checkpoint_dir, d) 
                    for d in os.listdir(checkpoint_dir) 
                    if d.startswith("checkpoint-") and os.path.isdir(os.path.join(checkpoint_dir, d))
                ]
                if checkpoints:
                    latest_checkpoint = max(checkpoints, key=lambda x: int(x.split("-")[-1]))
                    resume_checkpoint = latest_checkpoint
                    logger.info(f"🔄 Resuming training from checkpoint: {resume_checkpoint}")
            
            trainer.train(resume_from_checkpoint=resume_checkpoint)
            
            self.model.save_pretrained("./quant-strat-forge")
            self.tokenizer.save_pretrained("./quant-strat-forge")
            logger.info("Local training done!")
        except Exception as e:
            logger.error(f"Local training failed: {e}")
            raise

    def federated_train(self, num_clients=3, num_rounds=3, data_path="./formatted_data"):
        try:
            tokenized_dataset = self.prepare_for_training(data_path)
            client_datasets = [tokenized_dataset.shard(num_clients, i) for i in range(num_clients)]

            class QuantClient(fl.client.NumPyClient):
                def __init__(self, cid, trainset, model_loader, args_getter):
                    self.model = model_loader()
                    self.trainset = trainset
                    self.training_args = args_getter()
                    self.trainer = Trainer(model=self.model, args=self.training_args, train_dataset=self.trainset)

                def get_parameters(self, config):
                    return [val.cpu().numpy() for _, val in self.model.state_dict().items()]

                def set_parameters(self, parameters):
                    params_dict = zip(self.model.state_dict().keys(), parameters)
                    state_dict = {k: torch.tensor(v) for k, v in params_dict}
                    self.model.load_state_dict(state_dict, strict=False)

                def fit(self, parameters, config):
                    self.set_parameters(parameters)
                    self.trainer.train()
                    return self.get_parameters(config={}), len(self.trainset), {}

            def client_fn(cid: str):
                return QuantClient(cid, client_datasets[int(cid)], self.load_model, self.get_training_args)

            fl.simulation.start_simulation(
                client_fn=client_fn,
                num_clients=num_clients,
                client_resources={"num_cpus": 2, "num_gpus": 0.5 if torch.cuda.is_available() else 0},
                strategy=fl.server.strategy.FedAvg(),
                num_rounds=num_rounds
            )

            self.model = self.load_model()
            self.model.save_pretrained("./quant-strat-forge")
            self.tokenizer.save_pretrained("./quant-strat-forge")
            logger.info("Federated training completed!")
        except Exception as e:
            logger.error(f"Federated training failed: {e}")
            raise