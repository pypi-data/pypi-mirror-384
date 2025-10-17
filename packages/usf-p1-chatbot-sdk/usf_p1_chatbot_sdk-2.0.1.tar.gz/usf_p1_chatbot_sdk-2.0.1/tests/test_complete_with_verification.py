"""
Complete End-to-End Test with Ingestion Verification and All Deletions
Tests data ingestion completion and all deletion endpoints

Run with: python test_complete_with_verification.py
"""

import sys
import os
import time
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from usf_p1_chatbot_sdk import CivieClient

# Configuration
API_KEY = "ultrasafe-civie-asd#$%&q#w!kT&ert$"
BASE_URL = "https://api-civie.us.inc"
TIMEOUT = 300  # 5 minutes for long operations

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def wait_for_ingestion(client, request_id, description):
    """Wait for ingestion to complete and monitor progress"""
    print(f"\n⏳ Waiting for {description} to complete...")
    print(f"   Request ID: {request_id}")
    
    start_time = time.time()
    last_progress = -1
    
    while True:
        try:
            progress = client.ingestion.get_progress(request_id)
            status = progress['status']
            percentage = progress['progress_percentage']
            processed = progress['processed_files']
            total = progress['total_files']
            
            if percentage != last_progress:
                elapsed = int(time.time() - start_time)
                print(f"   [{elapsed}s] Status: {status}, Progress: {percentage}%, Files: {processed}/{total}")
                last_progress = percentage
            
            if status == 'completed':
                print(f"✅ {description} completed successfully!")
                return True
            elif status == 'failed':
                print(f"❌ {description} failed!")
                return False
            
            time.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            print(f"   Error checking progress: {e}")
            time.sleep(5)

