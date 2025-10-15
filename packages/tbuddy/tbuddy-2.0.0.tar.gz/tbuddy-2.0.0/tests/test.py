# tests/test_complete.py
import sys
import os
import secrets
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from TBuddy_SDK import TBuddyClient, TBuddyConfig
from TBuddy_SDK.models import StreamUpdate


class TestSuite:
    """Complete test suite for SDK"""

    def __init__(self):
        # Generate a valid dummy API key (>= 10 characters)
        dummy_api_key = secrets.token_hex(8)  # 16-character hex string
        
        self.config = TBuddyConfig(
            api_key=dummy_api_key,
            base_url="http://localhost:8000",
            log_level="INFO"
        )
        self.session_id = None

    async def test_1_new_query(self):
        """Test 1: Submit new query"""
        print("\n🧪 Test 1: New Query")
        print("-" * 50)

        async with TBuddyClient(self.config) as client:
            result = await client.submit_query(
                "Plan a 3-day trip to Paris from London on dates 11th, 12th, 13th October with budget under 30000k",
                wait_for_completion=True
            )

            assert result.session_id is not None
            assert result.status == "completed"
            assert result.destination is not None

            self.session_id = result.session_id

            print(f"✅ Session ID: {result.session_id}")
            print(f"✅ Destination: {result.destination}")
            print(f"✅ Status: {result.status}")

    async def test_2_follow_up(self):
        """Test 2: Follow-up query"""
        print("\n🧪 Test 2: Follow-up Query")
        print("-" * 50)

        async with TBuddyClient(self.config) as client:
            result = await client.submit_query(
                "Change budget to $2000",
                session_id=self.session_id,
                wait_for_completion=True
            )

            assert result.is_follow_up is True
            assert result.session_id == self.session_id

            print(f"✅ Is Follow-up: {result.is_follow_up}")
            print(f"✅ Update Type: {result.update_type}")

    async def test_3_session_memory(self):
        """Test 3: Get session memory"""
        print("\n🧪 Test 3: Session Memory")
        print("-" * 50)

        async with TBuddyClient(self.config) as client:
            memory = None
            for i in range(20):  # poll for up to ~4 seconds
                memory = await client.get_session_memory(self.session_id)
                print(f"🔍 Poll {i+1}: memory.exists={memory.exists}, destination={memory.destination}, conversation_turns={memory.conversation_turns}")
                
                if memory.exists:
                    break
                await asyncio.sleep(0.2)

            if not memory.exists:
                # Final log before failing
                print(f"❌ Session memory not initialized: {vars(memory)}")
            
            assert memory.exists is True

            print(f"✅ Memory exists: {memory.exists}")
            print(f"✅ Destination: {memory.destination}")
            print(f"✅ Conversation turns: {memory.conversation_turns}")

    async def test_4_websocket(self):
        """Test 4: WebSocket streaming"""
        print("\n🧪 Test 4: WebSocket Streaming")
        print("-" * 50)

        updates_received = []
        agent_updates = {}  # Track which agents completed
        workflow_complete = asyncio.Event()

        async def on_update(update: StreamUpdate):
            updates_received.append(update)
            
            # Track update type
            if update.type == "agent_start":
                print(f"🚀 {update.agent}: Started")
            elif update.type == "agent_update":
                print(f"✅ {update.agent}: Completed")
                agent_updates[update.agent] = "completed"
            elif update.type == "progress":
                print(f"📊 Progress: {update.message} ({update.progress_percent}%)")
            elif update.type == "completed":
                print(f"🎉 Workflow completed!")
                workflow_complete.set()
            elif update.type == "error":
                print(f"❌ Error: {update.message}")

        async with TBuddyClient(self.config) as client:
            # FIXED: Don't wait for completion in submit_query
            # Let the WebSocket callback handle everything
            result = await client.submit_query(
                "Plan a 3-day trip to Paris from London on dates 11th, 12th, 13th October with budget under 30000k",
                stream_callback=on_update,
                wait_for_completion=False  # ✅ CHANGED: Don't block
            )

            print(f"📝 Session started: {result.session_id}")
            print(f"🎧 Listening for WebSocket updates...")

            # Wait for workflow to complete via WebSocket
            try:
                await asyncio.wait_for(workflow_complete.wait(), timeout=60.0)
            except asyncio.TimeoutError:
                print("⏱️ Timeout waiting for workflow completion")
                raise

            # Verify we received updates
            assert len(updates_received) > 0, "No updates received"
            
            # Check we received different update types
            update_types = set(u.type for u in updates_received)
            print(f"\n📊 Update types received: {update_types}")
            
            # Should have at least: connected, progress, agent_update, completed
            assert "connected" in update_types or "progress" in update_types, \
                "Should receive connection/progress updates"
            
            # Should have agent completions
            assert len(agent_updates) > 0, "No agent completion updates received"
            
            print(f"✅ Received {len(updates_received)} total updates")
            print(f"✅ Agents completed: {list(agent_updates.keys())}")
            
            # Verify final result
            final_result = await client.get_result(result.session_id)
            assert final_result.status == "completed"
            print(f"✅ Final status: {final_result.status}")

    async def test_4_websocket_alternative(self):
        """Test 4 Alternative: WebSocket with wait_for_completion"""
        print("\n🧪 Test 4 (Alternative): WebSocket with Completion Wait")
        print("-" * 50)

        updates_received = []
        update_lock = asyncio.Lock()

        async def on_update(update: StreamUpdate):
            async with update_lock:
                updates_received.append(update)
                print(f"📡 [{update.type}] {update.agent}: {update.message}")

        async with TBuddyClient(self.config) as client:
            # Start streaming in background
            result = await client.submit_query(
                "Plan a 3-day trip to Paris from London on dates 11th, 12th, 13th October with budget under 30000k",
                stream_callback=on_update,
                wait_for_completion=True  # Will wait for completion
            )

            # Give WebSocket a moment to receive final updates
            await asyncio.sleep(1.0)

            assert len(updates_received) > 0, "No updates received"
            print(f"✅ Received {len(updates_received)} updates")
            print(f"✅ Final status: {result.status}")

    async def test_5_health_check(self):
        """Test 5: Health check"""
        print("\n🧪 Test 5: Health Check")
        print("-" * 50)

        async with TBuddyClient(self.config) as client:
            health = await client.health_check()

            print(f"✅ Status: {health.status}")
            print(f"✅ Orchestrator: {health.orchestrator}")

    async def test_6_websocket_existing_session(self):
        """Test 6: WebSocket on existing session (follow-up)"""
        print("\n🧪 Test 6: WebSocket on Existing Session")
        print("-" * 50)

        if not self.session_id:
            print("⚠️ Skipping - no existing session")
            return

        updates_received = []
        workflow_complete = asyncio.Event()

        async def on_update(update: StreamUpdate):
            updates_received.append(update)
            print(f"📡 {update.type}: {update.message}")
            if update.type == "completed":
                workflow_complete.set()

        async with TBuddyClient(self.config) as client:
            # Follow-up query with streaming
            result = await client.submit_query(
                "Add Eiffel Tower to my itinerary",
                session_id=self.session_id,
                stream_callback=on_update,
                wait_for_completion=False
            )

            print(f"📝 Follow-up session: {result.session_id}")
            print(f"🎧 Listening for updates...")

            try:
                await asyncio.wait_for(workflow_complete.wait(), timeout=30.0)
            except asyncio.TimeoutError:
                print("⏱️ Timeout")
                raise

            assert len(updates_received) > 0
            print(f"✅ Received {len(updates_received)} updates")

    async def run_all(self):
        """Run all tests"""
        print("=" * 50)
        print("🚀 TBuddy SDK Test Suite")
        print("=" * 50)

        try:
            await self.test_1_new_query()
            await self.test_2_follow_up()
            await self.test_3_session_memory()
            
            # Choose one WebSocket test method
            await self.test_4_websocket()  # Recommended
            # OR
            # await self.test_4_websocket_alternative()
            
            await self.test_5_health_check()
            
            # Optional: Test WebSocket on existing session
            # await self.test_6_websocket_existing_session()

            print("\n" + "=" * 50)
            print("✅ All tests passed!")
            print("=" * 50)

        except AssertionError as e:
            print(f"\n❌ Assertion failed: {e}")
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()


async def main():
    suite = TestSuite()
    await suite.run_all()


if __name__ == "__main__":
    asyncio.run(main())
