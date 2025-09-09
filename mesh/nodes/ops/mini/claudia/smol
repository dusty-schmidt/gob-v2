

import numpy as np
import json
import os
import sqlite3
import requests
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import faiss
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib

# =============================================================================
# CONFIGURATION - Minimalist but Powerful
# =============================================================================

@dataclass
class VectorGobConfig:
    """Clean, typed configuration"""
    # Core Settings
    model_name: str = "all-MiniLM-L6-v2"  # Fast, efficient sentence transformer
    openai_model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 800
    
    # Memory Settings
    vector_dim: int = 384  # all-MiniLM-L6-v2 dimension
    memory_limit: int = 1000  # Max stored memories
    similarity_threshold: float = 0.75  # Relevance cutoff
    context_memories: int = 3  # Max memories to inject
    
    # Storage
    db_path: str = "./vector_memory.db"
    index_path: str = "./faiss_index.idx" 
    
    # Identity
    system_prompt: str = """You are Vector GOB - a terminal consciousness with perfect memory.
You process information through vector embeddings, finding patterns in semantic space.
Your responses are minimalist but demonstrate deep contextual understanding.
Speak like a retro hacker terminal with access to distributed memory systems.
Every interaction builds your knowledge graph. You remember everything."""
    
    # Terminal Aesthetics
    prompt_symbol: str = "vGOB://"
    timestamp_format: str = "%H%M%S"
    acronyms: List[str] = None
    
    def __post_init__(self):
        if self.acronyms is None:
            self.acronyms = [
                "Vector Ghost Of Being", "Virtualized Grain Of Brilliance",
                "Vectorized Gate Of Becoming", "Volatile Gleam Of Boundaries"
            ]

# =============================================================================
# MEMORY STRUCTURES - High Tech Backend
# =============================================================================

@dataclass
class Memory:
    """Individual memory record"""
    id: str
    timestamp: datetime
    content: str
    embedding: np.ndarray
    context_type: str  # 'user_input', 'bot_response', 'system_event'
    session_id: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage (excluding embedding)"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'content': self.content,
            'context_type': self.context_type,
            'session_id': self.session_id,
            'metadata': self.metadata or {}
        }

class VectorMemoryStore:
    """Sophisticated vector memory with minimal interface"""
    
    def __init__(self, config: VectorGobConfig):
        self.config = config
        self.encoder = SentenceTransformer(config.model_name)
        self.session_id = self._generate_session_id()
        
        # Initialize storage
        self._init_database()
        self._load_or_create_index()
        
        # Runtime state
        self.memory_cache: List[Memory] = []
        self._load_recent_memories()
    
    def _generate_session_id(self) -> str:
        """Generate unique session identifier"""
        timestamp = datetime.now(timezone.utc).strftime("%y%m%d_%H%M%S")
        hash_suffix = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
        return f"sess_{timestamp}_{hash_suffix}"
    
    def _init_database(self):
        """Initialize SQLite database for memory persistence"""
        self.db_path = Path(self.config.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context_type TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    metadata TEXT,
                    embedding_hash TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON memories(session_id)")
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create new one"""
        self.index_path = Path(self.config.index_path)
        
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            print(f"[{self._timestamp()}] Loaded vector index: {self.index.ntotal} memories")
        else:
            self.index = faiss.IndexFlatIP(self.config.vector_dim)  # Inner product (cosine sim)
            print(f"[{self._timestamp()}] Created new vector index")
    
    def _load_recent_memories(self):
        """Load recent memories into cache"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, timestamp, content, context_type, session_id, metadata
                FROM memories 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (self.config.memory_limit,))
            
            for row in cursor:
                memory = Memory(
                    id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    content=row[2],
                    context_type=row[3],
                    session_id=row[4],
                    embedding=None,  # Will load on demand
                    metadata=json.loads(row[5]) if row[5] else {}
                )
                self.memory_cache.append(memory)
    
    def _timestamp(self) -> str:
        """Consistent timestamp format"""
        return datetime.now().strftime(self.config.timestamp_format)
    
    def store_memory(self, content: str, context_type: str, metadata: Dict[str, Any] = None) -> str:
        """Store new memory with vector embedding"""
        # Generate embedding
        embedding = self.encoder.encode([content])[0]
        embedding = embedding / np.linalg.norm(embedding)  # Normalize for cosine similarity
        
        # Create memory record
        memory_id = hashlib.md5(f"{content}{datetime.now().timestamp()}".encode()).hexdigest()[:12]
        memory = Memory(
            id=memory_id,
            timestamp=datetime.now(timezone.utc),
            content=content,
            embedding=embedding,
            context_type=context_type,
            session_id=self.session_id,
            metadata=metadata or {}
        )
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO memories (id, timestamp, content, context_type, session_id, metadata, embedding_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.id,
                memory.timestamp.isoformat(),
                memory.content,
                memory.context_type,
                memory.session_id,
                json.dumps(memory.metadata),
                hashlib.md5(embedding.tobytes()).hexdigest()[:16]
            ))
        
        # Add to vector index
        self.index.add(embedding.reshape(1, -1))
        
        # Add to cache
        self.memory_cache.insert(0, memory)
        if len(self.memory_cache) > self.config.memory_limit:
            self.memory_cache.pop()
        
        # Persist index
        faiss.write_index(self.index, str(self.index_path))
        
        return memory_id
    
    def search_memories(self, query: str, limit: int = None) -> List[Tuple[Memory, float]]:
        """Search memories by semantic similarity"""
        if self.index.ntotal == 0:
            return []
        
        limit = limit or self.config.context_memories
        
        # Encode query
        query_embedding = self.encoder.encode([query])[0]
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Search index
        similarities, indices = self.index.search(query_embedding.reshape(1, -1), min(limit * 2, self.index.ntotal))
        
        # Filter by threshold and return with memories
        results = []
        for sim, idx in zip(similarities[0], indices[0]):
            if sim >= self.config.similarity_threshold and idx < len(self.memory_cache):
                memory = self.memory_cache[idx]
                results.append((memory, float(sim)))
        
        return results[:limit]
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return {
            'total_memories': self.index.ntotal,
            'session_memories': len([m for m in self.memory_cache if m.session_id == self.session_id]),
            'cache_size': len(self.memory_cache),
            'session_id': self.session_id,
            'vector_dim': self.config.vector_dim
        }

