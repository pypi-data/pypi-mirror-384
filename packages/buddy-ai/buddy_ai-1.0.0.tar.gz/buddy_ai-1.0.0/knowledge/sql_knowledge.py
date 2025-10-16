import os
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Union

from buddy.document import Document
from buddy.knowledge.agent import AgentKnowledge
from buddy.utils.log import log_info, logger


class SQLKnowledgeBase(AgentKnowledge):
    """Knowledge base that stores documents in SQL database instead of using embeddings"""
    
    path: Optional[Union[str, Path, List[Dict[str, Union[str, Dict[str, Any]]]]]] = None
    db_path: str = "knowledge_database.db"
    formats: List[str] = []
    table_name: str = "documents"
    metadata_table_name: str = "document_metadata"
    
    def __init__(self, **data):
        super().__init__(**data)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create documents table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id TEXT,
                filepath TEXT,
                filename TEXT,
                content TEXT,
                chunk_index INTEGER,
                meta_data TEXT
            )
        ''')
        
        # Create metadata table for file tracking
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.metadata_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT UNIQUE,
                file_hash TEXT,
                last_modified REAL,
                last_ingested TEXT,
                file_size INTEGER
            )
        ''')
        
        # Create indexes for better search performance
        cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_content ON {self.table_name}(content)')
        cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_filepath ON {self.table_name}(filepath)')
        cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_filename ON {self.table_name}(filename)')
        cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_doc_id ON {self.table_name}(doc_id)')
        
        conn.commit()
        conn.close()
    
    def _get_file_hash(self, file_path: Path) -> Optional[str]:
        """Calculate MD5 hash of a file to detect changes"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None
    
    def _is_valid_file(self, path: Path) -> bool:
        """Helper to check if path is a valid file with supported format. If formats is empty, allow all files."""
        if not (path.exists() and path.is_file()):
            return False
        if not self.formats:
            return True
        return path.suffix in self.formats
    
    def _should_ingest_file(self, file_path: Path) -> bool:
        """Check if file should be ingested (new or changed)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            file_stat = os.stat(file_path)
            current_hash = self._get_file_hash(file_path)
            current_modified = file_stat.st_mtime
            current_size = file_stat.st_size
            
            if current_hash is None:
                return False
            
            # Check if file exists in metadata and if it has changed
            cursor.execute(
                f"SELECT file_hash, last_modified, file_size FROM {self.metadata_table_name} WHERE filepath = ?",
                (str(file_path),)
            )
            existing_record = cursor.fetchone()
            
            if existing_record is None:
                return True  # New file
            
            stored_hash, stored_modified, stored_size = existing_record
            # Check if file has changed
            if (current_hash != stored_hash or 
                current_modified != stored_modified or 
                current_size != stored_size):
                return True
            
            return False  # File hasn't changed
            
        except Exception as e:
            logger.error(f"Error checking file {file_path}: {e}")
            return False
        finally:
            conn.close()
    
    def _store_documents_in_db(self, documents: List[Document], file_path: Path) -> None:
        """Store documents in the SQL database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Remove old content for this file
            cursor.execute(f"DELETE FROM {self.table_name} WHERE filepath = ?", (str(file_path),))
            
            # Insert new documents
            for i, doc in enumerate(documents):
                cursor.execute(f'''
                    INSERT INTO {self.table_name} 
                    (doc_id, filepath, filename, content, chunk_index, meta_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    doc.id,
                    str(file_path),
                    file_path.name,
                    doc.content,
                    i,
                    str(doc.meta_data) if doc.meta_data else None
                ))
            
            # Update metadata
            file_stat = os.stat(file_path)
            current_hash = self._get_file_hash(file_path)
            current_modified = file_stat.st_mtime
            current_size = file_stat.st_size
            
            cursor.execute(f'''
                INSERT OR REPLACE INTO {self.metadata_table_name} 
                (filepath, file_hash, last_modified, last_ingested, file_size)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                str(file_path), 
                current_hash, 
                current_modified, 
                datetime.now().isoformat(), 
                current_size
            ))
            
            conn.commit()
            log_info(f"Stored {len(documents)} documents from {file_path.name}")
            
        except Exception as e:
            logger.error(f"Error storing documents from {file_path}: {e}")
            conn.rollback()
        finally:
            conn.close()

    @property
    def document_lists(self) -> Iterator[List[Document]]:
        """Iterate over files and yield lists of documents."""
        if self.path is None:
            raise ValueError("Path is not set")

        if isinstance(self.path, list):
            for item in self.path:
                if isinstance(item, dict) and "path" in item:
                    file_path = item["path"]
                    config = item.get("metadata", {})
                    _file_path = Path(file_path)
                    if self._is_valid_file(_file_path):
                        if self._should_ingest_file(_file_path):
                            documents = self._read_file_to_documents(_file_path, config)
                            if documents:
                                self._store_documents_in_db(documents, _file_path)
                                yield documents
        else:
            _file_path = Path(self.path)
            if _file_path.is_dir():
                for _file in _file_path.glob("**/*"):
                    if self._is_valid_file(_file):
                        if self._should_ingest_file(_file):
                            documents = self._read_file_to_documents(_file)
                            if documents:
                                self._store_documents_in_db(documents, _file)
                                yield documents
            elif self._is_valid_file(_file_path):
                if self._should_ingest_file(_file_path):
                    documents = self._read_file_to_documents(_file_path)
                    if documents:
                        self._store_documents_in_db(documents, _file_path)
                        yield documents

    @property
    async def async_document_lists(self) -> AsyncIterator[List[Document]]:
        """Async version - delegates to sync version as SQL operations are typically sync"""
        for doc_list in self.document_lists:
            yield doc_list
    
    def _read_file_to_documents(self, file_path: Path, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Read file content and convert to Document objects"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Create a single document for the entire file
            doc = Document(
                id=f"{file_path}_{datetime.now().isoformat()}",
                content=content,
                meta_data={
                    "filepath": str(file_path),
                    "filename": file_path.name,
                    "file_extension": file_path.suffix,
                    "file_size": len(content),
                    **(metadata or {})
                }
            )
            
            return [doc]
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return []
    
    def search(
        self, 
        query: str, 
        num_documents: Optional[int] = None, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search documents using SQL LIKE queries instead of vector similarity"""
        if not query.strip():
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            _num_documents = num_documents or self.num_documents
            
            # Build SQL query for text search
            sql_query = f'''
                SELECT DISTINCT doc_id, filepath, filename, content, meta_data 
                FROM {self.table_name}
                WHERE content LIKE ? OR filename LIKE ?
            '''
            params = [f'%{query}%', f'%{query}%']
            
            # Add filters if provided
            if filters:
                for key, value in filters.items():
                    if key == "filepath":
                        sql_query += " AND filepath LIKE ?"
                        params.append(f'%{value}%')
                    elif key == "filename":
                        sql_query += " AND filename LIKE ?"
                        params.append(f'%{value}%')
                    elif key == "file_extension":
                        sql_query += " AND filepath LIKE ?"
                        params.append(f'%{value}')
            
            sql_query += f" ORDER BY filename LIMIT {_num_documents}"
            
            cursor.execute(sql_query, params)
            results = cursor.fetchall()
            
            documents = []
            for doc_id, filepath, filename, content, meta_data_str in results:
                # Parse metadata
                meta_data = {}
                if meta_data_str:
                    try:
                        meta_data = eval(meta_data_str)  # Simple eval for dict strings
                    except:
                        pass
                
                doc = Document(
                    id=doc_id,
                    content=content,
                    meta_data=meta_data
                )
                documents.append(doc)
            
            log_info(f"Found {len(documents)} documents for query: {query}")
            return documents
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
        finally:
            conn.close()
    
    async def async_search(
        self, 
        query: str, 
        num_documents: Optional[int] = None, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Async search - delegates to sync version"""
        return self.search(query, num_documents, filters)
    
    def load(
        self,
        recreate: bool = False,
        upsert: bool = False,
        skip_existing: bool = True,
    ) -> None:
        """Load documents into the SQL database"""
        if recreate:
            log_info("Recreating SQL knowledge base")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self.table_name}")
            cursor.execute(f"DELETE FROM {self.metadata_table_name}")
            conn.commit()
            conn.close()
        
        log_info("Loading documents into SQL knowledge base")
        num_documents = 0
        for document_list in self.document_lists:
            num_documents += len(document_list)
        
        log_info(f"Loaded {num_documents} documents into SQL knowledge base")
    
    async def aload(
        self,
        recreate: bool = False,
        upsert: bool = False,
        skip_existing: bool = True,
    ) -> None:
        """Async load - delegates to sync version"""
        self.load(recreate, upsert, skip_existing)
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the current database state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get document count
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            doc_count = cursor.fetchone()[0]
            
            # Get file count
            cursor.execute(f"SELECT COUNT(DISTINCT filepath) FROM {self.table_name}")
            file_count = cursor.fetchone()[0]
            
            # Get latest ingestion time
            cursor.execute(f"SELECT MAX(last_ingested) FROM {self.metadata_table_name}")
            latest_ingestion = cursor.fetchone()[0]
            
            return {
                "document_count": doc_count,
                "file_count": file_count,
                "latest_ingestion": latest_ingestion,
                "database_path": self.db_path
            }
            
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {}
        finally:
            conn.close()
    
    def force_reingest(self) -> None:
        """Force re-ingestion of all files"""
        log_info("Force re-ingesting all files")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {self.table_name}")
        cursor.execute(f"DELETE FROM {self.metadata_table_name}")
        conn.commit()
        conn.close()
        
        # Reload all documents
        self.load(recreate=False)
