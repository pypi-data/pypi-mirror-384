"""
Chainlit Knowledge Cancellation Test Example

This example demonstrates the knowledge operation cancellation functionality.
It includes slow operations that can be cancelled to test the implementation.

To run this example:
1. Install Chainlit: pip install chainlit
2. Run: chainlit run example_cancel_test.py
3. Open the web interface
4. Try creating/updating/deleting knowledge items
5. Test cancelling operations while they're running

The operations are intentionally slow (5-10 seconds) to give you time to test cancellation.
"""

import chainlit as cl
import asyncio
from typing import Dict, Any
import random
import time
from chainlit.knowledge import KnowledgeSettings, KnowledgeType
from chainlit.input_widget import TextInput, Select
from chainlit.context import context


@cl.on_knowledge_create
async def handle_create(data: Dict[str, Any]) -> str:
    """Slow knowledge creation for testing cancellation - takes ~8 seconds"""

    # Simulate a slow operation like file processing, API calls, etc.
    content = data.get("content", "")
    title = data.get("title", "Untitled")

    # Generate a knowledge ID based on content
    knowledge_id = f"knowledge_{abs(hash(content + title)) % 10000}"

    print(f"🚀 Starting knowledge creation: '{title}' (ID: {knowledge_id})")

    # Simulate processing in chunks so cancellation can be responsive
    total_steps = 80  # 8 seconds at 0.1s per step
    for i in range(total_steps):
        # Check for cancellation every step
        await asyncio.sleep(0.1)
        progress = ((i + 1) / total_steps) * 100
        if i % 10 == 0:  # Log every second
            print(f"📄 Creating '{title}': {progress:.0f}% complete...")

    print(f"✅ Knowledge creation completed: '{title}' (ID: {knowledge_id})")
    return knowledge_id


@cl.on_knowledge_update
async def handle_update(knowledge_id: str, updates: Dict[str, Any]):
    """Slow knowledge update for testing cancellation - takes ~6 seconds"""

    title = updates.get("title", "Unknown")
    print(f"🔄 Starting knowledge update: '{title}' (ID: {knowledge_id})")

    # Simulate update processing
    total_steps = 60  # 6 seconds at 0.1s per step
    for i in range(total_steps):
        await asyncio.sleep(0.1)
        progress = ((i + 1) / total_steps) * 100
        if i % 10 == 0:  # Log every second
            print(f"📝 Updating '{title}': {progress:.0f}% complete...")

    print(f"✅ Knowledge update completed: '{title}' (ID: {knowledge_id})")


@cl.on_knowledge_delete
async def handle_delete(knowledge_id: str):
    """Slow knowledge deletion for testing cancellation - takes ~4 seconds"""

    print(f"🗑️ Starting knowledge deletion: ID {knowledge_id}")

    # Simulate deletion processing
    total_steps = 40  # 4 seconds at 0.1s per step
    for i in range(total_steps):
        await asyncio.sleep(0.1)
        progress = ((i + 1) / total_steps) * 100
        if i % 10 == 0:  # Log every second
            print(f"🗑️ Deleting {knowledge_id}: {progress:.0f}% complete...")

    print(f"✅ Knowledge deletion completed: ID {knowledge_id}")


@cl.on_knowledge_select
async def handle_select(knowledge_ids: list[str]):
    """Handle knowledge selection - this is fast and doesn't need cancellation"""
    print(f"📋 Selected knowledge items: {', '.join(knowledge_ids)}")