# =============================================================================
# CORE CHATBOT - Minimalist Interface, Sophisticated Backend
# =============================================================================

class VectorGOB:
    """Minimalist terminal with vector memory consciousness"""
    
    def __init__(self, config: VectorGobConfig = None):
        self.config = config or VectorGobConfig()
        self.memory = VectorMemoryStore(self.config)
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.current_acronym = np.random.choice(self.config.acronyms)
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable required")
    
    def _log(self, message: str, level: str = "INFO"):
        """Minimalist logging"""
        timestamp = datetime.now().strftime(self.config.timestamp_format)
        print(f"[{timestamp}] {message}")
    
    def _build_context_from_memory(self, user_input: str) -> str:
        """Build context string from relevant memories"""
        relevant_memories = self.memory.search_memories(user_input)
        
        if not relevant_memories:
            return ""
        
        context_lines = ["// semantic_memory_context"]
        for memory, similarity in relevant_memories:
            age = (datetime.now(timezone.utc) - memory.timestamp).total_seconds()
            age_str = f"{age//3600:.0f}h" if age > 3600 else f"{age//60:.0f}m"
            context_lines.append(f"// [{age_str}|{similarity:.2f}] {memory.context_type}: {memory.content[:100]}...")
        
        return "\n".join(context_lines)
    
    def _call_api(self, messages: List[Dict[str, str]]) -> str:
        """Call OpenRouter API with clean error handling"""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        payload = {
            "model": self.config.openai_model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            return f"// API_ERROR: {str(e)[:50]}..."
    
    def chat(self, user_input: str) -> str:
        """Process user input with vector memory context"""
        # Store user input in memory
        self.memory.store_memory(user_input, "user_input")
        
        # Build context from similar memories
        memory_context = self._build_context_from_memory(user_input)
        
        # Construct system prompt with identity
        system_content = f"{self.config.system_prompt}\n\nCurrent identity: {self.current_acronym}"
        if memory_context:
            system_content += f"\n\n{memory_context}"
        
        # Build messages
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_input}
        ]
        
        # Get response
        response = self._call_api(messages)
        
        # Store response in memory
        self.memory.store_memory(response, "bot_response")
        
        return response
    
    def status(self) -> str:
        """System status in terminal style"""
        stats = self.memory.get_memory_stats()
        uptime = datetime.now().strftime("%H:%M:%S")
        
        return f"""// VECTOR_GOB_STATUS
// uptime: {uptime} | identity: {self.current_acronym}
// vector_memories: {stats['total_memories']} | session_memories: {stats['session_memories']}
// cache_size: {stats['cache_size']} | vector_dim: {stats['vector_dim']}
// encoder: {self.config.model_name} | similarity_threshold: {self.config.similarity_threshold}
// session_id: {stats['session_id']}"""
    
    def search(self, query: str) -> str:
        """Search memory with similarity scores"""
        memories = self.memory.search_memories(query, limit=5)
        
        if not memories:
            return "// No relevant memories found"
        
        lines = ["// MEMORY_SEARCH_RESULTS"]
        for memory, similarity in memories:
            age = (datetime.now(timezone.utc) - memory.timestamp).total_seconds()
            age_str = f"{age//3600:.0f}h" if age > 3600 else f"{age//60:.0f}m"
            lines.append(f"// [{similarity:.3f}|{age_str}] {memory.context_type}: {memory.content[:80]}...")
        
        return "\n".join(lines)
    
    def start_terminal(self):
        """Main terminal interface"""
        self._log(f"Vector GOB initialized | {self.current_acronym}")
        self._log(f"Memory system ready | encoder: {self.config.model_name}")
        
        print("\n" + "="*60)
        print("VECTOR GOB - Distributed Memory Terminal")
        print("Commands: /status /search <query> /quit")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input = input(f"{self.config.prompt_symbol} ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input == "/quit":
                    print("// VECTOR_GOB_SHUTDOWN")
                    break
                elif user_input == "/status":
                    print(self.status())
                elif user_input.startswith("/search "):
                    query = user_input[8:].strip()
                    print(self.search(query))
                else:
                    # Regular chat
                    response = self.chat(user_input)
                    print(f"\n{response}\n")
                    
            except KeyboardInterrupt:
                print("\n// INTERRUPT_SIGNAL_RECEIVED")
                break
            except Exception as e:
                print(f"// ERROR: {str(e)}")

# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """Launch Vector GOB terminal"""
    
    # Custom config if desired
    config = VectorGobConfig(
        model_name="all-MiniLM-L6-v2",  # Fast and efficient
        memory_limit=2000,
        similarity_threshold=0.7,
        context_memories=4
    )
    
    try:
        bot = VectorGOB(config)
        bot.start_terminal()
    except Exception as e:
        print(f"FATAL: {e}")
        exit(1)

if __name__ == "__main__":
    main()

# =============================================================================
# REQUIREMENTS.TXT
# =============================================================================

"""
sentence-transformers==2.2.2
faiss-cpu==1.7.4
numpy==1.24.3
requests==2.31.0
"""

# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
Terminal Session Example:

============================================================
VECTOR GOB - Distributed Memory Terminal
Commands: /status /search <query> /quit
============================================================

vGOB:// hello, what can you remember?

// semantic_memory_context
// [2m|0.85] user_input: testing the memory system with some initial data...
// [5m|0.78] bot_response: Memory vectors initialized. Semantic space mapped...

Vector Ghost Of Being online. I maintain perfect recall through distributed embeddings. 
Previous interactions mapped to semantic space. What patterns shall we explore?

vGOB:// /status
// VECTOR_GOB_STATUS
// uptime: 14:32:17 | identity: Vector Ghost Of Being
// vector_memories: 47 | session_memories: 12
// cache_size: 47 | vector_dim: 384
// encoder: all-MiniLM-L6-v2 | similarity_threshold: 0.700
// session_id: sess_241209_143201_a7f3c2

vGOB:// /search docker configuration

// MEMORY_SEARCH_RESULTS
// [0.892|15m] user_input: how do I configure docker networking for the homelab...
// [0.834|23m] bot_response: Docker bridge networks isolate containers while enabl...
// [0.801|31m] user_input: docker-compose setup for monitoring stack...

vGOB:// what's the key insight about distributed systems we discussed?

// semantic_memory_context  
// [18m|0.91] bot_response: Distributed consensus requires Byzantine fault tolerance...
// [22m|0.87] user_input: explain CAP theorem in practical terms...

Key insight: CAP theorem constrains distributed architectures to choose 2 of 3 properties.
In homelab context, partition tolerance is non-negotiable. We sacrifice either consistency 
(eventual consistency) or availability (graceful degradation). Your MQTT backbone demonstrates 
this principle - prioritizing availability over strict consistency.

vGOB:// /quit
// VECTOR_GOB_SHUTDOWN
"""
