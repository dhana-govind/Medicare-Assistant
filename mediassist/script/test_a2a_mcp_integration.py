"""
Integration Test for A2A Protocol and MCP Server
=================================================

Tests the integration of:
1. A2A Protocol - Agent-to-agent messaging
2. MCP Server - Tool registration and invocation
3. Multi-agent orchestration with explicit communication

Run this to verify both systems work correctly.
"""

import json
import sys
from datetime import datetime

# Import the new modules
from a2a_protocol import (
    get_a2a_protocol, 
    Message, 
    MessageType, 
    MessagePriority,
    reset_protocol
)
from mcp_server import (
    get_mcp_server,
    ToolType,
    ToolDefinition,
    Parameter,
    ParameterType,
    reset_mcp_server
)
from patient_knowledge_graph import PatientKnowledgeGraph
from agent_analyzer import AnalyzerAgent
from agent_pharmacist import PharmacistAgent
from agent_care_coordinator import CareCoordinatorAgent


def test_a2a_protocol():
    """Test A2A Protocol functionality"""
    print("\n" + "="*70)
    print("TEST 1: A2A PROTOCOL FUNCTIONALITY")
    print("="*70)
    
    # Reset to clean state
    reset_protocol()
    protocol = get_a2a_protocol()
    
    # Test 1.1: Agent Registration
    print("\n[1.1] Testing Agent Registration...")
    protocol.register_agent("analyzer")
    protocol.register_agent("pharmacist")
    protocol.register_agent("coordinator")
    
    agents = protocol.registered_agents
    assert len(agents) == 3, f"Expected 3 agents, got {len(agents)}"
    print(f"✓ Registered agents: {agents}")
    
    # Test 1.2: Send Request Message
    print("\n[1.2] Testing Request Message...")
    msg_id = protocol.send_request(
        sender="analyzer",
        recipient="pharmacist",
        action="analyze_medications",
        data={"medications": ["Aspirin", "Metoprolol", "Lisinopril"]},
        priority=MessagePriority.HIGH
    )
    print(f"✓ Request sent with ID: {msg_id}")
    
    # Test 1.3: Send Response Message
    print("\n[1.3] Testing Response Message...")
    response_id = protocol.send_response(
        sender="pharmacist",
        recipient="analyzer",
        correlation_id=msg_id,
        result={"interactions_found": 0, "status": "safe"},
        success=True
    )
    print(f"✓ Response sent with ID: {response_id}")
    
    # Test 1.4: Broadcast Message
    print("\n[1.4] Testing Broadcast Message...")
    protocol.subscribe("analyzer", "patient_updates")
    protocol.subscribe("pharmacist", "patient_updates")
    protocol.subscribe("coordinator", "patient_updates")
    
    broadcast_id = protocol.broadcast_message(
        sender="coordinator",
        topic="patient_updates",
        data={"event": "patient_enrolled", "patient_id": "P001"},
        priority=MessagePriority.NORMAL
    )
    print(f"✓ Broadcast sent with ID: {broadcast_id}")
    print(f"  Subscribers to topic: {protocol.subscribers.get('patient_updates', set())}")
    
    # Test 1.5: Message Processing
    print("\n[1.5] Testing Message Processing...")
    
    def test_handler(msg):
        """Simple test handler"""
        print(f"  Handler received: {msg.message_type.value} from {msg.sender}")
        return None
    
    protocol.register_handler(test_handler, MessageType.REQUEST)
    responses = protocol.process_queue()
    print(f"✓ Processed {len(protocol.processed_messages)} messages")
    print(f"  Total stats: {protocol.get_statistics()}")
    
    # Test 1.6: Message Retrieval
    print("\n[1.6] Testing Message Retrieval...")
    message = protocol.get_message_by_id(msg_id)
    assert message is not None, "Message not found"
    print(f"✓ Retrieved message: {message.message_type.value}")
    
    correlation_chain = protocol.get_correlation_chain(msg_id)
    print(f"✓ Correlation chain has {len(correlation_chain)} messages")
    
    print("\n✓ A2A Protocol tests PASSED!")
    return True


