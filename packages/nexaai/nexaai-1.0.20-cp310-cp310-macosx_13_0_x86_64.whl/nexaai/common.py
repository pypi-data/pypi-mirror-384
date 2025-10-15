from dataclasses import dataclass
from typing import TypedDict, Literal, Optional, List
from enum import Enum


class PluginID(str, Enum):
    """Enum for plugin identifiers."""
    MLX = "mlx"
    LLAMA_CPP = "llama_cpp"
    NEXAML = "nexaml"


class ChatMessage(TypedDict):
    role: Literal["user", "assistant", "system"]
    content: str

class MultiModalMessageContent(TypedDict):
    type: Literal["text", "image", "audio", "video"]
    text: Optional[str]
    url: Optional[str]
    path: Optional[str]

class MultiModalMessage(TypedDict):
    role: Literal["user", "assistant", "system"]
    content: List[MultiModalMessageContent] 


@dataclass
class SamplerConfig:
    temperature: float = 0.8
    top_p: float = 0.95
    top_k: int = 40
    repetition_penalty: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    seed: int = -1
    grammar_path: str = None
    grammar_string: str = None

@dataclass
class GenerationConfig:
    max_tokens: int = 1024
    stop_words: list[str] = None
    sampler_config: SamplerConfig = None
    image_paths: list[str] = None
    audio_paths: list[str] = None

@dataclass
class ModelConfig:
    n_ctx: int = 4096
    n_threads: int = None
    n_threads_batch: int = None
    n_batch: int = 512
    n_ubatch: int = 512
    n_seq_max: int = 1
    n_gpu_layers: int = 999
    chat_template_path: str = None
    chat_template_content: str = None


@dataclass(frozen=True) # Read-only
class ProfilingData:
    """Profiling data structure for LLM/VLM performance metrics."""
    ttft: int = 0             # Time to first token (us)
    prompt_time: int = 0      # Prompt processing time (us)
    decode_time: int = 0      # Token generation time (us)
    prompt_tokens: int = 0    # Number of prompt tokens
    generated_tokens: int = 0  # Number of generated tokens
    audio_duration: int = 0   # Audio duration (us)
    prefill_speed: float = 0.0  # Prefill speed (tokens/sec)
    decoding_speed: float = 0.0 # Decoding speed (tokens/sec)
    real_time_factor: float = 0.0 # Real-Time Factor (RTF)
    stop_reason: str = ""     # Stop reason: "eos", "length", "user", "stop_sequence"
    
    @classmethod
    def from_dict(cls, data: dict) -> "ProfilingData":
        """Create ProfilingData from dictionary."""
        return cls(
            ttft=data.get("ttft", 0),
            prompt_time=data.get("prompt_time", 0),
            decode_time=data.get("decode_time", 0),
            prompt_tokens=data.get("prompt_tokens", 0),
            generated_tokens=data.get("generated_tokens", 0),
            audio_duration=data.get("audio_duration", 0),
            prefill_speed=data.get("prefill_speed", 0.0),
            decoding_speed=data.get("decoding_speed", 0.0),
            real_time_factor=data.get("real_time_factor", 0.0),
            stop_reason=data.get("stop_reason", "")
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "ttft": self.ttft,
            "prompt_time": self.prompt_time,
            "decode_time": self.decode_time,
            "prompt_tokens": self.prompt_tokens,
            "generated_tokens": self.generated_tokens,
            "audio_duration": self.audio_duration,
            "prefill_speed": self.prefill_speed,
            "decoding_speed": self.decoding_speed,
            "real_time_factor": self.real_time_factor,
            "stop_reason": self.stop_reason
        }
