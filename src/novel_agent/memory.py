from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import deque
from loguru import logger

from src.novel_agent.state import NovelState, ChapterModel


class MemoryItem:
    def __init__(self, content: str, memory_type: str, importance: float = 0.5):
        self.content = content
        self.memory_type = memory_type
        self.importance = importance
        self.created_at = datetime.now()
        self.access_count = 0
        self.last_accessed = datetime.now()

    def access(self):
        self.access_count += 1
        self.last_accessed = datetime.now()


class ShortTermMemory:
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.items: deque = deque(maxlen=max_size)

    def add(self, item: MemoryItem):
        self.items.append(item)

    def get_recent(self, n: int = 10) -> List[MemoryItem]:
        items = list(self.items)[-n:]
        for item in items:
            item.access()
        return items

    def clear(self):
        self.items.clear()

    def __len__(self):
        return len(self.items)


class LongTermMemory:
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.items: Dict[str, MemoryItem] = {}

    def add(self, key: str, item: MemoryItem):
        if len(self.items) >= self.max_size:
            self._evict_least_important()
        self.items[key] = item

    def get(self, key: str) -> Optional[MemoryItem]:
        item = self.items.get(key)
        if item:
            item.access()
        return item

    def search(self, query: str, top_k: int = 5) -> List[MemoryItem]:
        query_lower = query.lower()
        scored_items = []

        for item in self.items.values():
            if query_lower in item.content.lower():
                score = item.importance * (1 + item.access_count * 0.1)
                scored_items.append((score, item))

        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored_items[:top_k]]

    def _evict_least_important(self):
        if not self.items:
            return

        min_item = min(self.items.values(), key=lambda x: x.importance)
        key_to_remove = None
        for key, item in self.items.items():
            if item is min_item:
                key_to_remove = key
                break

        if key_to_remove:
            del self.items[key_to_remove]

    def clear(self):
        self.items.clear()

    def __len__(self):
        return len(self.items)


class NovelMemory:
    def __init__(self, novel_id: str):
        self.novel_id = novel_id
        self.short_term = ShortTermMemory(max_size=50)
        self.long_term = LongTermMemory(max_size=500)
        self.character_memories: Dict[str, str] = {}
        self.plot_memories: List[str] = []
        self.world_memories: Dict[str, str] = {}
        self.created_at = datetime.now()

    def add_character_memory(self, character_name: str, memory: str):
        self.character_memories[character_name] = memory
        item = MemoryItem(
            content=f"Character {character_name}: {memory}",
            memory_type="character",
            importance=0.8
        )
        key = f"char_{character_name}_{datetime.now().timestamp()}"
        self.long_term.add(key, item)

    def add_plot_memory(self, plot_point: str):
        self.plot_memories.append(plot_point)
        item = MemoryItem(
            content=plot_point,
            memory_type="plot",
            importance=0.9
        )
        key = f"plot_{len(self.plot_memories)}"
        self.long_term.add(key, item)

    def add_world_memory(self, key: str, memory: str):
        self.world_memories[key] = memory
        item = MemoryItem(
            content=f"World {key}: {memory}",
            memory_type="world",
            importance=0.7
        )
        self.long_term.add(f"world_{key}", item)

    def get_character_context(self, character_name: str) -> Optional[str]:
        return self.character_memories.get(character_name)

    def get_recent_plots(self, n: int = 5) -> List[str]:
        return self.plot_memories[-n:]

    def get_full_plot_summary(self) -> str:
        return "\n".join([f"{i+1}. {p}" for i, p in enumerate(self.plot_memories)])

    def search_memories(self, query: str) -> List[Dict[str, Any]]:
        results = self.long_term.search(query, top_k=10)

        character_matches = []
        for name, memory in self.character_memories.items():
            if query.lower() in memory.lower():
                character_matches.append({"type": "character", "name": name, "content": memory})

        world_matches = []
        for key, memory in self.world_memories.items():
            if query.lower() in memory.lower():
                world_matches.append({"type": "world", "key": key, "content": memory})

        return {
            "long_term_hits": [{"content": r.content, "type": r.memory_type} for r in results],
            "character_matches": character_matches,
            "world_matches": world_matches
        }

    def consolidate_to_long_term(self):
        recent_items = self.short_term.get_recent(20)
        for item in recent_items:
            if item.importance > 0.6:
                key = f"{item.memory_type}_{datetime.now().timestamp()}"
                self.long_term.add(key, item)

        logger.info(f"Consolidated {len(recent_items)} items to long-term memory")


class MemoryManager:
    def __init__(self):
        self.novel_memories: Dict[str, NovelMemory] = {}
        self._knowledge_items: Dict[str, Dict[str, Any]] = {}

    def get_or_create_memory(self, novel_id: str) -> NovelMemory:
        if novel_id not in self.novel_memories:
            self.novel_memories[novel_id] = NovelMemory(novel_id)
        return self.novel_memories[novel_id]

    def add_knowledge(self, content: str, category: str, source: str = "unknown"):
        key = f"{category}:{hash(content) & 0x7FFFFFFF}"
        self._knowledge_items[key] = {
            "content": content,
            "category": category,
            "source": source,
            "added_at": datetime.now().isoformat()
        }
        logger.debug(f"Knowledge stored: {category} from {source}")

    def delete_memory(self, novel_id: str):
        if novel_id in self.novel_memories:
            del self.novel_memories[novel_id]

    def get_memory_summary(self, novel_id: str) -> Dict[str, Any]:
        memory = self.get_or_create_memory(novel_id)
        return {
            "novel_id": novel_id,
            "short_term_size": len(memory.short_term),
            "long_term_size": len(memory.long_term),
            "character_count": len(memory.character_memories),
            "plot_points": len(memory.plot_memories),
            "world_facts": len(memory.world_memories)
        }


_global_memory_manager = MemoryManager()


def get_memory_manager() -> MemoryManager:
    return _global_memory_manager
