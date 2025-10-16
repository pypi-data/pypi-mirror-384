#indexer.py
from typing import List, Dict, Optional
import asyncio
from datetime import datetime, timezone
import redis.asyncio as redis
import json

from ...utils.logger import logger, log_operation
from ...storage.db.operations import DatabaseOperations
from .vector_search import VectorSearchEngine


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

class DocumentIndexer:
    def __init__(self, db_ops: DatabaseOperations, vector_search: VectorSearchEngine, redis_url: str):
        #logger.info("Initializing DocumentIndexer")
        self.db = db_ops
        self.vector_search = vector_search
        self.redis_client = redis.from_url(redis_url)
        self.indexing_queue = asyncio.Queue()
        self.active_sessions: Dict[str, Dict] = {}
        self._running = False
        #logger.info("DocumentIndexer initialized")

    @log_operation("start_indexing")
    async def start(self):
        """Start the indexing process."""
        #logger.info("Starting indexing service")
        self._running = True
        try:
            await asyncio.gather(
                self._process_queue(),
                self._monitor_research_sessions()
            )
        except Exception as e:
            logger.error(f"Error in indexing service: {str(e)}")
            self._running = False
            raise

    @log_operation("monitor_sessions")
    async def _monitor_research_sessions(self):
        """Monitor active research sessions for new documents."""
        while self._running:
            try:
                # Subscribe to research session updates
                async for message in self.redis_client.subscribe("research_updates"):
                    update = json.loads(message["data"])
                    session_id = update.get("session_id")
                    
                    if update.get("type") == "new_papers":
                        await self._handle_new_papers(session_id, update.get("papers", []))
                        
            except Exception as e:
                logger.error(f"Error monitoring sessions: {str(e)}")
                await asyncio.sleep(1)

    async def _handle_new_papers(self, session_id: str, papers: List[str]):
        """Handle new papers added to a research session."""
        #logger.info(f"Processing new papers for session {session_id}")
        for paper_id in papers:
            await self.queue_document(paper_id, session_id)

    @log_operation("queue_document")
    async def queue_document(self, doc_id: str, session_id: Optional[str] = None):
        """Queue a document for indexing."""
        #logger.info(f"Queuing document for indexing: {doc_id}")
        await self.indexing_queue.put({
            "doc_id": doc_id,
            "session_id": session_id,
            "queued_at": _utc_timestamp()
        })
        
        if session_id:
            await self._update_session_progress(session_id, "queued", doc_id)

    async def _process_queue(self):
        """Process documents in the indexing queue."""
        #logger.info("Starting queue processing")
        while self._running:
            try:
                item = await self.indexing_queue.get()
                doc_id = item["doc_id"]
                session_id = item.get("session_id")

                #logger.info(f"Processing document: {doc_id}")
                
                if session_id:
                    await self._update_session_progress(session_id, "processing", doc_id)

                processed_doc = await self.db.get_processed_paper(doc_id)
                if not processed_doc:
                    #logger.warning(f"Processed content not found: {doc_id}")
                    continue

                success = await self._index_document(doc_id, processed_doc.content)
                
                if success:
                    #logger.info(f"Successfully indexed: {doc_id}")
                    await self.db.update_paper_status(doc_id, "indexed")
                    if session_id:
                        await self._update_session_progress(session_id, "completed", doc_id)
                else:
                    #logger.error(f"Failed to index: {doc_id}")
                    if session_id:
                        await self._update_session_progress(session_id, "failed", doc_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing document: {str(e)}")
            finally:
                self.indexing_queue.task_done()

    async def _update_session_progress(self, session_id: str, status: str, doc_id: str):
        """Update indexing progress for research session."""
        try:
            progress_key = f"indexing_progress:{session_id}"
            await self.redis_client.hset(
                progress_key,
                mapping={
                    doc_id: json.dumps({
                        "status": status,
                        "updated_at": _utc_timestamp()
                    })
                }
            )
            
            # Publish update
            await self.redis_client.publish(
                "indexing_updates",
                json.dumps({
                    "session_id": session_id,
                    "doc_id": doc_id,
                    "status": status
                })
            )
        except Exception as e:
            logger.error(f"Error updating session progress: {str(e)}")

    @log_operation("batch_index")
    async def batch_index(self, doc_ids: List[str], session_id: Optional[str] = None) -> Dict[str, bool]:
        """Batch index multiple documents with session tracking."""
        #logger.info(f"Starting batch indexing: {len(doc_ids)} documents")
        results = {}
        
        for doc_id in doc_ids:
            await self.queue_document(doc_id, session_id)
            results[doc_id] = True
        
        await self.indexing_queue.join()
        return results

    @log_operation("reindex_all")
    async def reindex_all(self):
        """Reindex all documents with progress tracking."""
        #logger.info("Starting full reindexing")
        try:
            papers = await self.db.search_papers({"status": "processed"})
            doc_ids = [paper.id for paper in papers]
            
            if not doc_ids:
                logger.info("No documents found for reindexing")
                return
            
            total = len(doc_ids)
            progress_key = "reindex_progress"
            
            await self.redis_client.set(progress_key, "0")
            results = await self.batch_index(doc_ids)
            
            success_count = sum(1 for success in results.values() if success)
            await self.redis_client.set(progress_key, str(success_count / total * 100))
            
            #logger.info(f"Reindexing completed: {success_count}/{total} successful")
            
        except Exception as e:
            logger.error(f"Error during reindexing: {str(e)}")
            raise

    async def cleanup(self):
        """Cleanup indexing resources."""
        #logger.info("Cleaning up indexer resources")
        self._running = False
        await self.redis_client.close()