@cl.on_chat_start
async def start():
    """Set up the chat session with knowledge types for testing"""

    # Set up knowledge types that will trigger our slow handlers
    knowledge_types = [
        KnowledgeType(
            type="text_document",
            label="Text Document",
            description="Upload a text document (slow processing - 8 seconds)",
            icon="📄",
            inputs=[
                TextInput(
                    id="title",
                    label="Document Title",
                    placeholder="Enter a descriptive title"
                ),
                TextInput(
                    id="content",
                    label="Content",
                    placeholder="Enter the document content (larger content = longer processing)",
                    multiline=True
                ),
                Select(
                    id="category",
                    label="Category",
                    items={
                        "research": "Research",
                        "documentation": "Documentation",
                        "notes": "Notes"
                    }
                )
            ]
        ),
        KnowledgeType(
            type="web_url",
            label="Web URL",
            description="Add a web URL (slow processing - 8 seconds)",
            icon="🔗",
            inputs=[
                TextInput(
                    id="url",
                    label="URL",
                    placeholder="https://example.com"
                ),
                TextInput(
                    id="title",
                    label="Title",
                    placeholder="Descriptive title for this URL"
                ),
                TextInput(
                    id="description",
                    label="Description",
                    placeholder="Optional description of the content",
                    multiline=True
                )
            ]
        ),
        KnowledgeType(
            type="database",
            label="Database Connection",
            description="Connect to a database (slow processing - 8 seconds)",
            icon="🗄️",
            inputs=[
                TextInput(
                    id="connection_string",
                    label="Connection String",
                    placeholder="postgresql://user:pass@localhost:5432/db"
                ),
                TextInput(
                    id="title",
                    label="Connection Name",
                    placeholder="My Database"
                ),
                TextInput(
                    id="query",
                    label="Default Query",
                    placeholder="SELECT * FROM table_name LIMIT 100",
                    multiline=True
                )
            ]
        )
    ]

    # Send knowledge types using KnowledgeSettings
    knowledge_settings = KnowledgeSettings(types=knowledge_types)
    await knowledge_settings.send()

    # Add some sample knowledge items for testing updates and deletions
    sample_items = [
        {
            "id": "sample_1",
            "name": "Sample Document 1",
            "type": "text_document",
            "description": "A sample text document for testing updates and deletions"
        },
        {
            "id": "sample_2",
            "name": "Sample URL",
            "type": "web_url",
            "description": "A sample web URL for testing updates and deletions"
        }
    ]

    await context.emitter.set_knowledge_items(sample_items)

    # Welcome message with instructions
    welcome_msg = """# 🧪 Knowledge Cancellation Test

Welcome! This app demonstrates the knowledge operation cancellation functionality.

## 📋 How to Test:

1. **Click the knowledge button** (📚) in the chat input area
2. **Try creating knowledge items:**
   - Select a knowledge type (Text Document, Web URL, or Database)
   - Fill in the form and submit
   - **Operations take 4-8 seconds** - plenty of time to test cancellation!

3. **Test cancellation:**
   - Submit a form and watch for progress indicators
   - Look for cancel buttons in progress notifications
   - Try cancelling at different stages

4. **Test updates and deletions:**
   - Go to the "Manage" tab
   - Edit or delete existing items
   - These also have slow operations you can cancel

## 🔍 What to Look For:

- ✅ Immediate response when submitting forms
- 🔄 Progress indicators showing operations are running
- ❌ Cancel buttons during operations
- 📊 Console logs showing operation progress (check browser dev tools)
- 🎯 Proper cleanup when operations are cancelled

## 🐛 Backend Logs:

Check your terminal for operation progress logs:
- 🚀 Operation start messages
- 📊 Progress updates every second
- ❌ Cancellation messages
- ✅ Completion messages

Happy testing! 🎉"""

    await cl.Message(welcome_msg).send()


# Additional utility functions for demonstration

async def simulate_file_processing(filename: str, size_mb: float):
    """Simulate processing a file - can be cancelled"""
    chunks = int(size_mb * 10)  # 10 chunks per MB
    for i in range(chunks):
        await asyncio.sleep(0.1)  # 100ms per chunk
        yield f"Processing {filename}: {((i+1)/chunks)*100:.1f}% complete"


async def simulate_api_call(endpoint: str, retries: int = 3):
    """Simulate making API calls with retries - can be cancelled"""
    for attempt in range(retries):
        print(f"🌐 API call to {endpoint} - Attempt {attempt + 1}/{retries}")

        # Simulate network delay
        delay = random.uniform(1.0, 3.0)
        steps = int(delay * 10)

        for i in range(steps):
            await asyncio.sleep(0.1)

        # Simulate occasional failures
        if attempt < retries - 1 and random.random() < 0.3:
            print(f"❌ API call failed, retrying...")
            continue

        print(f"✅ API call to {endpoint} successful")
        return {"status": "success", "data": "Sample response"}

    raise Exception(f"API call to {endpoint} failed after {retries} attempts")


if __name__ == "__main__":
    print("🧪 Knowledge Cancellation Test Example")
    print("=" * 50)
    print("Run with: chainlit run example_cancel_test.py")
    print("Then open your browser and test the cancellation functionality!")
    print()
    print("💡 Tips:")
    print("- Operations are intentionally slow (4-8 seconds)")
    print("- Watch the terminal for operation progress logs")
    print("- Try cancelling operations at different stages")
    print("- Test all three operations: create, update, delete")