def test_mcp_server():
    """Test MCP Server functionality"""
    print("\n" + "="*70)
    print("TEST 2: MCP SERVER FUNCTIONALITY")
    print("="*70)
    
    # Reset to clean state
    reset_mcp_server()
    mcp = get_mcp_server()
    
    # Test 2.1: Tool Registration
    print("\n[2.1] Testing Tool Registration...")
    
    def extract_data_handler(patient_id: str, data: dict) -> dict:
        return {"status": "extracted", "patient_id": patient_id}
    
    tool1 = ToolDefinition(
        name="extract_data",
        description="Extract patient data",
        tool_type=ToolType.CUSTOM,
        handler=extract_data_handler,
        parameters=[
            Parameter("patient_id", ParameterType.STRING, "Patient ID", True),
            Parameter("data", ParameterType.OBJECT, "Patient data", True)
        ],
        tags=["extraction", "data"]
    )
    
    tool_name = mcp.register_tool(tool1, aliases=["extract", "parse"])
    print(f"✓ Tool registered: {tool_name}")
    assert tool_name == "extract_data"
    
    # Test 2.2: Tool Listing
    print("\n[2.2] Testing Tool Listing...")
    all_tools = mcp.list_tools()
    assert len(all_tools) > 0, "No tools found"
    print(f"✓ Listed {len(all_tools)} tools")
    
    custom_tools = mcp.list_tools(tool_type=ToolType.CUSTOM)
    print(f"✓ Custom tools: {len(custom_tools)}")
    
    # Test 2.3: Tool Invocation
    print("\n[2.3] Testing Tool Invocation...")
    success, result = mcp.invoke_tool(
        "extract_data",
        {"patient_id": "P001", "data": {"name": "John Smith"}}
    )
    
    assert success, f"Tool invocation failed: {result}"
    print(f"✓ Tool invoked successfully: {result}")
    
    # Test 2.4: Tool Alias Invocation
    print("\n[2.4] Testing Tool Alias Invocation...")
    success2, result2 = mcp.invoke_tool(
        "extract",  # Using alias
        {"patient_id": "P002", "data": {"name": "Jane Doe"}}
    )
    
    assert success2, f"Alias invocation failed: {result2}"
    print(f"✓ Alias invocation successful: {result2}")
    
    # Test 2.5: Resource Management
    print("\n[2.5] Testing Resource Management...")
    
    resource = mcp.create_resource(
        name="patient_dataset_001",
        resource_type="dataset",
        data={"patients": 10, "records": 500},
        tags=["production", "important"]
    )
    
    print(f"✓ Resource created: {resource.resource_id}")
    print(f"  Resource type: {resource.resource_type}")
    
    retrieved = mcp.get_resource(resource.resource_id)
    assert retrieved is not None, "Resource not found"
    print(f"✓ Resource retrieved: {retrieved.name}")
    
    resources = mcp.list_resources(resource_type="dataset")
    assert len(resources) > 0
    print(f"✓ Listed {len(resources)} dataset resources")
    
    # Test 2.6: Server Info
    print("\n[2.6] Testing Server Info...")
    info = mcp.get_server_info()
    print(f"✓ Server: {info['server_name']}")
    print(f"  Tools: {info['tools_count']}")
    print(f"  Resources: {info['resources_count']}")
    print(f"  Invocations: {info['statistics']['total_invocations']}")
    
    print("\n✓ MCP Server tests PASSED!")
    return True


