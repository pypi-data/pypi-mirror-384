#context_manager.py

from typing import Dict, List, Optional, Any
import asyncio
from datetime import datetime, timezone
import uuid
import json
import os
import redis.asyncio as redis
import logging
from typing import Dict, Any, Optional, List
import hashlib

from ...utils.logger import logger, log_operation
from ...storage.db.operations import DatabaseOperations
from ...storage.db.models import ResearchSession
from .synthesizer import ResearchSynthesizer

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_timestamp() -> str:
    return _utc_now().isoformat()

class ResearchContextManager:
    """
    Manages research context and provides real-time streaming updates.
    """
    
    def __init__(self, db_ops: DatabaseOperations, synthesizer: ResearchSynthesizer, redis_url: str):
        self.db = db_ops
        self.synthesizer = synthesizer
        self.redis_client = redis.from_url(redis_url)
        self.active_sessions: Dict[str, Dict] = {}
        self.stream_subscribers: Dict[str, List[asyncio.Queue]] = {}
        
    async def create_research_session(self, user_id: str, topic: str, research_questions: List[str]) -> str:
        """Create a new research session with streaming support."""
        session_id = hashlib.md5(f"{user_id}_{topic}_{_utc_timestamp()}".encode()).hexdigest()

        session_data = {
            "id": session_id,
            "user_id": user_id,
            "topic": topic,
            "research_questions": json.dumps(research_questions),  # Convert list to JSON string
            "status": "initialized",
            "progress": 0.0,
            "current_step": "Initializing research session",
            "papers": json.dumps([]),  # Convert list to JSON string
            "notes": json.dumps([]),  # Convert list to JSON string
            "created_at": _utc_timestamp(),
            "updated_at": _utc_timestamp(),
            "synthesis": "",  # Convert None to empty string
            "error": ""  # Convert None to empty string
        }

        # Store in Redis for persistence
        await self.redis_client.hset(f"research_session:{session_id}", mapping=session_data)

        # Store in memory with proper types
        self.active_sessions[session_id] = {
            "id": session_id,
            "user_id": user_id,
            "topic": topic,
            "research_questions": research_questions,
            "status": "initialized",
            "progress": 0.0,
            "current_step": "Initializing research session",
            "papers": [],
            "notes": [],
            "created_at": _utc_timestamp(),
            "updated_at": _utc_timestamp(),
            "synthesis": None,
            "error": None
        }
        self.stream_subscribers[session_id] = []

        # Send initial update
        await self._broadcast_update(session_id, {
            "type": "session_created",
            "session_id": session_id,
            "data": self.active_sessions[session_id]
        })

        logger.info(f"Created research session {session_id} for user {user_id}")
        return session_id
    
    async def update_session_status(self, session_id: str, status: str, message: str, progress: Optional[float] = None):
        """Update session status and broadcast to subscribers."""
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return
            
        session = self.active_sessions[session_id]
        session["status"] = status
        session["current_step"] = message
        session["updated_at"] = _utc_timestamp()
        
        if progress is not None:
            session["progress"] = progress
            
        # Update Redis with serialized data
        redis_data = {
            "status": status,
            "current_step": message,
            "updated_at": session["updated_at"],
            "papers": json.dumps(session["papers"]),
            "notes": json.dumps(session["notes"]),
            "research_questions": json.dumps(session["research_questions"])
        }
        if progress is not None:
            redis_data["progress"] = progress
            
        await self.redis_client.hset(f"research_session:{session_id}", mapping=redis_data)
        
        # Broadcast update
        update_data = {
            "type": "status_update",
            "session_id": session_id,
            "status": status,
            "message": message,
            "progress": session["progress"],
            "timestamp": _utc_timestamp()
        }
        await self._broadcast_update(session_id, update_data)
        
        logger.info(f"Session {session_id} status: {status} - {message}")
    
    async def add_paper_to_session(self, session_id: str, paper_id: str, paper_info: Dict[str, Any]):
        """Add a paper to the session and broadcast update."""
        if session_id not in self.active_sessions:
            return
            
        session = self.active_sessions[session_id]
        session["papers"].append(paper_id)
        session["updated_at"] = _utc_timestamp()
        
        # Update Redis
        await self.redis_client.hset(f"research_session:{session_id}", mapping=session)
        
        # Broadcast paper addition
        await self._broadcast_update(session_id, {
            "type": "paper_added",
            "session_id": session_id,
            "paper_id": paper_id,
            "paper_info": paper_info,
            "total_papers": len(session["papers"]),
            "timestamp": _utc_timestamp()
        })
    
    async def update_session_synthesis(self, session_id: str, synthesis: Dict[str, Any]):
        """Update session with synthesis results and broadcast."""
        if session_id not in self.active_sessions:
            return
            
        session = self.active_sessions[session_id]
        session["synthesis"] = synthesis
        session["status"] = "completed"
        session["progress"] = 100.0
        session["updated_at"] = _utc_timestamp()
        
        # Update Redis
        await self.redis_client.hset(f"research_session:{session_id}", mapping=session)
        
        # Broadcast synthesis completion
        await self._broadcast_update(session_id, {
            "type": "synthesis_complete",
            "session_id": session_id,
            "synthesis_summary": {
                "paper_count": synthesis.get("meta", {}).get("paper_count", 0),
                "findings_count": len(synthesis.get("common_findings", [])),
                "gaps_count": len(synthesis.get("research_gaps", [])),
                "contradictions_count": len(synthesis.get("contradictions", []))
            },
            "timestamp": _utc_timestamp()
        })
    
    async def subscribe_to_updates(self, session_id: str) -> asyncio.Queue:
        """Subscribe to real-time updates for a session."""
        if session_id not in self.stream_subscribers:
            self.stream_subscribers[session_id] = []
            
        queue = asyncio.Queue()
        self.stream_subscribers[session_id].append(queue)
        
        # Send current session state
        if session_id in self.active_sessions:
            await queue.put({
                "type": "session_state",
                "session_id": session_id,
                "data": self.active_sessions[session_id]
            })
        
        logger.info(f"New subscriber added to session {session_id}")
        return queue
    
    async def unsubscribe_from_updates(self, session_id: str, queue: asyncio.Queue):
        """Unsubscribe from session updates."""
        if session_id in self.stream_subscribers:
            try:
                self.stream_subscribers[session_id].remove(queue)
            except ValueError:
                pass
    
    async def _broadcast_update(self, session_id: str, update: Dict[str, Any]):
        """Broadcast update to all subscribers."""
        if session_id not in self.stream_subscribers:
            return
            
        # Send to Redis pub/sub for cross-process communication
        await self.redis_client.publish(f"research_updates:{session_id}", json.dumps(update))
        
        # Send to local subscribers
        dead_queues = []
        for queue in self.stream_subscribers[session_id]:
            try:
                await queue.put(update)
            except Exception as e:
                logger.warning(f"Failed to send update to subscriber: {e}")
                dead_queues.append(queue)
        
        # Clean up dead queues
        for queue in dead_queues:
            try:
                self.stream_subscribers[session_id].remove(queue)
            except ValueError:
                pass
    
    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session status."""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Try to load from Redis
        try:
            session_data = await self.redis_client.hgetall(f"research_session:{session_id}")
            if session_data:
                return session_data
        except Exception as e:
            logger.error(f"Error loading session from Redis: {e}")
        
        return None
    
    async def list_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """List all sessions for a user."""
        sessions = []
        for session_id, session_data in self.active_sessions.items():
            if session_data.get("user_id") == user_id:
                sessions.append(session_data)
        return sessions
    
    async def cleanup_session(self, session_id: str):
        """Clean up a session and its subscribers."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        if session_id in self.stream_subscribers:
            # Cancel all subscribers
            for queue in self.stream_subscribers[session_id]:
                try:
                    await queue.put(None)  # Signal shutdown
                except Exception:
                    pass
            del self.stream_subscribers[session_id]
        
        # Remove from Redis
        try:
            await self.redis_client.delete(f"research_session:{session_id}")
        except Exception as e:
            logger.error(f"Error cleaning up session from Redis: {e}")
        
        logger.info(f"Cleaned up session {session_id}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the context manager."""
        try:
            active_sessions = len(self.active_sessions)
            total_subscribers = sum(len(subscribers) for subscribers in self.stream_subscribers.values())
            
            return {
                "status": "healthy",
                "active_sessions": active_sessions,
                "total_subscribers": total_subscribers,
                "timestamp": _utc_timestamp()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": _utc_timestamp()
            }

    # ---------------- Caching & Reporting Utilities ----------------
    def _normalize_topic(self, text: str) -> str:
        text = (text or "").lower()
        cleaned = ''.join(ch if ch.isalnum() or ch.isspace() else ' ' for ch in text)
        tokens = [t for t in cleaned.split() if t]
        return ' '.join(sorted(tokens))

    def _cache_key(self, topic: str, questions: List[str]) -> str:
        norm_topic = self._normalize_topic(topic)
        norm_questions = [self._normalize_topic(q) for q in (questions or [])]
        return json.dumps({"t": norm_topic, "q": norm_questions}, sort_keys=True)

    async def _get_cached_synthesis(self, topic: str, questions: List[str]) -> Optional[Dict[str, Any]]:
        try:
            key = self._cache_key(topic, questions)
            data = await self.redis_client.hget("synthesis_cache", key)
            if not data:
                return None
            if isinstance(data, bytes):
                try:
                    data = data.decode('utf-8', 'ignore')
                except Exception:
                    return None
            return json.loads(data)
        except Exception:
            return None

    async def _store_synthesis_cache(self, topic: str, questions: List[str], synthesis: Dict[str, Any]):
        try:
            key = self._cache_key(topic, questions)
            def _convert(obj):
                if isinstance(obj, set):
                    return list(obj)
                return obj
            payload = json.dumps(synthesis, ensure_ascii=False, default=_convert)
            await self.redis_client.hset("synthesis_cache", key, payload)
        except Exception:
            pass

    async def _find_similar_cached(self, topic: str, questions: List[str], min_score: float = 0.7) -> Optional[Dict[str, Any]]:
        """Find a semantically similar cached synthesis using simple token Jaccard overlap."""
        try:
            entries = await self.redis_client.hgetall("synthesis_cache")
            if not entries:
                return None
            target_tokens = set(self._normalize_topic(topic).split())
            best = None
            best_score = 0.0
            for key, val in entries.items():
                try:
                    if isinstance(key, bytes):
                        key_str = key.decode('utf-8', 'ignore')
                    else:
                        key_str = str(key)
                    parsed = json.loads(key_str)
                    cached_topic = parsed.get('t', '')
                    tokens = set(str(cached_topic).split())
                    inter = len(tokens & target_tokens)
                    union = len(tokens | target_tokens) or 1
                    score = inter / union
                    if score > best_score:
                        best_score = score
                        best = val
                except Exception:
                    continue
            if best_score >= min_score and best is not None:
                data = best.decode('utf-8', 'ignore') if isinstance(best, bytes) else str(best)
                return json.loads(data)
        except Exception:
            return None
        return None

    async def _write_reports(self, session_id: str, topic: str, synthesis: Dict[str, Any]):
        try:
            reports_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            # JSON report
            json_path = os.path.join(reports_dir, f"{session_id}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(synthesis, f, ensure_ascii=False, indent=2)
            # Markdown report
            md_path = os.path.join(reports_dir, f"{session_id}.md")
            summary = synthesis.get('summary') or synthesis.get('synthesis') or ""
            body = json.dumps({k: v for k, v in synthesis.items() if k not in ['summary', 'synthesis']}, ensure_ascii=False, indent=2)
            md_lines = [
                f"# Research Report: {topic}",
                "",
                f"Generated: {_utc_timestamp()}Z",
                "",
                "## Summary",
                summary if isinstance(summary, str) else json.dumps(summary, ensure_ascii=False, indent=2),
                "",
                "## Details",
                body
            ]
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(md_lines))
        except Exception:
            pass

    @log_operation("create_session")
    async def create_session(self, topic: str, context: Optional[Dict] = None, user_id: str = "default_user") -> str:
        """Create a new research session with enhanced context handling."""
        #logger.info(f"Creating research session for topic: {topic}")
        
        session_id = str(uuid.uuid4())
        session = ResearchSession(
            id=session_id,
            user_id=user_id,
            topic=topic,
            context=context or {},
            created_at=_utc_now(),
            updated_at=_utc_now(),
            status="initializing",
            papers=[],
            notes=[],
            progress={
                "stage": "created",
                "percentage": 0,
                "papers_found": 0,
                "papers_processed": 0
            }
        )
        
        # Store in database and cache
        await self.db.store_research_session(session.dict())
        self.active_sessions[session_id] = session
        
        # Start background processing
        self.session_tasks[session_id] = asyncio.create_task(
            self._process_session(session_id)
        )
        
        #logger.info(f"Created research session: {session_id}")
        return session_id

    @log_operation("process_session")
    async def _process_session(self, session_id: str):
        """Handle long-running session processing."""
        try:
            session = self.active_sessions[session_id]
            
            # Update status
            session.status = "searching"
            await self._update_session(session)
            
            # Search for papers
            papers = await self._search_papers(session.topic, session.context)
            session.papers = [p["id"] for p in papers]
            session.progress["papers_found"] = len(papers)
            await self._update_session(session)
            
            # Process papers
            for paper in papers:
                await self._queue_paper_processing(session_id, paper)
                session.progress["papers_processed"] += 1
                await self._update_session(session)
            
            # After synthesis, collect citations
            if session.papers:
                session.status = "synthesizing"
                await self._update_session(session)
                synthesis = await self.synthesizer.synthesize_papers(session.papers)
                session.synthesis = synthesis
                # Collect citations from synthesis
                session.citations = synthesis.get('citations', [])
            
            session.status = "completed"
            session.progress["percentage"] = 100
            await self._update_session(session)
            
        except Exception as e:
            logger.error(f"Error processing session {session_id}: {str(e)}")
            session.status = "error"
            session.error = str(e)
            await self._update_session(session)

    async def _search_papers(self, topic: str, context: Dict) -> List[Dict]:
        """Search for relevant papers with parallelization, deduplication, and ranking."""
        import heapq
        import operator
        #logger.info(f"Searching for papers on: {topic}")
        papers = []
        errors = {}
        try:
            # Gather from multiple sources in parallel
            from src.services.paper_service.openalex import OpenAlexClient
            from src.services.paper_service.paper_access import PaperAccessManager
            # Optionally add more sources here
            async with OpenAlexClient() as openalex, PaperAccessManager() as pam:
                tasks = [
                    openalex.search_works(topic, per_page=15),
                    # Add more sources here as needed, e.g. pam.semantic_scholar_search(topic), pam.core_search(topic)
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for res in results:
                    if isinstance(res, Exception):
                        errors[type(res).__name__] = str(res)
                        continue
                    if isinstance(res, dict) and res.get('results'):
                        for paper in res['results']:
                            papers.append(paper)
                    elif isinstance(res, list):
                        papers.extend(res)
        except Exception as e:
            logger.warning(f"Paper search failed: {str(e)}")
            errors[type(e).__name__] = str(e)
        # Deduplicate by DOI or title
        seen = set()
        deduped = []
        for paper in papers:
            doi = paper.get('doi') or paper.get('id')
            title = paper.get('title', '').lower()
            key = (doi, title)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(paper)
        # Rank by relevance, citation count, recency
        def paper_score(p):
            score = 0
            # Prefer more recent
            year = p.get('year') or p.get('publication_year') or 0
            score += (int(year) if year else 0) * 1.0
            # Prefer more citations
            score += (p.get('citations') or p.get('cited_by_count') or 0) * 2.0
            # Prefer open access
            if p.get('open_access') or (p.get('open_access', {}).get('is_oa', False)):
                score += 10
            return score
        deduped.sort(key=paper_score, reverse=True)
        # If nothing found, fall back to mock papers
        if not deduped:
            #logger.info(f"Using mock papers for topic: {topic}")
            return [
                {
                    'id': f"mock-paper-1-{uuid.uuid4()}",
                    'title': f"Advances in {topic}",
                    'doi': "https://doi.org/10.1234/mock.123",
                    'authors': ["A. Researcher", "B. Scientist", "C. Professor"],
                    'year': 2024,
                    'citations': 42,
                    'open_access': True,
                    'abstract': f"This paper explores recent developments in {topic}, focusing on practical applications.",
                },
                {
                    'id': f"mock-paper-2-{uuid.uuid4()}",
                    'title': f"Review of {topic} Technologies",
                    'doi': "https://doi.org/10.5678/mock.456",
                    'authors': ["D. Expert", "E. Analyst"],
                    'year': 2023,
                    'citations': 28,
                    'open_access': True,
                    'abstract': f"A comprehensive review of current {topic} technologies and methodologies.",
                },
                {
                    'id': f"mock-paper-3-{uuid.uuid4()}",
                    'title': f"Future Directions in {topic}",
                    'doi': "https://doi.org/10.9012/mock.789",
                    'authors': ["F. Visionary", "G. Pioneer"],
                    'year': 2024,
                    'citations': 15,
                    'open_access': True,
                    'abstract': f"This forward-looking paper examines emerging trends and future directions in {topic}.",
                }
            ]
        return deduped[:20]  # Limit to top 20 papers

    def _extract_abstract(self, paper):
        """Extract abstract from OpenAlex format"""
        abstract_index = paper.get("abstract_inverted_index")
        if not abstract_index:
            return "No abstract available"
        
        # Reconstruct from inverted index
        words = [""] * 300
        for word, positions in abstract_index.items():
            for pos in positions:
                if pos < len(words):
                    words[pos] = word
        
        abstract = " ".join(word for word in words if word).strip()
        return abstract[:800] + "..." if len(abstract) > 800 else abstract

    async def _queue_paper_processing(self, session_id: str, paper: Dict):
        """Queue paper for processing with session context."""
        try:
            processing_request = {
                "session_id": session_id,
                "paper": paper,
                "timestamp": _utc_timestamp()
            }
            
            await self.redis_client.lpush(
                "processing_queue",
                json.dumps(processing_request)
            )
            
        except Exception as e:
            logger.error(f"Error queuing paper for processing: {str(e)}")
            raise

    @log_operation("get_session_status")
    async def get_session_status(self, session_id: str) -> Dict:
        """Get detailed session status."""
        session = await self._get_session(session_id)
        if not session:
            return {"error": "Session not found"}
            
        # Get processing progress
        progress = await self.redis_client.hgetall(f"progress:{session_id}")
        
        return {
            "id": session_id,
            "status": session.status,
            "progress": session.progress,
            "papers_total": len(session.papers),
            "processing_stage": progress.get("stage", "unknown"),
            "processing_percentage": progress.get("percentage", 0),
            "last_updated": session.updated_at.isoformat(),
            "error": session.error if hasattr(session, 'error') else None
        }

    @log_operation("add_note")
    async def add_note(self, session_id: str, note: Dict) -> bool:
        """Add a structured note to research session."""
        session = await self._get_session(session_id)
        if not session:
            return False
            
        note_entry = {
            "id": str(uuid.uuid4()),
            "content": note.get("content"),
            "type": note.get("type", "general"),
            "references": note.get("references", []),
            "created_at": _utc_timestamp()
        }
        
        session.notes.append(note_entry)
        session.updated_at = _utc_now()
        
        await self._update_session(session)
        return True

    async def _update_session(self, session: ResearchSession):
        """Update session in database and cache."""
        session.updated_at = _utc_now()
        await self.db.update_research_session(session.dict())
        self.active_sessions[session.id] = session

        # Prepare Redis-compatible mapping
        redis_mapping = {}
        for key, value in session.dict().items():
            if value is None:
                # Convert None to empty string for Redis
                redis_mapping[key] = ""
            elif isinstance(value, datetime):
                # Convert datetime to ISO format string
                redis_mapping[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                # Serialize complex types
                redis_mapping[key] = json.dumps(value)
            else:
                redis_mapping[key] = value

        # Update Redis cache
        try:
            await self.redis_client.hset(
                f"session:{session.id}",
                mapping=redis_mapping  # Use serialized mapping
            )
        except Exception as e:
            logger.error(f"Error updating Redis cache: {str(e)}")

    async def _get_session(self, session_id: str) -> Optional[ResearchSession]:
        """Get research session by ID with caching."""
        # Check memory cache first
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
                
        # Try Redis cache
        session_data = await self.redis_client.hgetall(f"session:{session_id}")
        if session_data:
            # Convert JSON strings and datetime strings back to Python objects
            for key, value in session_data.items():
                if key in ['progress', 'context', 'synthesis']:
                    try:
                        session_data[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        pass
                elif key in ['created_at', 'updated_at'] and isinstance(value, str):
                    try:
                        session_data[key] = datetime.fromisoformat(value)
                    except ValueError:
                        pass
                    
            session = ResearchSession(**session_data)
            self.active_sessions[session_id] = session
            return session
            
        # Finally try database
        session_data = await self.db.get_research_session(session_id)
        if session_data:
            session = ResearchSession(**session_data)
            self.active_sessions[session_id] = session
            
            # Update cache
            await self.redis_client.hset(
                f"session:{session_id}",
                mapping=session.dict()
            )
            return session
            
        return None

    async def cleanup(self):
        """Cleanup manager resources."""
        try:
            # Cancel all running tasks
            for task in self.session_tasks.values():
                task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(*self.session_tasks.values(), return_exceptions=True)
            
            # Close Redis connection
            await self.redis_client.close()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    @log_operation("start_layered_research")
    async def start_layered_research(self, topic: str, research_questions: List[str], max_layers: int = 3, user_id: str = "default_user") -> str:
        """Start a multi-layered research process that explores connected concepts"""
        #logger.info(f"Starting layered research on: {topic}")
        
        # Create a new session
        session_id = str(uuid.uuid4())
        session = ResearchSession(
            id=session_id,
            topic=topic,
            user_id=user_id,
            context={
                "research_type": "layered",
                "questions": research_questions,
                "max_layers": max_layers,
                "current_layer": 0,
                "explored_concepts": [topic],
                "discovered_concepts": []
            },
            created_at=_utc_now(),
            updated_at=_utc_now(),
            status="initializing",
            papers=[],
            notes=[],
            progress={
                "stage": "created",
                "percentage": 0,
                "web_sources_found": 0,
                "papers_found": 0,
                "papers_processed": 0
            }
        )
        
        # Store in database and cache
        await self.db.store_research_session(session.dict())
        self.active_sessions[session_id] = session
        
        # Serve from cache if available
        cached = await self._get_cached_synthesis(topic, research_questions)
        if cached:
            session.synthesis = cached
            session.status = "completed"
            session.progress["percentage"] = 100
            await self._update_session(session)
        else:
            # Start layered research process
            self.session_tasks[session_id] = asyncio.create_task(
                self._process_layered_research(session_id)
            )
        
        #logger.info(f"Created layered research session: {session_id}")
        return session_id

    async def _process_layered_research(self, session_id: str):
        """Process a layered research session with LLM-powered query generation, semantic clustering, and source scoring."""
        try:
            session = self.active_sessions[session_id]
            session.status = "exploring_main_topic"
            await self._update_session(session)

            import time
            SATURATION_CRITERIA = {
                'min_papers': 10,
                'min_web_sources': 15,
                'novelty_threshold': 0.15,
                'time_budget': 1800,  # 30 min
                'ideal_paper_range': (20, 100),
            }
            state = {
                'web_sources': [],
                'academic_papers': [],
                'key_insights': set(),
                'information_graph': {},
                'saturation_score': 0,
                'start_time': time.time(),
                'diversity_metrics': {},
                'contradictions': [],
                'gap_queries': set(),
                'clusters': [],
                'source_scores': {},
            }
            topic = session.topic
            layer = 1
            max_layers = session.context.get("max_layers", 3)
            concepts_to_explore = [topic]
            explored_concepts = set()
            gap_queries = set()
            while True:
                if not concepts_to_explore or layer > max_layers:
                    break
                concept = concepts_to_explore.pop(0)
                if concept in explored_concepts:
                    continue
                explored_concepts.add(concept)
                session.context["current_layer"] = layer
                session.context.setdefault("explored_concepts", []).append(concept)
                session.progress["percentage"] = min(80, int((layer / max_layers) * 80))
                session.status = f"exploring_layer_{layer}"
                await self._update_session(session)

                # --- Parallel search ---
                web_results, papers = await asyncio.gather(
                    self._search_web_sources(concept),
                    self._search_papers(concept, session.context)
                )
                # Fetch web content for important results
                web_content_tasks = []
                for result in web_results:
                    if self._is_important_result(result):
                        task = asyncio.create_task(self._fetch_web_content(result.get("url", "")))
                        web_content_tasks.append((result, task))
                for result, task in web_content_tasks:
                    try:
                        content = await task
                        result["extracted_content"] = content
                    except Exception as e:
                        result["extracted_content"] = f"Failed to extract: {str(e)}"
                # --- Source credibility scoring ---
                for paper in papers:
                    score = self._score_academic_source(paper)
                    state['source_scores'][paper.get('id')] = score
                for web in web_results:
                    score = self._score_web_source(web)
                    state['source_scores'][web.get('url')] = score
                # Deduplicate web results by (url, title)
                seen = set()
                uniq_web = []
                for w in web_results:
                    key = (w.get('url','').strip().lower(), w.get('title','').strip().lower())
                    if key in seen:
                        continue
                    seen.add(key)
                    uniq_web.append(w)
                web_results = uniq_web
                # Update state
                state['web_sources'].extend(web_results)
                state['academic_papers'].extend(papers)
                session.context.setdefault("web_sources", []).extend(web_results)
                session.papers.extend([p["id"] for p in papers])
                session.progress["web_sources_found"] += len(web_results)
                session.progress["papers_found"] += len(papers)
                await self._update_session(session)
                # --- Extract insights ---
                new_insights_web = self._extract_insights_from_web(web_results)
                new_insights_papers = self._extract_insights_from_papers(papers)
                # --- Semantic clustering ---
                state['clusters'] = self._cluster_insights(new_insights_web | new_insights_papers)
                # --- Calculate novelty ---
                web_novelty = self._calculate_novelty(new_insights_web, state['key_insights'])
                paper_novelty = self._calculate_novelty(new_insights_papers, state['key_insights'])
                # --- Update key insights ---
                state['key_insights'].update(new_insights_web)
                state['key_insights'].update(new_insights_papers)
                # --- Diversity & contradiction analysis ---
                state['diversity_metrics'] = self._analyze_diversity(state['academic_papers'], state['web_sources'])
                state['contradictions'].extend(self._detect_contradictions(new_insights_web, new_insights_papers))
                # --- Gap analysis & LLM-powered query refinement ---
                new_gap_queries = self._generate_gap_queries(state, concept)
                # Use LLM to suggest additional queries
                llm_gap_queries = await self._llm_generate_gap_queries(state, concept)
                for q in new_gap_queries.union(llm_gap_queries):
                    if q not in gap_queries:
                        gap_queries.add(q)
                        concepts_to_explore.append(q)
                # --- Calculate saturation ---
                state['saturation_score'] = self._calculate_saturation(
                    web_novelty, paper_novelty,
                    len(state['academic_papers']), len(state['web_sources'])
                )
                # --- Coverage checks ---
                coverage_met = (
                    len(state['academic_papers']) >= SATURATION_CRITERIA['min_papers'] and
                    len(state['web_sources']) >= SATURATION_CRITERIA['min_web_sources']
                )
                time_elapsed = time.time() - state['start_time']
                # --- Stopping conditions ---
                if (
                    (web_novelty < SATURATION_CRITERIA['novelty_threshold'] and paper_novelty < SATURATION_CRITERIA['novelty_threshold']) or
                    state['saturation_score'] >= 0.95 or
                    coverage_met or
                    time_elapsed > SATURATION_CRITERIA['time_budget']
                ):
                    break
                layer += 1
            # --- Synthesis ---
            session.status = "synthesizing"
            await self._update_session(session)
            synthesis = await self._generate_layered_synthesis(session_id)
            # Attach advanced metrics to synthesis
            synthesis['diversity_metrics'] = state['diversity_metrics']
            synthesis['contradictions'] = state['contradictions']
            synthesis['gap_queries'] = list(gap_queries)
            synthesis['clusters'] = state['clusters']
            synthesis['source_scores'] = state['source_scores']
            session.synthesis = synthesis
            session.status = "completed"
            session.progress["percentage"] = 100
            await self._update_session(session)
            # Persist for reuse and create reports
            await self._store_synthesis_cache(session.topic, session.context.get('questions', []), synthesis)
            await self._write_reports(session_id, session.topic, synthesis)
        except Exception as e:
            logger.error(f"Error in layered research {session_id}: {str(e)}")
            session.status = "error"
            session.error = str(e)
            await self._update_session(session)

    async def _explore_concept(self, session_id: str, concept: str, layer: int):
        """Explore a concept in the layered research process"""
        session = self.active_sessions[session_id]
        max_layers = session.context.get("max_layers", 3)
        
        # Don't explore beyond max layers or already explored concepts
        if layer > max_layers or concept in session.context.get("explored_concepts", []):
            return
        
        #logger.info(f"Exploring concept '{concept}' at layer {layer} for session {session_id}")
        
        # Update session state
        session.context["current_layer"] = layer
        session.context.get("explored_concepts", []).append(concept)
        session.progress["percentage"] = min(80, int((layer / max_layers) * 80))  # Reserve 20% for synthesis
        session.status = f"exploring_layer_{layer}"
        await self._update_session(session)
        
        # Search for both web and academic sources
        web_results, papers = await asyncio.gather(
            self._search_web_sources(concept),
            self._search_papers(concept, session.context)
        )
        
        web_content_tasks = []
        for result in web_results:
            if self._is_important_result(result):
                task = asyncio.create_task(self._fetch_web_content(result.get("url", "")))
                web_content_tasks.append((result, task))

        # Wait for content fetching to complete
        for result, task in web_content_tasks:
            try:
                content = await task
                result["extracted_content"] = content
            except Exception as e:
                logger.error(f"Error fetching content: {str(e)}")
                result["extracted_content"] = f"Failed to extract: {str(e)}"
        
        # Update session with new sources
        if "web_sources" not in session.context:
            session.context["web_sources"] = []
        session.context["web_sources"].extend(web_results)
        session.progress["web_sources_found"] += len(web_results)
        
        # Add papers to session
        paper_ids = [p["id"] for p in papers]
        session.papers.extend(paper_ids)
        session.progress["papers_found"] += len(papers)
        await self._update_session(session)
        
        # Process papers to extract information
        for paper in papers:
            await self._queue_paper_processing(session_id, paper)
            session.progress["papers_processed"] += 1
            await self._update_session(session)
        
        # Discover new concepts from current sources
        new_concepts = await self._discover_related_concepts(session_id, concept, web_results, papers)
        
        # Store discovered concepts
        if "discovered_concepts" not in session.context:
            session.context["discovered_concepts"] = []
        
        concept_layer = {
            "concept": concept,
            "layer": layer,
            "related_concepts": new_concepts
        }
        session.context["discovered_concepts"].append(concept_layer)
        await self._update_session(session)
        
        # Recursively explore new concepts in next layer
        for new_concept in new_concepts[:3]:  # Limit to top 3 concepts per layer
            await self._explore_concept(session_id, new_concept, layer + 1)

    async def _search_web_sources(self, concept: str) -> List[Dict]:
        """Search for web sources related to a concept (Google -> Bing -> mock)."""

        # Mock fallback
        mock_results = [
            {
                "title": f"Overview of {concept}",
                "url": "https://example.com/mock1",
                "snippet": f"This is a comprehensive overview of {concept} and its applications in scientific research.",
                "source": "mock"
            },
            {
                "title": f"Recent developments in {concept}",
                "url": "https://example.com/mock2",
                "snippet": f"Recent studies have shown significant progress in the field of {concept}.",
                "source": "mock"
            }
        ]

        try:
            # Prefer Google Custom Search if configured
            google_results = await self._try_google_search(concept)
            if google_results:
                return google_results

            # Fallback to Bing Search API
            bing_results = await self._try_bing_search(concept)
            if bing_results:
                return bing_results

            logger.warning(f"All web searches failed - using mock results for: {concept}")
            return mock_results
        except Exception as e:
            logger.error(f"Web search error: {str(e)}")
            return mock_results

    async def _try_google_search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Try to search using Google Custom Search API"""
        import os
        import aiohttp
        
        # Support multiple common env var names for compatibility
        api_key = (
            os.environ.get("GOOGLE_SEARCH_API_KEY")
            or os.environ.get("GOOGLE_CUSTOM_SEARCH_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )
        cx = (
            os.environ.get("GOOGLE_SEARCH_CX")
            or os.environ.get("GOOGLE_SEARCH_ENGINE_ID")
            or os.environ.get("GOOGLE_SEARCH_ENGINE_CX")
        )
        
        if not api_key or not cx:
            logger.warning("Google Search API credentials not configured")
            return []
            
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cx,
            "q": query,
            "num": min(num_results, 10)
        }
        
        # Retry with basic backoff
        for attempt in range(3):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = []
                            for item in data.get("items", []):
                                results.append({
                                    "title": item.get("title"),
                                    "url": item.get("link"),
                                    "snippet": item.get("snippet"),
                                    "source": "google_search"
                                })
                            return results
                        else:
                            logger.warning(f"Google search failed with status {response.status}")
            except Exception as e:
                logger.error(f"Google search error (attempt {attempt+1}): {str(e)}")
            await asyncio.sleep(1.0 * (attempt + 1))
        return []

    async def _try_bing_search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Try to search using Bing Search API"""
        import os
        import aiohttp
        
        api_key = os.environ.get("BING_SEARCH_API_KEY")
        
        if not api_key:
            logger.warning("Bing Search API key not configured")
            return []
            
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": api_key}
        params = {
            "q": query,
            "count": min(num_results, 50),
            "responseFilter": "Webpages"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        results = []
                        for item in data.get("webPages", {}).get("value", []):
                            results.append({
                                "title": item.get("name"),
                                "url": item.get("url"),
                                "snippet": item.get("snippet"),
                                "source": "bing_search"
                            })
                        return results
                    else:
                        logger.warning(f"Bing search failed with status {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Bing search error: {str(e)}")
            return []

    async def _fetch_web_content(self, url: str) -> str:
        """Fetch and extract main content from web page"""
        import aiohttp
        from bs4 import BeautifulSoup
        
        for attempt in range(3):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            html = await response.text()
                            # Parse with BeautifulSoup
                            soup = BeautifulSoup(html, 'html.parser')
                            # Remove non-content elements
                            for element in soup(["script", "style", "header", "footer", "nav"]):
                                element.decompose()
                            # Get text content
                            text = soup.get_text(separator='\n')
                            # Clean up text
                            lines = (line.strip() for line in text.splitlines())
                            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                            text = '\n'.join(chunk for chunk in chunks if chunk)
                            # Truncate if too long
                            if len(text) > 5000:
                                text = text[:5000] + "..."
                            return text
                        else:
                            msg = f"Failed to fetch content: HTTP {response.status}"
                            if attempt == 2:
                                return msg
            except Exception as e:
                logger.error(f"Error fetching content from {url} (attempt {attempt+1}): {str(e)}")
            await asyncio.sleep(1.0 * (attempt + 1))
        return "Error fetching content after retries"

    def _is_important_result(self, result: Dict) -> bool:
        """Determine if a web result is important enough to fetch full content"""
        important_keywords = ["research", "study", "analysis", "review", "journal"]
        return any(keyword in result.get("title", "").lower() for keyword in important_keywords)

    async def _discover_related_concepts(self, session_id: str, concept: str, 
                                        web_results: List[Dict], papers: List[Dict]) -> List[str]:
        """Discover related concepts from current research sources"""
        session = self.active_sessions[session_id]
        
        # Check if llm_manager is available
        if not hasattr(self, 'llm_manager') or self.llm_manager is None:
            logger.warning(f"No LLM manager available - returning mock concepts for: {concept}")
            # Return mock concepts for testing without LLM
            return ["Quantum algorithms", "Molecular modeling", "Drug discovery optimization"]
        
        # Use the query generator to discover concepts
        from .query_generator import EnhancedQueryGenerator
        query_generator = EnhancedQueryGenerator(self.llm_manager)  # Use llm_manager here
        
        # Extract context from web results
        web_context = []
        for result in web_results:
            if "extracted_content" in result:
                web_context.append(f"Title: {result['title']}\nContent: {result['extracted_content'][:500]}...")
            else:
                web_context.append(f"Title: {result['title']}\nSnippet: {result['snippet']}")
        
        # Extract context from papers
        paper_context = []
        for paper in papers:
            paper_context.append(f"Title: {paper.get('title', '')}\nAuthors: {', '.join(paper.get('authors', []))}")
        
        # Generate concepts
        concepts_prompt = f"""
        Based on research about "{concept}", identify 3-5 important related concepts that should be explored next.
        
        RESEARCH QUESTIONS:
        {json.dumps(session.context.get('questions', []))}
        
        WEB SOURCES:
        {json.dumps(web_context)}
        
        ACADEMIC PAPERS:
        {json.dumps(paper_context)}
        
        Identify concepts that:
        1. Are mentioned across multiple sources
        2. Appear important but not fully explained
        3. Would deepen understanding of the main topic
        4. Are distinct from the current focus
        
        Return ONLY a list of concepts, one per line.
        """
        
        # Get concepts from LLM
        response = await self.llm_manager.generate_text(concepts_prompt)  # Use llm_manager here
        concepts = [c.strip() for c in response.split('\n') if c.strip()]
        
        return concepts[:5]  # Limit to 5 concepts

    async def _generate_layered_synthesis(self, session_id: str) -> Dict:
        """Generate comprehensive synthesis for layered research"""
        session = self.active_sessions[session_id]
        
        # Collect all web sources
        web_sources = session.context.get("web_sources", [])
        
        # Collect all processed papers
        processed_papers = []
        for paper_id in session.papers:
            paper_data = await self.db.get_processed_paper(paper_id)
            if paper_data:
                processed_papers.append(paper_data)
        
        # Get concept layers
        concept_layers = session.context.get("discovered_concepts", [])
        
        # Use synthesizer to generate synthesis
        synthesis = await self.synthesizer.synthesize_layered_research(
            session.topic,
            session.context.get("questions", []),
            web_sources,
            processed_papers,
            concept_layers
        )
        # Attach helpful artifacts
        synthesis['artifacts'] = {
            'report_json': f"/reports/{session_id}.json",
            'report_markdown': f"/reports/{session_id}.md"
        }
        
        return synthesis

    def _extract_insights_from_web(self, web_results):
        """Extract key insights from web results."""
        insights = set()
        for result in web_results:
            snippet = result.get("snippet") or result.get("extracted_content")
            if snippet:
                for sent in snippet.split(". "):
                    if len(sent.split()) > 6:
                        insights.add(sent.strip())
        return insights

    def _extract_insights_from_papers(self, papers):
        """Extract key insights from academic papers."""
        insights = set()
        for paper in papers:
            abstract = paper.get("abstract")
            if abstract:
                for sent in abstract.split(". "):
                    if len(sent.split()) > 6:
                        insights.add(sent.strip())
        return insights

    def _calculate_novelty(self, new_insights, known_insights):
        """Calculate novelty as the fraction of new insights."""
        if not new_insights:
            return 0.0
        new = set(new_insights) - set(known_insights)
        return len(new) / max(1, len(new_insights))

    def _calculate_saturation(self, web_novelty, paper_novelty, num_papers, num_web):
        """Calculate a saturation score based on novelty and coverage."""
        novelty_score = 1.0 - max(web_novelty, paper_novelty)
        coverage_score = min(num_papers / 30, num_web / 30, 1.0)
        return 0.7 * novelty_score + 0.3 * coverage_score

    def _analyze_diversity(self, papers, web_sources):
        """Analyze diversity of institutions, methodologies, viewpoints, and publication years."""
        diversity = {
            'institutions': set(),
            'methodologies': set(),
            'years': set(),
            'source_types': set(),
        }
        for paper in papers:
            if 'institution' in paper:
                diversity['institutions'].add(paper['institution'])
            if 'methodology' in paper:
                diversity['methodologies'].add(paper['methodology'])
            if 'year' in paper:
                diversity['years'].add(paper['year'])
            diversity['source_types'].add('academic')
        for web in web_sources:
            if 'source' in web:
                diversity['source_types'].add(web['source'])
            if 'date' in web:
                diversity['years'].add(web['date'][:4])
        # Convert sets to lists for serialization
        for k in diversity:
            diversity[k] = list(diversity[k])
        return diversity

    def _detect_contradictions(self, web_insights, paper_insights):
        """Detect contradictions between web and academic insights."""
        contradictions = []
        web_set = set(web_insights)
        paper_set = set(paper_insights)
        # Simple contradiction: same topic, opposite claims (heuristic)
        for w in web_set:
            for p in paper_set:
                if w.lower() in p.lower() or p.lower() in w.lower():
                    continue
                # Heuristic: if both mention the same keyword but have different sentiment
                # (This can be improved with LLM or sentiment analysis)
                if any(neg in w.lower() for neg in ['not ', 'no ', 'fail', 'lack']) != any(neg in p.lower() for neg in ['not ', 'no ', 'fail', 'lack']):
                    contradictions.append({'web': w, 'paper': p})
        return contradictions

    def _generate_gap_queries(self, state, concept):
        """Generate new queries to fill gaps in coverage."""
        # Heuristic: look for missing years, institutions, or methodologies
        gap_queries = set()
        # Example: if not enough recent papers, add query for 'recent advances in ...'
        if len(state['diversity_metrics'].get('years', [])) < 3:
            gap_queries.add(f"recent advances in {concept}")
        if len(state['diversity_metrics'].get('institutions', [])) < 2:
            gap_queries.add(f"institutional perspectives on {concept}")
        if len(state['diversity_metrics'].get('methodologies', [])) < 2:
            gap_queries.add(f"methodological approaches to {concept}")
        # Add more heuristics as needed
        return gap_queries

    async def _llm_generate_gap_queries(self, state, concept: str) -> set:
        """Use LLM to propose additional gap-filling queries."""
        try:
            if not hasattr(self, 'llm_manager') or self.llm_manager is None:
                return set()
            web_sources = state.get('web_sources', [])[-5:]
            papers = state.get('academic_papers', [])[-5:]
            prompt = (
                f"Given the topic '{concept}', propose 3-6 additional search queries to fill knowledge gaps.\n"
                f"Recent web sources: {json.dumps(web_sources[:3])}\n"
                f"Recent papers titles: {[p.get('title','') for p in papers[:5]]}\n"
                f"Focus on missing institutions, methodologies, time ranges, and alternative viewpoints.\n"
                f"Return one query per line, no bullets or numbering."
            )
            text = await self.llm_manager.generate_text(prompt)
            queries = {q.strip() for q in text.split('\n') if q.strip()}
            return set(list(queries)[:6])
        except Exception:
            return set()

    def _cluster_insights(self, insights):
        """Cluster insights by semantic similarity (using embeddings)."""
        # Placeholder: In production, use embeddings + clustering (e.g., KMeans)
        # For now, group by keyword overlap as a simple heuristic
        clusters = []
        insights = list(insights)
        used = set()
        for i, sent in enumerate(insights):
            if i in used:
                continue
            cluster = [sent]
            for j, other in enumerate(insights):
                if i != j and j not in used:
                    if len(set(sent.lower().split()) & set(other.lower().split())) > 3:
                        cluster.append(other)
                        used.add(j)
            used.add(i)
            clusters.append(cluster)
        return clusters

    def _score_academic_source(self, paper):
        """Score academic source credibility (citation count, journal, recency)."""
        score = 0.0
        if 'citation_count' in paper:
            try:
                c = int(paper['citation_count'])
                score += min(5.0, 2.0 * (c ** 0.5))
            except:
                pass
        if 'year' in paper:
            try:
                y = int(paper['year'])
                if y >= 2022:
                    score += 2.0
                elif y >= 2018:
                    score += 1.0
            except:
                pass
        if 'journal' in paper and paper['journal']:
            score += 1.0
        return min(score, 10.0)

    def _score_web_source(self, web):
        """Score web source credibility (domain, recency, cross-references)."""
        score = 0.0
        url = web.get('url', '')
        if any(domain in url for domain in ['.edu', '.ac.', '.gov']):
            score += 3.0
        if any(domain in url.lower() for domain in ['ieee', 'springer', 'nature', 'acm', 'nejm', 'science.org', 'cell.com', 'wiley']):
            score += 2.0
        if 'date' in web:
            try:
                y = int(web['date'][:4])
                if y >= 2022:
                    score += 2.0
                elif y >= 2018:
                    score += 1.0
            except:
                pass
        if 'source' in web and web['source'] in ['web_search', 'bing_search']:
            score += 1.0
        return min(score, 10.0)