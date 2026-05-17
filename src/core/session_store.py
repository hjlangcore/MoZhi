import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from src.novel_agent.state import SessionModel, NovelState, SessionStore
from loguru import logger


class FileSessionStore(SessionStore):
    def __init__(self, storage_dir: str = "./data"):
        super().__init__()
        self.storage_dir = Path(storage_dir)
        self.sessions_file = self.storage_dir / "sessions.json"
        self.novels_file = self.storage_dir / "novels.json"
        self._ensure_storage_dir()
        self._load_data()

    def _ensure_storage_dir(self):
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _load_data(self):
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for session_data in data:
                        session = SessionModel(**session_data)
                        self._sessions[session.session_id] = session
                logger.info(f"Loaded {len(self._sessions)} sessions from disk")
            except Exception as e:
                logger.error(f"Failed to load sessions: {e}")

        if self.novels_file.exists():
            try:
                with open(self.novels_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for novel_data in data:
                        novel = NovelState(**novel_data)
                        self._novels[novel.novel_id] = novel
                logger.info(f"Loaded {len(self._novels)} novels from disk")
            except Exception as e:
                logger.error(f"Failed to load novels: {e}")

    def _save_sessions(self):
        try:
            data = [session.model_dump() for session in self._sessions.values()]
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")

    def _save_novels(self):
        try:
            data = [novel.model_dump() for novel in self._novels.values()]
            with open(self.novels_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save novels: {e}")

    def create_session(self, session_name: str) -> SessionModel:
        session = super().create_session(session_name)
        self._save_sessions()
        logger.info(f"Created session: {session.session_id}")
        return session

    def update_session(self, session_id: str, **kwargs) -> Optional[SessionModel]:
        session = super().update_session(session_id, **kwargs)
        if session:
            self._save_sessions()
        return session

    def delete_session(self, session_id: str) -> bool:
        success = super().delete_session(session_id)
        if success:
            self._save_sessions()
            self._save_novels()
        return success

    def create_novel(self, session_id: str, theme: str, style_type: str = "凡人流") -> Optional[NovelState]:
        novel = super().create_novel(session_id, theme, style_type)
        if novel:
            self._save_novels()
            self._save_sessions()
        return novel

    def update_novel(self, novel_id: str, **kwargs) -> Optional[NovelState]:
        novel = super().update_novel(novel_id, **kwargs)
        if novel:
            self._save_novels()
        return novel

    def add_chapter(self, novel_id: str, chapter) -> bool:
        success = super().add_chapter(novel_id, chapter)
        if success:
            self._save_novels()
        return success

    def delete_novel(self, novel_id: str) -> bool:
        success = super().delete_novel(novel_id)
        if success:
            self._save_novels()
        return success

    def add_foreshadowing(self, novel_id: str, foreshadowing) -> bool:
        success = super().add_foreshadowing(novel_id, foreshadowing)
        if success:
            self._save_novels()
        return success

    def resolve_foreshadowing(self, novel_id: str, seed: str) -> bool:
        success = super().resolve_foreshadowing(novel_id, seed)
        if success:
            self._save_novels()
        return success


_file_store = None


def get_session_store() -> FileSessionStore:
    global _file_store
    if _file_store is None:
        _file_store = FileSessionStore()
    return _file_store