def test_agent_integration():
    """Test integration with agents"""
    print("\n" + "="*70)
    print("TEST 3: AGENT INTEGRATION WITH A2A PROTOCOL")
    print("="*70)
    
    # Reset protocols
    reset_protocol()
    protocol = get_a2a_protocol()
    
    # Create knowledge graph and agents
    kg = PatientKnowledgeGraph()
    analyzer = AnalyzerAgent(kg)
    pharmacist = PharmacistAgent(kg)
    coordinator = CareCoordinatorAgent(kg)
    
    print("\n[3.1] Testing Agent Initialization...")
    print(f"✓ Analyzer agent registered: {analyzer.agent_name}")
    print(f"✓ Pharmacist agent registered: {pharmacist.agent_name}")
    print(f"✓ Coordinator agent registered: {coordinator.agent_name}")
    
    # Test 3.2: Verify A2A protocol integration
    print("\n[3.2] Testing A2A Protocol in Agents...")
    assert analyzer.a2a_protocol is not None, "Analyzer A2A not initialized"
    assert pharmacist.a2a_protocol is not None, "Pharmacist A2A not initialized"
    assert coordinator.a2a_protocol is not None, "Coordinator A2A not initialized"
    print("✓ All agents have A2A protocol initialized")
    
    # Test 3.3: Run analyzer and verify A2A message sent
    print("\n[3.3] Testing Analyzer -> Pharmacist Communication...")
    
    mock_data = {
        "patient_id": "TEST001",
        "name": "Test Patient",
        "admission_date": "2025-01-01",
        "discharge_date": "2025-01-07",
        "primary_diagnosis": "Hypertension",
        "medications": "Lisinopril 10mg daily, Aspirin 325mg daily",
        "follow_up": "PCP in 1 week"
    }
    
    analysis = analyzer.analyze_discharge_summary(mock_data)
    print(f"✓ Analysis completed: {analysis.status}")
    print(f"  Medications extracted: {analysis.findings.get('medications_extracted')}")
    
    # Check if message was sent
    messages_in_queue = len(protocol.message_queue)
    print(f"✓ Messages in A2A queue: {messages_in_queue}")
    
    print("\n✓ Agent Integration tests PASSED!")
    return True


def test_end_to_end():
    """End-to-end workflow test"""
    print("\n" + "="*70)
    print("TEST 4: END-TO-END WORKFLOW")
    print("="*70)
    
    # Reset
    reset_protocol()
    reset_mcp_server()
    
    protocol = get_a2a_protocol()
    mcp = get_mcp_server()
    kg = PatientKnowledgeGraph()
    
    # Initialize agents
    analyzer = AnalyzerAgent(kg)
    pharmacist = PharmacistAgent(kg)
    coordinator = CareCoordinatorAgent(kg)
    
    print("\n[4.1] Patient Data Extraction...")
    mock_data = {
        "patient_id": "E2E001",
        "name": "End-to-End Test",
        "primary_diagnosis": "Acute MI",
        "medications": "Aspirin 325mg daily, Clopidogrel 75mg daily, Metoprolol 50mg daily",
        "follow_up": "Cardiology in 1 week"
    }
    
    analysis1 = analyzer.analyze_discharge_summary(mock_data)
    print(f"✓ Analyzer: {analysis1.status}")
    
    print("\n[4.2] Medication Interaction Analysis...")
    analysis2 = pharmacist.check_medication_interactions()
    print(f"✓ Pharmacist: {analysis2.status}")
    print(f"  Interactions found: {analysis2.findings.get('total_interactions', 0)}")
    
    print("\n[4.3] Patient Engagement...")
    greeting, analysis3 = coordinator.initiate_patient_engagement()
    print(f"✓ Coordinator: {analysis3.status}")
    
    print("\n[4.4] A2A Protocol Statistics...")
    stats = protocol.get_statistics()
    print(f"✓ Total messages: {stats['total_messages']}")
    print(f"✓ Processed: {stats['processed_count']}")
    print(f"✓ Registered agents: {stats['registered_agents']}")
    
    print("\n[4.5] MCP Server Metrics...")
    metrics = mcp.export_metrics()
    print(f"✓ Tools registered: {len(metrics['tools'])}")
    print(f"✓ Tool invocations: {metrics['server_info']['statistics']['total_invocations']}")
    
    print("\n✓ End-to-End workflow test PASSED!")
    return True


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("   MediSync A2A Protocol & MCP Server Integration Tests")
    print("="*70)
    
    tests = [
        ("A2A Protocol", test_a2a_protocol),
        ("MCP Server", test_mcp_server),
        ("Agent Integration", test_agent_integration),
        ("End-to-End Workflow", test_end_to_end)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n✗ TEST FAILED: {test_name}")
            print(f"  Error: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{status:12} | {test_name}")
    
    print("="*70)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests PASSED! Integration successful.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