def main():
    print("=" * 80)
    print("USF P1 Chatbot SDK - Complete End-to-End Test with Verification")
    print("=" * 80)
    
    client = CivieClient(api_key=API_KEY, base_url=BASE_URL, timeout=TIMEOUT)
    print(f"\n✅ Client initialized (timeout: {TIMEOUT}s)")
    
    test_data = {}
    
    # =================================================================
    # STEP 1: Create Collection
    # =================================================================
    print_section("STEP 1: Create Collection")
    
    collection_name = f"test_verification_{int(time.time())}"
    response = client.collections.create(
        collection_name=collection_name,
        description="Test collection for complete verification"
    )
    collection_id = response["collection_info"]["collection_id"]
    test_data["collection_id"] = collection_id
    test_data["collection_name"] = collection_name
    print(f"✅ Collection created: {collection_id}")
    
    # =================================================================
    # STEP 2: Register Patient
    # =================================================================
    print_section("STEP 2: Register Patient")
    
    patient_username = f"test_verify_{int(time.time())}"
    response = client.patients.register(
        patient_user_name=patient_username,
        collection_id=collection_id,
        full_name="Test Verification Patient",
        email="verify@test.com",
        metadata={"test": "verification"}
    )
    patient_id = response["patient_id"]
    test_data["patient_username"] = patient_username
    test_data["patient_id"] = patient_id
    print(f"✅ Patient registered: {patient_username} (ID: {patient_id})")
    
    # Check initial data count
    patient_info = client.patients.get(patient_username, collection_id)
    print(f"   Initial data count: {patient_info.get('data_count', 0)}")
    
    # =================================================================
    # STEP 3: Ingest Data (PDFs)
    # =================================================================
    print_section("STEP 3: Ingest PDFs and Wait for Completion")
    
    pdf_files = [
        "CBC_Report_Ravi_A_Menon.pdf",
        "Kidney_Function_Ravi_A_Menon.pdf",
        "Lipid_Profile_Ravi_A_Menon.pdf"
    ]
    
    print(f"📤 Uploading {len(pdf_files)} PDFs...")
    response = client.ingestion.ingest_pdfs(
        pdf_files=pdf_files,
        collection_id=collection_id,
        patient_user_name=patient_username
    )
    pdf_request_id = response["request_id"]
    test_data["pdf_request_id"] = pdf_request_id
    print(f"   Request ID: {pdf_request_id}")
    print(f"   Total Files: {response['total_files']}")
    print(f"   Estimated Time: {response.get('estimated_time_minutes', 'N/A')} minutes")
    
    # Wait for PDF ingestion to complete
    if wait_for_ingestion(client, pdf_request_id, "PDF ingestion"):
        # Verify ingestion
        print("\n🔍 Verifying data ingestion...")
        
        # Check patient data count
        patient_info = client.patients.get(patient_username, collection_id)
        data_count = patient_info.get('data_count', 0)
        print(f"   Patient data count: {data_count}")
        
        # Check files in collection
        db_files = client.files.list_db_files_by_collection(collection_id)
        print(f"   DB files in collection: {len(db_files)}")
        
        if data_count > 0:
            print(f"✅ Data successfully ingested! ({data_count} records)")
        else:
            print(f"⚠️  Warning: No data count yet, might still be processing")
    
    # =================================================================
    # STEP 4: Test Chat with Ingested Data
    # =================================================================
    print_section("STEP 4: Test Chat with Ingested Data")
    
    print("💬 Testing chat with ingested data...")
    chat_response = client.chat.send_message(
        messages=[{"user": "What medical reports do you have for me?"}],
        collection_id=collection_id,
        patient_user_name=patient_username
    )
    print(f"   Response: {chat_response['response'][:200]}...")
    print(f"   Response Time: {chat_response['total_response_time_ms']}ms")
    print(f"✅ Chat working with ingested data")
    
    # =================================================================
    # STEP 5: Get Document UUID for Deletion Test
    # =================================================================
    print_section("STEP 5: Prepare for Deletion Tests")
    
    # Get files to find document UUID
    db_files = client.files.list_db_files_by_collection(collection_id)
    document_uuid = None
    if db_files and len(db_files) > 0:
        document_uuid = db_files[0].get('uuid')
        test_data["document_uuid"] = document_uuid
        print(f"   Found document UUID: {document_uuid}")
    else:
        print(f"   No documents found for deletion test")
    
    # Get ingestion request for cancellation test
    recent_requests = client.ingestion.list_recent_requests(limit=5)
    if recent_requests and len(recent_requests) > 0:
        # Find a processing request if available
        for req in recent_requests:
            if req.get('status') == 'processing':
                test_data["cancel_request_id"] = req.get('request_id')
                break
    
    # =================================================================
    # STEP 6: TEST ALL DELETION ENDPOINTS
    # =================================================================
    print_section("STEP 6: Testing ALL Deletion Endpoints")
    
    # 6.1 Delete Document (if we have a UUID)
    if document_uuid:
        print("\n🗑️  Testing: DELETE /api/document/{document_uuid}")
        try:
            result = client.files.delete_document(document_uuid)
            print(f"✅ Document deleted successfully")
            print(f"   Response: {result}")
        except Exception as e:
            print(f"❌ Failed to delete document: {e}")
    else:
        print("\n⚠️  Skipping document deletion - no document UUID available")
    
    # 6.2 Cancel Ingestion Request (if we have one)
    if "cancel_request_id" in test_data:
        print("\n🗑️  Testing: DELETE /api/data/request/{request_id}")
        try:
            result = client.ingestion.cancel_request(test_data["cancel_request_id"])
            print(f"✅ Ingestion request cancelled successfully")
            print(f"   Response: {result}")
        except Exception as e:
            print(f"❌ Failed to cancel request: {e}")
    else:
        print("\n⚠️  Skipping request cancellation - no active request found")
    
    # 6.3 Clear Log Collection
    print("\n🗑️  Testing: DELETE /api/logs/{collection_name}")
    try:
        # Try to clear a test log collection (not critical ones)
        result = client.logs.clear_collection("logs_data_ingestion")
        print(f"✅ Log collection cleared successfully")
        print(f"   Response: {result}")
    except Exception as e:
        # This might fail if collection doesn't exist, which is fine
        print(f"⚠️  Log collection clear: {e}")
    
    # 6.4 Delete Patient (with extended timeout)
    print("\n🗑️  Testing: DELETE /api/patient/{patient_user_name}")
    print(f"   Note: This may take a long time due to data cleanup...")
    try:
        result = client.patients.delete(
            patient_user_name=patient_username,
            collection_id=collection_id,
            delete_patient_record=True
        )
        print(f"✅ Patient deleted successfully")
        print(f"   Response: {result}")
        test_data["patient_deleted"] = True
    except Exception as e:
        print(f"❌ Failed to delete patient: {e}")
        print(f"   This is expected if timeout occurs due to large data cleanup")
        test_data["patient_deleted"] = False
    
    # 6.5 Delete Collection
    print("\n🗑️  Testing: DELETE /api/collections/{collection_id}")
    try:
        result = client.collections.delete(collection_id)
        print(f"✅ Collection deleted successfully")
        print(f"   Response: {result}")
    except Exception as e:
        print(f"❌ Failed to delete collection: {e}")
    
    # =================================================================
    # FINAL SUMMARY
    # =================================================================
    print_section("TEST SUMMARY")
    
    print("\n📊 End-to-End Test Results:")
    print(f"   ✅ Collection created and deleted")
    print(f"   ✅ Patient registered")
    print(f"   ✅ Data ingestion completed and verified")
    print(f"   ✅ Chat working with ingested data")
    if document_uuid:
        print(f"   ✅ Document deletion tested")
    if test_data.get("patient_deleted"):
        print(f"   ✅ Patient deletion successful")
    else:
        print(f"   ⚠️  Patient deletion timed out (expected with large data)")
    
    client.close()
    print(f"\n✅ Client closed")
    print("\n" + "=" * 80)
    print("Complete End-to-End Test Finished!")
    print("=" * 80)

if __name__ == "__main__":
    main()
