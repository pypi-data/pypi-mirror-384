"""
Complete Test Suite for USF P1 Chatbot SDK
Tests all 33 endpoints across 8 categories

Run with: python test_all_33_endpoints.py
"""

import sys
import os
import time
import json
from datetime import datetime

# Add parent directory to path to import the SDK
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from usf_p1_chatbot_sdk import CivieClient, CivieAPIError

# Configuration
API_KEY = "ultrasafe-civie-asd#$%&q#w!kT&ert$"
BASE_URL = "https://api-civie.us.inc"
TIMEOUT = 180  # 3 minutes for deletion operations

# Test results tracker
test_results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "total": 33
}

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_endpoint(endpoint_name, test_func):
    """Wrapper to test an endpoint and track results"""
    try:
        print(f"\n🧪 Testing: {endpoint_name}")
        result = test_func()
        if result is False:
            print(f"⚠️  SKIPPED: {endpoint_name}")
            test_results["skipped"] += 1
            return None
        print(f"✅ PASSED: {endpoint_name}")
        test_results["passed"] += 1
        return result
    except Exception as e:
        print(f"❌ FAILED: {endpoint_name}")
        print(f"   Error: {str(e)}")
        test_results["failed"] += 1
        return None

def main():
    """Main test execution"""
    print("=" * 70)
    print("USF P1 Chatbot SDK - Complete Endpoint Test Suite")
    print("Testing all 33 endpoints across 8 categories")
    print("=" * 70)
    
    # Initialize client with increased timeout for deletion operations
    try:
        client = CivieClient(api_key=API_KEY, base_url=BASE_URL, timeout=TIMEOUT)
        print(f"\n✅ Client initialized")
        print(f"   Base URL: {BASE_URL}")
        print(f"   Timeout: {TIMEOUT} seconds")
    except Exception as e:
        print(f"\n❌ Failed to initialize client: {e}")
        return
    
    # Store test data
    test_data = {}
    
    # =================================================================
    # CATEGORY 1: Health Check (1 endpoint)
    # =================================================================
    print_section("CATEGORY 1: Health Check (1 endpoint)")
    
    def test_health():
        health = client.health()
        print(f"   Status: {health}")
        return health
    
    test_endpoint("1. GET /health", test_health)
    
    # =================================================================
    # CATEGORY 2: Collection Management (3 endpoints)
    # =================================================================
    print_section("CATEGORY 2: Collection Management (3 endpoints)")
    
    # 2.1 Create Collection
    def test_create_collection():
        collection_name = f"test_sdk_{int(time.time())}"
        response = client.collections.create(
            collection_name=collection_name,
            description="SDK test collection"
        )
        collection_id = response["collection_info"]["collection_id"]
        test_data["collection_id"] = collection_id
        test_data["collection_name"] = collection_name
        print(f"   Collection ID: {collection_id}")
        print(f"   Collection Name: {collection_name}")
        return response
    
    test_endpoint("2. POST /api/collections (Create)", test_create_collection)
    
    # 2.2 List All Collections
    def test_list_collections():
        response = client.collections.list()
        print(f"   Total Collections: {response['total_count']}")
        return response
    
    test_endpoint("3. GET /api/collections (List)", test_list_collections)
    
    # =================================================================
    # CATEGORY 3: Patient Management (7 endpoints)
    # =================================================================
    print_section("CATEGORY 3: Patient Management (7 endpoints)")
    
    if "collection_id" not in test_data:
        print("\n⚠️  Skipping patient tests - no collection_id available")
        test_results["skipped"] += 7
    else:
        collection_id = test_data["collection_id"]
        
        # 3.1 Register Patient
        def test_register_patient():
            patient_username = f"test_patient_{int(time.time())}"
            response = client.patients.register(
                patient_user_name=patient_username,
                collection_id=collection_id,
                full_name="Test Patient SDK",
                email="test@example.com",
                metadata={"test": True}
            )
            test_data["patient_username"] = patient_username
            test_data["patient_id"] = response["patient_id"]
            print(f"   Patient Username: {patient_username}")
            print(f"   Patient ID: {response['patient_id']}")
            return response
        
        test_endpoint("4. POST /api/patient/register", test_register_patient)
        
        # 3.2 Validate Patient
        def test_validate_patient():
            if "patient_username" not in test_data:
                return False
            response = client.patients.validate(
                patient_user_name=test_data["patient_username"],
                collection_id=collection_id
            )
            print(f"   Exists: {response['exists']}")
            return response
        
        test_endpoint("5. POST /api/patient/validate", test_validate_patient)
        
        # 3.3 Get Patient Info
        def test_get_patient():
            if "patient_username" not in test_data:
                return False
            response = client.patients.get(
                patient_user_name=test_data["patient_username"],
                collection_id=collection_id
            )
            print(f"   Name: {response.get('full_name')}")
            print(f"   Data Count: {response.get('data_count')}")
            return response
        
        test_endpoint("6. GET /api/patient/{patient_user_name}", test_get_patient)
        
        # 3.4 List All Patients
        def test_list_all_patients():
            response = client.patients.list(limit=10)
            print(f"   Total Retrieved: {len(response)}")
            return response
        
        test_endpoint("7. GET /api/patients", test_list_all_patients)
        
        # 3.5 List Patients by Collection
        def test_list_patients_by_collection():
            response = client.patients.list_by_collection(
                collection_id=collection_id,
                limit=10
            )
            print(f"   Patients in Collection: {len(response)}")
            return response
        
        test_endpoint("8. GET /api/patients/collection/{collection_id}", test_list_patients_by_collection)
        
        # 3.6 Get Patient Data Summary
        def test_get_patient_data():
            if "patient_username" not in test_data:
                return False
            response = client.patients.get_data_summary(
                patient_user_name=test_data["patient_username"],
                collection_id=collection_id
            )
            print(f"   Data Summary Retrieved")
            return response
        
        test_endpoint("9. GET /api/patient/{patient_user_name}/data", test_get_patient_data)
    
    # =================================================================
    # CATEGORY 4: Async Data Ingestion (3 endpoints)
    # =================================================================
    print_section("CATEGORY 4: Async Data Ingestion (3 endpoints)")
    
    if "collection_id" not in test_data or "patient_username" not in test_data:
        print("\n⚠️  Skipping ingestion tests - missing collection_id or patient_username")
        test_results["skipped"] += 3
    else:
        collection_id = test_data["collection_id"]
        patient_username = test_data["patient_username"]
        
        # 4.1 Ingest PDFs (using actual test files)
        def test_ingest_pdfs():
            pdf_files = [
                "CBC_Report_Ravi_A_Menon.pdf",
                "Kidney_Function_Ravi_A_Menon.pdf",
                "Lipid_Profile_Ravi_A_Menon.pdf",
                "Liver_Function_Ravi_A_Menon.pdf",
                "Thyroid_Function_Ravi_A_Menon.pdf"
            ]
            response = client.ingestion.ingest_pdfs(
                pdf_files=pdf_files,
                collection_id=collection_id,
                patient_user_name=patient_username
            )
            test_data["pdf_request_id"] = response["request_id"]
            print(f"   Request ID: {response['request_id']}")
            print(f"   Total Files: {response['total_files']}")
            print(f"   Estimated Time: {response.get('estimated_time_minutes', 'N/A')} minutes")
            return response
        
        test_endpoint("10. POST /api/data/async/pdfs", test_ingest_pdfs)
        
        # 4.2 Ingest URLs
        def test_ingest_urls():
            response = client.ingestion.ingest_urls(
                urls=["https://pypi.org/project/usf-p1-chatbot-sdk/"],
                collection_id=collection_id,
                patient_user_name=patient_username
            )
            test_data["url_request_id"] = response["request_id"]
            print(f"   Request ID: {response['request_id']}")
            print(f"   Total Files: {response['total_files']}")
            return response
        
        test_endpoint("11. POST /api/data/async/urls", test_ingest_urls)
        
        # 4.3 Ingest Mixed (PDFs + URLs)
        def test_ingest_mixed():
            response = client.ingestion.ingest_mixed(
                collection_id=collection_id,
                patient_user_name=patient_username,
                pdf_files=["CBC_Report_Ravi_A_Menon.pdf"],
                urls=["https://pypi.org/project/usf-p1-chatbot-sdk/"]
            )
            test_data["mixed_request_id"] = response["request_id"]
            print(f"   Request ID: {response['request_id']}")
            print(f"   Total Files: {response['total_files']}")
            return response
        
        test_endpoint("12. POST /api/data/async (Mixed)", test_ingest_mixed)
    
    # =================================================================
    # CATEGORY 5: Ingestion Status (4 endpoints)
    # =================================================================
    print_section("CATEGORY 5: Ingestion Status (4 endpoints)")
    
    # 5.1 Get Progress
    def test_get_progress():
        if "url_request_id" not in test_data:
            return False
        response = client.ingestion.get_progress(test_data["url_request_id"])
        print(f"   Status: {response['status']}")
        print(f"   Progress: {response['progress_percentage']}%")
        return response
    
    test_endpoint("13. GET /api/data/progress/{request_id}", test_get_progress)
    
    # 5.2 List Recent Requests
    def test_list_requests():
        response = client.ingestion.list_recent_requests(limit=5)
        print(f"   Recent Requests: {len(response)}")
        return response
    
    test_endpoint("14. GET /api/data/requests", test_list_requests)
    
    # 5.3 Get Service Status
    def test_service_status():
        response = client.ingestion.get_service_status()
        print(f"   Service Status Retrieved")
        return response
    
    test_endpoint("15. GET /api/data/status", test_service_status)
    
    # 5.4 Cancel Request (skip to avoid disrupting ingestion)
    print(f"\n🧪 Testing: 16. DELETE /api/data/request/{'{request_id}'}")
    print(f"⚠️  SKIPPED: Would interrupt ongoing ingestion")
    test_results["skipped"] += 1
    
    # =================================================================
    # CATEGORY 6: Chat Operations (2 endpoints)
    # =================================================================
    print_section("CATEGORY 6: Chat Operations (2 endpoints)")
    
    if "collection_id" not in test_data or "patient_username" not in test_data:
        print("\n⚠️  Skipping chat tests - missing collection_id or patient_username")
        test_results["skipped"] += 2
    else:
        collection_id = test_data["collection_id"]
        patient_username = test_data["patient_username"]
        
        # 6.1 Standard Chat
        def test_chat():
            response = client.chat.send_message(
                messages=[
                    {"user": "Give me analysis of my report?"}
                ],
                collection_id=collection_id,
                patient_user_name=patient_username
            )
            print(f"   Response: {response['response'][:100]}...")
            print(f"   Response Time: {response['total_response_time_ms']}ms")
            return response
        
        test_endpoint("17. POST /api/chat", test_chat)
        
        # 6.2 Streaming Chat
        def test_chat_stream():
            print(f"   Streaming: ", end="", flush=True)
            chunks = []
            for chunk in client.chat.send_message_stream(
                messages=[{"user": "Give me analysis of my report?"}],
                collection_id=collection_id,
                patient_user_name=patient_username
            ):
                chunks.append(chunk)
                if len(chunks) <= 10:
                    print(".", end="", flush=True)
            print(f" Done ({len(chunks)} chunks)")
            return True
        
        test_endpoint("18. POST /api/chat/stream", test_chat_stream)
    
    # =================================================================
    # CATEGORY 7: Log Management (8 endpoints)
    # =================================================================
    print_section("CATEGORY 7: Log Management (8 endpoints)")
    
    # 7.1 Get Log Collections
    def test_log_collections():
        response = client.logs.get_collections()
        print(f"   Log Collections Retrieved")
        return response
    
    test_endpoint("19. GET /api/logs/collections", test_log_collections)
    
    # 7.2 Get Log Stats
    def test_log_stats():
        response = client.logs.get_stats()
        print(f"   Log Statistics Retrieved")
        return response
    
    test_endpoint("20. GET /api/logs/stats", test_log_stats)
    
    # 7.3 Get Recent Logs
    def test_recent_logs():
        response = client.logs.get_recent(minutes=60, limit=5)
        print(f"   Recent Logs Retrieved")
        return response
    
    test_endpoint("21. GET /api/logs/recent", test_recent_logs)
    
    # 7.4 Get Logs from Collection
    def test_logs_from_collection():
        response = client.logs.get_from_collection(
            collection_name="logs_chat_interactions",
            limit=5
        )
        print(f"   Logs from Collection Retrieved")
        return response
    
    test_endpoint("22. GET /api/logs/{collection_name}", test_logs_from_collection)
    
    # 7.5 Clear Log Collection (skip to avoid data loss)
    print(f"\n🧪 Testing: 23. DELETE /api/logs/{'{collection_name}'}")
    print(f"⚠️  SKIPPED: Would delete logs")
    test_results["skipped"] += 1
    
    # 7.6 Get Patient Recent Logs
    def test_patient_recent_logs():
        if "collection_id" not in test_data or "patient_username" not in test_data:
            return False
        response = client.logs.get_patient_recent(
            collection_id=test_data["collection_id"],
            patient_user_name=test_data["patient_username"],
            minutes=120
        )
        print(f"   Patient Recent Logs Retrieved")
        return response
    
    test_endpoint("24. GET /api/logs/patient-recent/{collection_id}/{patient_user_name}", test_patient_recent_logs)
    
    # 7.7 Get Patient Logs from Log Collection
    def test_patient_logs_from_collection():
        if "collection_id" not in test_data or "patient_username" not in test_data:
            return False
        response = client.logs.get_patient_from_collection(
            collection_id=test_data["collection_id"],
            patient_user_name=test_data["patient_username"],
            log_collection_name="logs_chat_interactions"
        )
        print(f"   Patient Logs from Collection Retrieved")
        return response
    
    test_endpoint("25. GET /api/logs/patient-from-collection/{collection_id}/{patient_user_name}/{log_collection_name}", test_patient_logs_from_collection)
    
    # 7.8 Get Logs by Collection and Log Collection
    def test_logs_by_collection_and_log():
        if "collection_id" not in test_data:
            return False
        response = client.logs.get_by_collection_and_log_collection(
            collection_id=test_data["collection_id"],
            log_collection_name="logs_data_ingestion"
        )
        print(f"   Logs by Collection and Log Collection Retrieved")
        return response
    
    test_endpoint("26. GET /api/logs/collection-specific/{collection_id}/{log_collection_name}", test_logs_by_collection_and_log)
    
    # =================================================================
    # CATEGORY 8: File Operations (5 endpoints)
    # =================================================================
    print_section("CATEGORY 8: File Operations (5 endpoints)")
    
    # 8.1 List DB Files
    def test_list_db_files():
        response = client.files.list_db_files()
        print(f"   DB Files Retrieved: {len(response)}")
        return response
    
    test_endpoint("27. GET /api/db/files", test_list_db_files)
    
    # 8.2 List DB Files by Collection
    def test_list_db_files_by_collection():
        if "collection_id" not in test_data:
            return False
        response = client.files.list_db_files_by_collection(test_data["collection_id"])
        print(f"   DB Files by Collection: {len(response)}")
        return response
    
    test_endpoint("28. GET /api/db/files/{collection_id}", test_list_db_files_by_collection)
    
    # 8.3 List S3 Files
    def test_list_s3_files():
        response = client.files.list_s3_files()
        print(f"   S3 Files Retrieved")
        return response
    
    test_endpoint("29. GET /api/s3/files", test_list_s3_files)
    
    # 8.4 List S3 Files by Collection
    def test_list_s3_files_by_collection():
        if "collection_id" not in test_data:
            return False
        response = client.files.list_s3_files_by_collection(test_data["collection_id"])
        print(f"   S3 Files by Collection Retrieved")
        return response
    
    test_endpoint("30. GET /api/s3/files/{collection_id}", test_list_s3_files_by_collection)
    
    # 8.5 Delete Document (skip to avoid data loss)
    print(f"\n🧪 Testing: 31. DELETE /api/document/{'{document_uuid}'}")
    print(f"⚠️  SKIPPED: Would delete document")
    test_results["skipped"] += 1
    
    # =================================================================
    # CLEANUP: Delete Patient and Collection (2 more endpoints)
    # =================================================================
    print_section("CLEANUP: Testing Deletion Endpoints")
    
    # Delete Patient
    def test_delete_patient():
        if "collection_id" not in test_data or "patient_username" not in test_data:
            return False
        response = client.patients.delete(
            patient_user_name=test_data["patient_username"],
            collection_id=test_data["collection_id"],
            delete_patient_record=True
        )
        print(f"   Patient Deleted Successfully")
        return response
    
    test_endpoint("32. DELETE /api/patient/{patient_user_name}", test_delete_patient)
    
    # Delete Collection
    def test_delete_collection():
        if "collection_id" not in test_data:
            return False
        response = client.collections.delete(test_data["collection_id"])
        print(f"   Collection Deleted Successfully")
        return response
    
    test_endpoint("33. DELETE /api/collections/{collection_id}", test_delete_collection)
    
    # =================================================================
    # FINAL SUMMARY
    # =================================================================
    print_section("TEST SUMMARY")
    
    print(f"\n📊 Test Results:")
    print(f"   Total Endpoints: {test_results['total']}")
    print(f"   ✅ Passed: {test_results['passed']}")
    print(f"   ❌ Failed: {test_results['failed']}")
    print(f"   ⚠️  Skipped: {test_results['skipped']}")
    print(f"   Success Rate: {(test_results['passed']/(test_results['total']-test_results['skipped'])*100):.1f}%")
    
    # Close client
    client.close()
    print(f"\n✅ Client closed")
    print("\n" + "=" * 70)
    print("Test Suite Complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
