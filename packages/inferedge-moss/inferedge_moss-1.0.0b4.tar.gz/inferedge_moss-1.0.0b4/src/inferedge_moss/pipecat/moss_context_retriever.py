"""
Simple Moss Context Retriever for Pipecat
This processor enhances LLM messages with Moss search results.
"""

import asyncio
import os
from typing import Any

from loguru import logger
from pipecat.frames.frames import Frame, LLMMessagesFrame, TranscriptionFrame
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContextFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from ..client.moss_client import MossClient


class MossContextRetriever(FrameProcessor):
    """Simple processor that enhances LLM messages with Moss context"""

    def __init__(self, project_id: str, project_key: str, index_name: str, **kwargs):
        super().__init__(**kwargs)
        self.project_id = project_id
        self.project_key = project_key
        self.index_name = index_name
        self.moss_client = None
        self._initialized = False
        self.pending_context = None  # Store context to inject into next LLM call
        logger.debug("🔍 MossContextRetriever initialized")

    async def initialize_index(self):
        """Initialize the Moss client and index. Call this once at application startup."""
        try:
            logger.debug(
                f"🔧 Moss - Project: {self.project_id[:8] if self.project_id else None}, Key: {'***' if self.project_key else None}, Index: {self.index_name}"
            )

            if not all([self.project_id, self.project_key, self.index_name]):
                missing = []
                if not self.project_id:
                    missing.append("project_id")
                if not self.project_key:
                    missing.append("project_key")
                if not self.index_name:
                    missing.append("index_name")
                error_msg = f"Missing required Moss parameters: {missing}"
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)

            logger.debug("🚀 Moss: Initializing Moss client...")
            self.moss_client = MossClient(self.project_id, self.project_key)
            logger.debug("✅ Moss: Moss client ready")

            # Load the index
            logger.debug(f"🔄 Moss: Loading index: {self.index_name}")
            await self.moss_client.load_index(self.index_name)
            self._initialized = True
            logger.info(f"✅ Moss: Index '{self.index_name}' loaded successfully")

        except Exception as e:
            logger.error(f"❌ Moss: Failed to initialize: {e}")
            self._initialized = False
            raise

    def is_ready(self) -> bool:
        """Check if Moss is ready to process queries"""
        return self._initialized and self.moss_client is not None

    async def _enhance_with_moss_context(
        self, frame: OpenAILLMContextFrame, direction: FrameDirection
    ):
        """Enhance OpenAI LLM context frame with Moss semantic search context"""
        context = frame.context
        messages = context.messages

        # Find the most recent user message to use for retrieval
        user_query = None
        for message in reversed(messages):
            if message.get("role") == "user":
                user_query = message.get("content", "").strip()
                break

        if not user_query:
            logger.debug(
                "📭 MossContextRetriever: No user query found, passing frame unchanged"
            )
            await self.push_frame(frame, direction)
            return

        logger.debug(
            f"🔍 MossContextRetriever: Enhancing LLM context for user query: '{user_query}'"
        )

        try:
            # Check if Moss is ready
            if not self.is_ready():
                logger.error(
                    "⚠️ MossContextRetriever: Moss not initialized properly, skipping enhancement"
                )
                await self.push_frame(frame, direction)
                return

            # Query Moss
            logger.debug(
                f"📡 MossContextRetriever: Querying Moss index '{self.index_name}'"
            )

            results = await self.moss_client.query(
                self.index_name,
                user_query,
                5,  # Top 5 results
            )

            logger.debug(
                f"📊 MossContextRetriever: Moss returned {len(results.docs)} results"
            )

            # Build context from results
            if results.docs:
                context_parts = [
                    "Here is relevant information from our knowledge base:"
                ]
                current_length = len(context_parts[0])
                max_context_length = 1500

                for i, doc in enumerate(results.docs):
                    logger.debug(
                        f"📄 MossContextRetriever: Doc {i+1}: score={doc.score:.3f}"
                    )
                    logger.debug(
                        f"📝 MossContextRetriever: Doc {i+1} content: {doc.text}"
                    )

                    faq_text = f"\n\n- {doc.text}"

                    if current_length + len(faq_text) <= max_context_length:
                        context_parts.append(faq_text)
                        current_length += len(faq_text)
                        logger.debug(f"✅ MossContextRetriever: Added doc {i+1}")
                    else:
                        logger.debug(
                            f"⏭️ MossContextRetriever: Skipping doc {i+1} - would exceed max length"
                        )
                        break

                moss_context = "".join(context_parts)
                logger.debug(
                    f"📤 MossContextRetriever: Full context being added: {moss_context}"
                )

                # Enhance the system message with Moss context
                enhanced_messages = self._add_context_to_messages(
                    messages, moss_context
                )

                # Update the context with enhanced messages
                # Since context.messages might be read-only, we'll modify the messages list in place
                context.messages.clear()
                context.messages.extend(enhanced_messages)

                logger.debug(
                    "✅ MossContextRetriever: OpenAI LLM context enhanced with Moss context"
                )
                await self.push_frame(frame, direction)
            else:
                logger.debug(
                    "📭 MossContextRetriever: No Moss results, passing original frame"
                )
                await self.push_frame(frame, direction)

        except Exception as e:
            logger.error(
                f"❌ MossContextRetriever: Failed to enhance with Moss context: {e}"
            )
            # Fall back to original frame if Moss fails
            await self.push_frame(frame, direction)

    def _add_context_to_messages(self, messages: list, moss_context: str) -> list:
        """Add Moss context to the system message"""
        enhanced_messages = []
        context_added = False

        for message in messages:
            if message.get("role") == "system" and not context_added:
                # Enhance the first system message with Moss context
                original_content = message.get("content", "")
                enhanced_content = f"{original_content}\n\n{moss_context}"

                enhanced_message = message.copy()
                enhanced_message["content"] = enhanced_content
                enhanced_messages.append(enhanced_message)
                context_added = True

                logger.debug(
                    f"📝 MossContextRetriever: Added Moss context to system message ({len(moss_context)} chars)"
                )
            else:
                enhanced_messages.append(message)

        # If no system message found, add context as new system message
        if not context_added:
            context_message = {
                "role": "system",
                "content": f"Use the following information to help answer the user's question:\n\n{moss_context}",
            }
            enhanced_messages.insert(0, context_message)
            logger.debug(
                f"📝 MossContextRetriever: Added new system message with Moss context ({len(moss_context)} chars)"
            )

        return enhanced_messages

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process frames and enhance context before LLM processing"""

        # Always call parent first to handle StartFrame and other system frames
        await super().process_frame(frame, direction)

        # Handle OpenAILLMContextFrame to inject Moss context before LLM processing
        if isinstance(frame, OpenAILLMContextFrame):
            logger.debug(
                f"🎯 MossContextRetriever: Processing OpenAI LLM context frame"
            )
            await self._enhance_with_moss_context(frame, direction)
        else:
            # Pass through all other frames unchanged
            await self.push_frame(frame, direction)

    async def _inject_context_into_llm(
        self, frame: LLMMessagesFrame, direction: FrameDirection
    ):
        """Inject stored Moss context into LLM messages as system message"""
        try:
            messages = frame.messages.copy()

            # Add context as a system message before the user message
            context_message = {
                "role": "system",
                "content": f"Use this information to help answer the user's question: {self.pending_context}",
            }

            # Insert context before the last message (which should be the user query)
            if messages:
                messages.insert(-1, context_message)
            else:
                messages.append(context_message)

            # Create new frame with enhanced messages
            enhanced_frame = LLMMessagesFrame(messages)

            logger.debug(f"✅ MossContextRetriever: Injected context into LLM messages")

            # Clear pending context
            self.pending_context = None

            await self.push_frame(enhanced_frame, direction)

        except Exception as e:
            logger.error(f"❌ MossContextRetriever: Failed to inject context: {e}")
            # Clear pending context and pass original frame
            self.pending_context = None
            await self.push_frame(frame, direction)
