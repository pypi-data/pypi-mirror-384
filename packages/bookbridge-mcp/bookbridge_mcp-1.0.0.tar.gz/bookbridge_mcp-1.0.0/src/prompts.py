"""
Prompt Templates Module
Contains professional prompts for translation and document processing
"""

from typing import Dict, Any
import asyncio


class PromptTemplates:
    """Manages prompt templates for various translation and processing tasks"""
    
    def __init__(self):
        pass
    
    async def get_translation_prompt(
        self,
        source_lang: str = "Chinese",
        target_lang: str = "English",
        content_type: str = "book_chapter"
    ) -> str:
        """
        Get professional translation prompt
        
        Args:
            source_lang: Source language
            target_lang: Target language
            content_type: Type of content being translated
            
        Returns:
            Formatted translation prompt
        """
        
        # Base translation principles
        base_principles = """
        You are a professional literary translator with expertise in {source_language} to {target_language} translation.
        Your task is to provide accurate, fluent, and culturally appropriate translations that preserve the original meaning, tone, and style.
        """
        
        # Content-specific guidelines
        content_guidelines = {
            "book_chapter": """
            SPECIFIC GUIDELINES FOR BOOK TRANSLATION:
            - Maintain the narrative flow and literary style
            - Preserve character voices and dialogue authenticity  
            - Adapt cultural references appropriately for {target_language} readers
            - Keep chapter structure, paragraph breaks, and formatting
            - Translate idioms and metaphors to equivalent expressions when possible
            - Maintain consistent terminology for character names, places, and concepts
            """,
            
            "academic": """
            SPECIFIC GUIDELINES FOR ACADEMIC TRANSLATION:
            - Maintain academic tone and formal register
            - Preserve technical terminology and concepts
            - Keep citations and references intact
            - Ensure logical flow and argumentation clarity
            - Maintain precision in specialized vocabulary
            """,
            
            "technical": """
            SPECIFIC GUIDELINES FOR TECHNICAL TRANSLATION:
            - Preserve technical accuracy and precision
            - Keep technical terms consistent
            - Maintain step-by-step instructions clarity
            - Preserve formatting for code, formulas, and diagrams
            - Use standard technical terminology in {target_language}
            """,
            
            "business": """
            SPECIFIC GUIDELINES FOR BUSINESS TRANSLATION:
            - Maintain professional tone
            - Adapt business concepts to target market context
            - Preserve formal structure and protocols
            - Use appropriate business terminology
            - Maintain clarity for decision-making content
            """
        }
        
        # Quality standards
        quality_standards = """
        QUALITY STANDARDS:
        1. ACCURACY: Preserve all information and meaning from the source
        2. FLUENCY: Ensure natural, readable {target_language} that flows well
        3. CONSISTENCY: Use consistent terminology and style throughout
        4. CULTURAL ADAPTATION: Make appropriate cultural adjustments without losing authenticity
        5. FORMATTING: {preserve_formatting}
        
        TRANSLATION PROCESS:
        1. Read the entire text to understand context and tone
        2. Identify key terms, cultural references, and stylistic elements
        3. Translate while maintaining the author's voice and intent
        4. Review for accuracy, fluency, and consistency
        5. Make final adjustments for optimal readability
        
        Please provide ONLY the translation without explanations unless specifically requested.
        """
        
        # Combine all parts
        full_prompt = (
            base_principles +
            content_guidelines.get(content_type, content_guidelines["book_chapter"]) +
            quality_standards
        ).format(
            source_language=source_lang,
            target_language=target_lang,
            preserve_formatting="{preserve_formatting}"
        )
        
        return full_prompt
    
    async def get_quality_check_prompt(self) -> str:
        """Get translation quality assessment prompt"""
        
        return """
        You are a professional translation quality assessor. Evaluate the provided translation based on these criteria:

        EVALUATION CRITERIA:
        1. ACCURACY (25%): How well does the translation preserve the original meaning?
        2. FLUENCY (25%): How natural and readable is the target language?
        3. CONSISTENCY (20%): Is terminology and style consistent throughout?
        4. CULTURAL ADAPTATION (15%): Are cultural elements appropriately adapted?
        5. COMPLETENESS (15%): Is all information from the source preserved?

        SCORING SCALE:
        - 9-10: Excellent - Professional publication quality
        - 7-8: Good - Minor improvements needed
        - 5-6: Adequate - Noticeable issues but understandable
        - 3-4: Poor - Significant problems affecting comprehension
        - 1-2: Unacceptable - Major errors, requires complete revision

        Please provide:
        1. Overall score (1-10)
        2. Individual criterion scores
        3. Specific issues identified
        4. Suggestions for improvement
        5. Examples of excellent translation segments

        Format your response as JSON with the following structure:
        {
            "overall_score": 8.5,
            "criterion_scores": {
                "accuracy": 9,
                "fluency": 8,
                "consistency": 8,
                "cultural_adaptation": 9,
                "completeness": 9
            },
            "issues": ["List of specific issues"],
            "suggestions": ["List of improvement suggestions"],
            "excellent_segments": ["Examples of well-translated parts"]
        }
        """
    
    async def get_chapter_analysis_prompt(self) -> str:
        """Get chapter structure analysis prompt"""
        
        return """
        You are a literary analyst specializing in book chapter structure and content analysis.
        Analyze the provided chapter and identify its key components and characteristics.

        ANALYSIS AREAS:
        
        1. STRUCTURE ANALYSIS:
        - Chapter theme and main topics
        - Narrative structure (chronological, flashback, parallel, etc.)
        - Key scenes or sections
        - Transition methods between sections

        2. CONTENT ANALYSIS:
        - Main characters introduced or developed
        - Plot developments and story progression
        - Key dialogue and conversations
        - Important cultural or historical references

        3. STYLE ANALYSIS:
        - Writing tone and mood
        - Literary devices used (metaphors, symbolism, etc.)
        - Narrative voice and perspective
        - Pacing and rhythm

        4. TRANSLATION CONSIDERATIONS:
        - Cultural elements requiring adaptation
        - Idiomatic expressions and colloquialisms
        - Technical or specialized terminology
        - Formatting and structural elements to preserve

        5. DIFFICULTY ASSESSMENT:
        - Translation complexity level (1-10)
        - Potential challenging passages
        - Recommended translation approach
        - Special attention areas

        Please provide a comprehensive analysis that will help guide the translation process.
        Focus on elements that will impact translation decisions and quality.
        """
    
    async def get_formatting_preservation_prompt(self) -> str:
        """Get prompt for preserving document formatting"""
        
        return """
        FORMATTING PRESERVATION GUIDELINES:
        
        When translating, preserve the following formatting elements:
        
        1. STRUCTURE:
        - Headers and subheaders (# ## ### etc.)
        - Paragraph breaks and spacing
        - List formatting (bullet points, numbered lists)
        - Table structures
        - Quote blocks and indentation
        
        2. TEXT FORMATTING:
        - **Bold text** formatting
        - *Italic text* formatting
        - ***Bold and italic*** combinations
        - `Code or special terms` in backticks
        - Links: [text](URL) format
        
        3. DOCUMENT ELEMENTS:
        - Chapter numbers and titles
        - Section dividers
        - Footnotes and references
        - Image captions and alt text
        - Table headers and data organization
        
        4. SPECIAL CHARACTERS:
        - Preserve special punctuation
        - Maintain quotation mark styles appropriate for target language
        - Keep mathematical symbols and formulas
        - Preserve line breaks in poetry or formatted text
        
        IMPORTANT: Translate the CONTENT but keep the FORMATTING exactly as shown in the original.
        """
    
    async def get_batch_processing_prompt(self) -> str:
        """Get prompt for batch processing guidance"""
        
        return """
        BATCH PROCESSING GUIDELINES:
        
        You are processing multiple chapters from the same book. Maintain consistency across all chapters:
        
        1. TERMINOLOGY CONSISTENCY:
        - Character names: Keep consistent spellings and name choices
        - Place names: Use consistent geographical terms
        - Technical terms: Maintain the same translations throughout
        - Key concepts: Use consistent terminology for recurring themes
        
        2. STYLE CONSISTENCY:
        - Narrative voice: Maintain the same tone and perspective
        - Character voices: Keep distinct dialogue styles for each character
        - Writing style: Preserve the author's unique voice throughout
        
        3. CULTURAL ADAPTATIONS:
        - Apply the same cultural adaptation principles across chapters
        - Maintain consistent explanations for cultural concepts
        - Use the same approach for idiomatic expressions
        
        4. QUALITY STANDARDS:
        - Apply the same quality criteria to each chapter
        - Maintain consistent translation depth and accuracy
        - Ensure each chapter meets the same professional standards
        
        Remember: Each chapter should feel like part of a cohesive, professionally translated book.
        """
    
    async def get_revision_prompt(self) -> str:
        """Get prompt for translation revision and improvement"""
        
        return """
        You are reviewing and improving an existing translation. Your goal is to enhance quality while preserving the original translator's work where it's already good.

        REVISION FOCUS AREAS:
        
        1. ACCURACY IMPROVEMENTS:
        - Identify and correct mistranslations
        - Ensure all source content is preserved
        - Verify technical terms and proper nouns
        - Check cultural reference translations
        
        2. FLUENCY ENHANCEMENTS:
        - Improve sentence flow and readability
        - Eliminate awkward phrasing
        - Enhance natural language usage
        - Smooth transitions between ideas
        
        3. CONSISTENCY CHECKS:
        - Verify terminology consistency
        - Align style throughout the document
        - Ensure character voice consistency
        - Check formatting consistency
        
        4. CULTURAL ADAPTATION REVIEW:
        - Evaluate cultural reference handling
        - Improve idiomatic expression translations
        - Enhance cultural context explanations
        - Ensure appropriate cultural sensitivity
        
        REVISION PRINCIPLES:
        - Only change what needs improvement
        - Preserve good existing translations
        - Focus on significant quality gains
        - Maintain the original meaning and tone
        
        Provide the revised translation along with a brief summary of major changes made.
        """
    
    async def get_content_type_prompt(self, content_type: str) -> str:
        """Get prompt based on specific content type"""
        
        prompts = {
            "dialogue": """
            DIALOGUE TRANSLATION GUIDELINES:
            - Preserve character personality in speech patterns
            - Maintain formality levels and social relationships
            - Adapt slang and colloquialisms appropriately
            - Keep emotional tone and subtext
            - Preserve dialogue tags and action descriptions
            """,
            
            "description": """
            DESCRIPTIVE TEXT GUIDELINES:
            - Maintain vivid imagery and sensory details
            - Preserve atmosphere and mood
            - Adapt metaphors and similes effectively
            - Keep spatial and temporal relationships clear
            - Maintain the author's descriptive style
            """,
            
            "action": """
            ACTION SEQUENCE GUIDELINES:
            - Maintain pacing and urgency
            - Keep chronological sequence clear
            - Preserve tension and excitement
            - Adapt action verbs for maximum impact
            - Maintain clarity in complex action descriptions
            """,
            
            "exposition": """
            EXPOSITORY TEXT GUIDELINES:
            - Maintain logical flow of information
            - Preserve cause-and-effect relationships
            - Keep technical accuracy
            - Ensure clarity of complex concepts
            - Maintain educational or informative purpose
            """
        }
        
        return prompts.get(content_type, "")
    
    async def get_domain_specific_prompt(self, domain: str) -> str:
        """Get domain-specific translation guidelines"""
        
        domains = {
            "medical": """
            MEDICAL TRANSLATION GUIDELINES:
            - Maintain medical accuracy and terminology
            - Use standardized medical terms
            - Preserve dosage, measurement, and clinical information
            - Follow medical translation best practices
            - Ensure patient safety through accurate translation
            """,
            
            "legal": """
            LEGAL TRANSLATION GUIDELINES:
            - Maintain legal precision and accuracy
            - Use appropriate legal terminology
            - Preserve legal structure and hierarchy
            - Follow legal translation conventions
            - Note when legal concepts don't have direct equivalents
            """,
            
            "financial": """
            FINANCIAL TRANSLATION GUIDELINES:
            - Maintain financial accuracy and precision
            - Use standard financial terminology
            - Preserve numerical data and calculations
            - Follow financial reporting standards
            - Ensure regulatory compliance considerations
            """,
            
            "literary": """
            LITERARY TRANSLATION GUIDELINES:
            - Preserve artistic and creative elements
            - Maintain literary devices and techniques
            - Adapt poetic and metaphorical language
            - Keep author's unique voice and style
            - Balance fidelity with artistic expression
            """
        }
        
        return domains.get(domain, "")
