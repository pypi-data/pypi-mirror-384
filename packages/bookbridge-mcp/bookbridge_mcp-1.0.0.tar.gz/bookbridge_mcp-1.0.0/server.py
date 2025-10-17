"""
BookBridge-MCP Server
A FastMCP-based server for book translation document processing
Client-side LLM interaction architecture - Server provides tools, resources, and prompts only
"""

import asyncio
import hashlib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastmcp import FastMCP
from dotenv import load_dotenv

from src.document_processor import DocumentProcessor
from src.resource_manager import ResourceManager
from src.prompts import PromptTemplates

# Load environment variables
load_dotenv('config.env')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bookbridge_mcp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BookBridgeMCPServer:
    """
    BookBridge MCP Server - Document Processing and Resource Management
    
    This server provides Tools, Resources, and Prompts for book translation workflow.
    LLM interactions are handled client-side for better separation of concerns.
    """
    
    def __init__(self):
        """Initialize the BookBridge MCP Server with all required components."""
        # Initialize FastMCP server
        self.mcp = FastMCP("BookBridge-MCP")
        
        # Initialize components (without translator - client-side LLM)
        self.doc_processor = DocumentProcessor()
        self.resource_manager = ResourceManager()
        self.prompts = PromptTemplates()
        
        # Server statistics
        self.stats = {
            "start_time": datetime.now(),
            "documents_processed": 0,
            "resources_accessed": 0,
            "prompts_generated": 0,
            "total_requests": 0
        }
        
        # Create directories if they don't exist
        self._setup_directories()
        
        # Register all MCP elements
        self._register_tools()
        self._register_resources()
        self._register_prompts()
        
        logger.info("BookBridge MCP Server initialized with client-side LLM architecture")

    def _setup_directories(self):
        """Setup required directories"""
        dirs = [
            os.getenv('INPUT_DIR', './input_documents'),
            os.getenv('OUTPUT_DIR', './output_documents'),
            os.getenv('TEMP_DIR', './temp_documents')
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _get_absolute_path(self, config_key: str, default_relative_path: str) -> str:
        """Get absolute path from environment or default relative path"""
        env_path = os.getenv(config_key)
        if env_path:
            return str(Path(env_path).absolute())
        
        # Fallback to script directory based absolute path
        script_dir = Path(__file__).parent.absolute()
        return str(script_dir / default_relative_path.lstrip('./'))

    async def _get_document_content_impl(self, document_path: str) -> Dict[str, Any]:
        """
        Internal implementation of document content extraction.
        This is shared between tools and batch processing.
        """
        try:
            doc_path = Path(document_path)
            if not doc_path.exists():
                return {
                    "status": "error",
                    "message": f"Document not found: {document_path}"
                }
            
            # Read document content based on type
            if doc_path.suffix.lower() in ['.md', '.txt']:
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            elif doc_path.suffix.lower() == '.docx':
                # Convert to markdown first for easier processing
                result = await self.doc_processor.word_to_markdown(str(doc_path))
                content = result["content"]
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported file type: {doc_path.suffix}"
                }
            
            return {
                "status": "success",
                "document_path": str(doc_path),
                "content": content,
                "file_size": doc_path.stat().st_size,
                "file_type": doc_path.suffix.lower(),
                "modified": datetime.fromtimestamp(doc_path.stat().st_mtime).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting document content: {e}")
            return {
                "status": "error",
                "message": f"Failed to get document content: {str(e)}"
            }

    def _scan_documents_impl(self, directory: str = None) -> Dict[str, Any]:
        """
        Internal implementation of document scanning functionality.
        This is shared between tools and resources.
        """
        try:
            # Use provided directory or default from config
            if directory:
                scan_dir = directory
            else:
                scan_dir = os.getenv('INPUT_DIR', './input_documents')
            
            scan_path = Path(scan_dir)
            logger.info(f"Scanning directory: {scan_path.absolute()}")
            
            if not scan_path.exists():
                logger.error(f"Directory does not exist: {scan_path.absolute()}")
                return {
                    "success": False,
                    "error": f"Directory does not exist: {scan_dir}",
                    "documents": [],
                    "statistics": {}
                }
            
            # Scan for supported document types
            supported_extensions = ['.docx', '.doc', '.md', '.txt']
            documents = []
            stats_by_type = {}
            
            for ext in supported_extensions:
                files = list(scan_path.rglob(f'*{ext}'))
                stats_by_type[ext] = len(files)
                
                for file_path in files:
                    # Generate stable ID based on absolute path MD5 hash
                    abs_path = str(file_path.absolute())
                    file_id = hashlib.md5(abs_path.encode('utf-8')).hexdigest()
                    documents.append({
                        "file_id": file_id,
                        "name": file_path.name,
                        "path": abs_path,
                        "type": ext,
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
            
            result = {
                "success": True,
                "directory": str(scan_path),
                "documents": documents,
                "statistics": {
                    "total_files": len(documents),
                    "by_type": stats_by_type,
                    "scan_time": datetime.now().isoformat()
                }
            }
            
            logger.info(f"Scanned {len(documents)} documents in {scan_dir}")
            return result
            
        except Exception as e:
            logger.error(f"Error scanning documents: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "documents": [],
                "statistics": {}
            }

    # ============================================================================
    # TOOLS: Operations Execution Layer
    # ============================================================================
    
    def _register_tools(self):
        """Register all MCP tools for operations execution."""
        
        @self.mcp.tool()
        def scan_documents(directory: str = None) -> Dict[str, Any]:
            """
            Scan and discover documents in specified directory.
            
            Args:
                directory: Target directory path (optional, uses config default)
                
            Returns:
                Document inventory with statistics and file list
            """
            self.stats["total_requests"] += 1
            return self._scan_documents_impl(directory)
        
        @self.mcp.tool()
        async def word_to_markdown(document_path: str) -> Dict[str, Any]:
            """
            Convert a Word document to Markdown format
            
            Args:
                document_path: Path to the Word document (.docx)
            
            Returns:
                Dictionary with conversion status and output path
            """
            try:
                self.stats["total_requests"] += 1
                logger.info(f"Converting Word to Markdown: {document_path}")
                result = await self.doc_processor.word_to_markdown(document_path)
                return {
                    "status": "success",
                    "message": "Word document successfully converted to Markdown",
                    "output_path": result["output_path"],
                    "content_preview": result["content"][:500] + "..." if len(result["content"]) > 500 else result["content"]
                }
            except Exception as e:
                logger.error(f"Error converting Word to Markdown: {e}")
                return {
                    "status": "error",
                    "message": f"Failed to convert document: {str(e)}"
                }

        @self.mcp.tool()
        async def markdown_to_word(
            markdown_path: str,
            output_path: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Convert a Markdown document to Word format
            
            Args:
                markdown_path: Path to the Markdown file
                output_path: Optional output path for the Word document
            
            Returns:
                Dictionary with conversion status and output path
            """
            try:
                self.stats["total_requests"] += 1
                logger.info(f"Converting Markdown to Word: {markdown_path}")
                result = await self.doc_processor.markdown_to_word(markdown_path, output_path)
                
                return {
                    "status": "success",
                    "message": "Markdown document successfully converted to Word",
                    "output_path": result["output_path"],
                    "page_count": result.get("page_count", "Unknown"),
                    "word_count": result.get("word_count", "Unknown")
                }
                
            except Exception as e:
                logger.error(f"Error converting Markdown to Word: {e}")
                return {
                    "status": "error",
                    "message": f"Failed to convert document: {str(e)}"
                }

        @self.mcp.tool()
        async def get_document_content(document_path: str) -> Dict[str, Any]:
            """
            Get document content for client-side processing
            
            Args:
                document_path: Path to the document
            
            Returns:
                Dictionary with document content and metadata
            """
            self.stats["total_requests"] += 1
            return await self._get_document_content_impl(document_path)

        @self.mcp.tool()
        async def save_translated_content(
            original_path: str,
            translated_content: str,
            target_language: str = "english",
            output_format: str = "markdown"
        ) -> Dict[str, Any]:
            """
            Save translated content to appropriate format
            
            Args:
                original_path: Path to original document
                translated_content: Translated content from client
                target_language: Target language name
                output_format: Output format (markdown or word)
            
            Returns:
                Dictionary with save status and output path
            """
            try:
                self.stats["total_requests"] += 1
                
                original_file = Path(original_path)
                output_dir = Path(os.getenv('OUTPUT_DIR', './output_documents'))
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate output filename
                base_name = original_file.stem
                
                if output_format == "markdown":
                    output_file = output_dir / f"{base_name}_{target_language}.md"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(translated_content)
                    
                    return {
                        "status": "success",
                        "message": "Translated content saved as Markdown",
                        "output_path": str(output_file),
                        "format": "markdown"
                    }
                
                elif output_format == "word":
                    # Save as markdown first, then convert to Word
                    temp_md = output_dir / f"{base_name}_{target_language}_temp.md"
                    with open(temp_md, 'w', encoding='utf-8') as f:
                        f.write(translated_content)
                    
                    # Convert to Word
                    word_result = await self.doc_processor.markdown_to_word(
                        str(temp_md), 
                        str(output_dir / f"{base_name}_{target_language}.docx")
                    )
                    
                    # Clean up temp file
                    temp_md.unlink()
                    
                    return {
                        "status": "success", 
                        "message": "Translated content saved as Word document",
                        "output_path": word_result["output_path"],
                        "format": "word",
                        "word_count": word_result.get("word_count", "Unknown")
                    }
                
                else:
                    return {
                        "status": "error",
                        "message": f"Unsupported output format: {output_format}"
                    }
                    
            except Exception as e:
                logger.error(f"Error saving translated content: {e}")
                return {
                    "status": "error",
                    "message": f"Failed to save translated content: {str(e)}"
                }

        @self.mcp.tool()
        async def batch_prepare_documents(
            input_directory: str,
            file_pattern: str = "*.docx"
        ) -> Dict[str, Any]:
            """
            Prepare multiple documents for batch translation (client-side processing)
            
            Args:
                input_directory: Directory containing source documents
                file_pattern: File pattern to match (e.g., "*.docx")
            
            Returns:
                Dictionary with document list and preparation results
            """
            try:
                self.stats["total_requests"] += 1
                
                input_path = Path(input_directory)
                if not input_path.exists():
                    return {
                        "status": "error",
                        "message": f"Input directory not found: {input_directory}"
                    }
                
                # Find matching files
                files = list(input_path.glob(file_pattern))
                if not files:
                    return {
                        "status": "warning",
                        "message": f"No files matching pattern '{file_pattern}' found",
                        "documents": []
                    }
                
                prepared_docs = []
                
                for file_path in files:
                    try:
                        # Get document content for each file directly
                        doc_result = await self._get_document_content_impl(str(file_path))
                        
                        if doc_result["status"] == "success":
                            prepared_docs.append({
                                "file_id": hashlib.md5(str(file_path.absolute()).encode('utf-8')).hexdigest(),
                                "name": file_path.name,
                                "path": str(file_path),
                                "content": doc_result["content"],
                                "file_size": doc_result["file_size"],
                                "file_type": doc_result["file_type"],
                                "status": "ready"
                            })
                        else:
                            prepared_docs.append({
                                "file_id": hashlib.md5(str(file_path.absolute()).encode('utf-8')).hexdigest(),
                                "name": file_path.name,
                                "path": str(file_path),
                                "status": "error",
                                "error": doc_result.get("message", "Unknown error")
                            })
                            
                    except Exception as e:
                        prepared_docs.append({
                            "file_id": hashlib.md5(str(file_path.absolute()).encode('utf-8')).hexdigest(),
                            "name": file_path.name,
                            "path": str(file_path),
                            "status": "error",
                            "error": str(e)
                        })
                
                success_count = sum(1 for d in prepared_docs if d.get("status") == "ready")
                
                return {
                    "status": "completed",
                    "message": f"Prepared {success_count}/{len(files)} documents for processing",
                    "total_files": len(files),
                    "ready_files": success_count,
                    "error_files": len(files) - success_count,
                    "documents": prepared_docs
                }
                
            except Exception as e:
                logger.error(f"Error in batch preparation: {e}")
                return {
                    "status": "error",
                    "message": f"Batch preparation failed: {str(e)}"
                }

        @self.mcp.tool()
        async def list_documents() -> Dict[str, Any]:
            """
            List all available documents in the system
            
            Returns:
                Dictionary with document listings
            """
            try:
                self.stats["total_requests"] += 1
                documents = await self.resource_manager.list_all_documents()
                return {
                    "status": "success",
                    "documents": documents
                }
            except Exception as e:
                logger.error(f"Error listing documents: {e}")
                return {
                    "status": "error",
                    "message": f"Failed to list documents: {str(e)}"
                }

    # ============================================================================
    # RESOURCES: Data Access Layer
    # ============================================================================
    
    def _register_resources(self):
        """Register all MCP resources for data access."""
        
        @self.mcp.resource("document://{doc_id}")
        def get_document(doc_id: str) -> Dict[str, Any]:
            """
            Get specific document content by ID.
            
            Args:
                doc_id: Document identifier
                
            Returns:
                Document content and metadata
            """
            try:
                self.stats["resources_accessed"] += 1
                
                # Find document by ID through scanning
                scan_result = self._scan_documents_impl()
                doc_info = None
                
                for doc in scan_result.get("documents", []):
                    if doc["file_id"] == doc_id:
                        doc_info = doc
                        break
                
                if not doc_info:
                    return {
                        "success": False,
                        "error": f"Document not found: {doc_id}",
                        "content": None
                    }
                
                # Get document content
                doc_path = Path(doc_info["path"])
                content = {
                    "document_id": doc_id,
                    "metadata": doc_info,
                    "raw_available": doc_path.exists()
                }
                
                # Include raw content if available
                if doc_path.exists():
                    try:
                        if doc_path.suffix.lower() in ['.md', '.txt']:
                            with open(doc_path, 'r', encoding='utf-8') as f:
                                content["raw_content"] = f.read()
                        elif doc_path.suffix.lower() == '.docx':
                            # Convert to markdown for easier client processing
                            try:
                                # Since we can't use async in resource functions, 
                                # we'll provide a note that conversion is available via tools
                                content["conversion_available"] = True
                                content["note"] = "Use word_to_markdown tool for content extraction"
                            except Exception as e:
                                content["conversion_error"] = str(e)
                    except Exception as e:
                        content["content_error"] = str(e)
                
                return {
                    "success": True,
                    "uri": f"document://{doc_id}",
                    "content": content,
                    "access_time": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error accessing document resource: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "content": None
                }
        
        @self.mcp.resource("documents://list")
        def get_document_list() -> Dict[str, Any]:
            """
            Get list of all available documents.
            
            Returns:
                List of documents with metadata
            """
            try:
                self.stats["resources_accessed"] += 1
                
                # Get all documents from configured directories
                scan_result = self._scan_documents_impl()
                
                return {
                    "success": True,
                    "uri": "documents://list",
                    "documents": scan_result.get("documents", []),
                    "statistics": scan_result.get("statistics", {}),
                    "access_time": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error accessing document list resource: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "documents": []
                }
        
        @self.mcp.resource("config://server/status")
        def get_server_status() -> Dict[str, Any]:
            """
            Get comprehensive server status and configuration.
            
            Returns:
                Server status, statistics, and configuration
            """
            try:
                self.stats["resources_accessed"] += 1
                
                uptime = datetime.now() - self.stats["start_time"]
                
                status = {
                    "server_info": {
                        "name": "BookBridge-MCP",
                        "version": "1.0.0",
                        "protocol": "MCP Standard",
                        "framework": "FastMCP",
                        "architecture": "Client-side LLM",
                        "start_time": self.stats["start_time"].isoformat(),
                        "uptime_seconds": int(uptime.total_seconds())
                    },
                    "statistics": {
                        "total_requests": self.stats["total_requests"],
                        "documents_processed": self.stats["documents_processed"],
                        "resources_accessed": self.stats["resources_accessed"],
                        "prompts_generated": self.stats["prompts_generated"]
                    },
                    "configuration": {
                        "input_dir": os.getenv('INPUT_DIR', './input_documents'),
                        "output_dir": os.getenv('OUTPUT_DIR', './output_documents'),
                        "temp_dir": os.getenv('TEMP_DIR', './temp_documents'),
                        "supported_formats": ['.docx', '.doc', '.md', '.txt']
                    },
                    "capabilities": {
                        "tools": [
                            "scan_documents", 
                            "word_to_markdown", 
                            "markdown_to_word",
                            "get_document_content",
                            "save_translated_content",
                            "batch_prepare_documents",
                            "list_documents"
                        ],
                        "resources": [
                            "document://", 
                            "documents://list", 
                            "config://server/status"
                        ],
                        "prompts": [
                            "translation_prompt", 
                            "quality_check_prompt",
                            "chapter_analysis_prompt"
                        ]
                    },
                    "health": {
                        "status": "healthy",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                return {
                    "success": True,
                    "uri": "config://server/status",
                    "status": status,
                    "access_time": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error accessing server status resource: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "status": None
                }

    # ============================================================================
    # PROMPTS: AI Interaction Template Layer (for Client-side LLM)
    # ============================================================================
    
    def _register_prompts(self):
        """Register all MCP prompts for AI interaction templates."""
        
        @self.mcp.prompt("translation_prompt")
        def translation_prompt_template(
            source_language: str = "Chinese",
            target_language: str = "English",
            content_type: str = "book_chapter"
        ) -> str:
            """Professional translation prompt template for client-side LLM"""
            # Since prompts can't be async, we'll create the prompt directly
            self.stats["prompts_generated"] += 1
            
            prompt = f"""You are a professional translator specializing in {source_language} to {target_language} translation.

**Translation Task:**
- Source Language: {source_language}
- Target Language: {target_language}
- Content Type: {content_type}

**Quality Standards:**
1. **Accuracy**: Maintain the original meaning and context
2. **Fluency**: Produce natural, readable {target_language}
3. **Style**: Preserve the author's voice and tone
4. **Consistency**: Use consistent terminology throughout

**Content-Specific Guidelines:**
"""
            
            if content_type == "book_chapter":
                prompt += """
- Preserve chapter structure and formatting
- Maintain character names and dialogue style
- Keep cultural context when appropriate
- Ensure narrative flow remains engaging"""
            elif content_type == "academic":
                prompt += """
- Maintain academic tone and terminology
- Preserve citations and references
- Keep technical terms accurate
- Ensure logical structure is clear"""
            elif content_type == "technical":
                prompt += """
- Preserve technical accuracy
- Maintain step-by-step instructions
- Keep code examples intact
- Ensure clarity for technical audience"""
            elif content_type == "creative":
                prompt += """
- Preserve creative voice and style
- Maintain emotional impact
- Keep literary devices when possible
- Ensure artistic intent is preserved"""
            else:
                prompt += """
- Maintain appropriate tone for content
- Preserve structure and formatting
- Ensure clarity and readability
- Keep original intent intact"""
            
            prompt += f"""

**Instructions:**
1. Translate the provided {source_language} text to {target_language}
2. Maintain all markdown formatting if present
3. Preserve paragraph breaks and structure
4. Provide natural, fluent translation
5. Note any cultural references that need explanation

Begin translation:"""
            
            return prompt
        
        @self.mcp.prompt("quality_check_prompt")
        def quality_check_prompt_template() -> str:
            """Translation quality assessment prompt for client-side LLM"""
            self.stats["prompts_generated"] += 1
            return """You are a translation quality assessor. Review the provided translation and evaluate it based on:

**Quality Criteria:**
1. **Accuracy** (1-10): How well does the translation preserve the original meaning?
2. **Fluency** (1-10): How natural and readable is the target language?
3. **Consistency** (1-10): Is terminology and style consistent throughout?
4. **Completeness** (1-10): Are all parts of the source text translated?

**Assessment Format:**
- Accuracy: [score]/10 - [brief explanation]
- Fluency: [score]/10 - [brief explanation]  
- Consistency: [score]/10 - [brief explanation]
- Completeness: [score]/10 - [brief explanation]

**Overall Quality:** [average score]/10

**Recommendations:**
- List specific areas for improvement
- Suggest alternative translations for problematic sections
- Note any cultural or contextual considerations

**Summary:**
Provide a brief overall assessment and recommendation (Accept/Revise/Reject).
"""
        
        @self.mcp.prompt("chapter_analysis_prompt")
        def chapter_analysis_prompt_template() -> str:
            """Chapter structure analysis prompt for client-side LLM"""
            self.stats["prompts_generated"] += 1
            return """You are a literary analyst specializing in chapter structure and content analysis.

**Analysis Task:**
Analyze the provided chapter and identify:

**1. Structure Elements:**
- Chapter title and number
- Section breaks and subheadings
- Paragraph organization
- Dialogue vs. narrative distribution

**2. Content Analysis:**
- Main themes and topics
- Key characters introduced or developed
- Plot advancement and story beats
- Setting and time references

**3. Translation Considerations:**
- Cultural references that need context
- Idiomatic expressions requiring adaptation
- Technical or specialized terminology
- Emotional tone and style elements

**4. Formatting Notes:**
- Special formatting (emphasis, lists, etc.)
- Chapter transitions and breaks
- Any non-text elements to preserve

**Output Format:**
Structure: [brief description]
Content: [key themes and plot points]
Translation Notes: [specific considerations]
Formatting: [elements to preserve]

**Recommendation:**
Suggested approach for translating this chapter effectively.
"""

        @self.mcp.prompt("batch_translation_prompt")
        def batch_translation_prompt_template(
            document_count: int,
            source_language: str = "Chinese", 
            target_language: str = "English"
        ) -> str:
            """Batch translation coordination prompt for client-side LLM"""
            prompt = f"""You are coordinating the translation of {document_count} documents from {source_language} to {target_language}.

**Batch Translation Guidelines:**

1. **Consistency Management:**
   - Maintain consistent terminology across all documents
   - Keep character names, place names, and technical terms uniform
   - Create a glossary for recurring terms

2. **Quality Standards:**
   - Apply the same quality criteria to each document
   - Ensure uniform translation depth and style
   - Maintain the author's voice throughout the series

3. **Workflow Coordination:**
   - Process documents in logical order when possible
   - Track translation decisions for consistency
   - Review and adjust terminology as needed

4. **Progress Tracking:**
   - Report progress after each document
   - Note any terminology or style decisions made
   - Flag any issues that might affect other documents

5. **Final Review:**
   - Ensure consistency across the entire batch
   - Verify terminology usage is uniform
   - Check for overall coherence and flow

Remember: Each document should feel like part of a cohesive, professionally translated series."""
            
            self.stats["prompts_generated"] += 1
            return prompt

    # ============================================================================
    # Server Management
    # ============================================================================
    
    def run(self):
        """Run the MCP server."""
        try:
            logger.info("Starting BookBridge MCP Server via stdio transport...")
            self.mcp.run()
        except Exception as e:
            logger.error(f"Error running server: {str(e)}")
            raise
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get server capabilities summary."""
        return {
            "server_info": {
                "name": "BookBridge-MCP",
                "version": "1.0.0",
                "protocol": "MCP Standard",
                "framework": "FastMCP",
                "architecture": "Client-side LLM"
            },
            "tools": {
                "scan_documents": "Document discovery and listing",
                "word_to_markdown": "Convert Word documents to Markdown",
                "markdown_to_word": "Convert Markdown to Word documents", 
                "get_document_content": "Extract document content for processing",
                "save_translated_content": "Save client-translated content",
                "batch_prepare_documents": "Prepare documents for batch processing",
                "list_documents": "List available documents"
            },
            "resources": {
                "document://": "Individual document access by ID",
                "documents://list": "List of available documents",
                "config://server/status": "Server status and configuration"
            },
            "prompts": {
                "translation_prompt": "Professional translation templates",
                "quality_check_prompt": "Translation quality assessment",
                "chapter_analysis_prompt": "Chapter structure analysis",
                "batch_translation_prompt": "Batch translation coordination"
            },
            "features": [
                "Client-side LLM architecture", 
                "Document format conversion",
                "Resource-based document access",
                "Professional translation prompts",
                "Batch processing support"
            ]
        }


def main():
    """Main entry point for the BookBridge MCP Server."""
    try:
        # Create and configure server
        server = BookBridgeMCPServer()
        
        # Log server capabilities
        capabilities = server.get_capabilities()
        logger.info("BookBridge MCP Server Capabilities:")
        logger.info(json.dumps(capabilities, indent=2))
        
        # Run server
        logger.info("Starting BookBridge MCP Server...")
        server.run()
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
