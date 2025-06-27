#!/usr/bin/env python3
"""
Test script to generate sample data and test the anonymization connector.
"""

import json
import sys
from datetime import datetime
from typing import Any, Dict

from airbyte_cdk.models import AirbyteMessage, AirbyteRecordMessage, ConfiguredAirbyteCatalog, Type


def create_test_record(stream_name: str, data: Dict[str, Any]) -> AirbyteMessage:
    """Create a test Airbyte record message."""
    record = AirbyteRecordMessage(
        stream=stream_name,
        data=data,
        emitted_at=int(datetime.now().timestamp() * 1000)
    )
    
    return AirbyteMessage(
        type=Type.RECORD,
        record=record
    )

def generate_sample_data():
    """Generate sample user data for testing."""
    sample_users = [
        {
            "id": 1,
            "email": "john.doe@company.com",
            "first_name": "John",
            "last_name": "Doe", 
            "phone": "(555) 123-4567",
            "ssn": "123-45-6789",
            "salary": 75000.00,
            "department": "Engineering"
        },
        {
            "id": 2,
            "email": "jane.smith@company.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "(555) 987-6543", 
            "ssn": "987-65-4321",
            "salary": 82000.00,
            "department": "Marketing"
        },
        {
            "id": 3,
            "email": "bob.johnson@company.com",
            "first_name": "Bob",
            "last_name": "Johnson",
            "phone": "(555) 456-7890",
            "ssn": "456-78-9012",
            "salary": 68000.00,
            "department": "Sales"
        },
        {
            "id": 4,
            "email": "alice.wilson@company.com", 
            "first_name": "Alice",
            "last_name": "Wilson",
            "phone": "(555) 321-0987",
            "ssn": "321-09-8765",
            "salary": 91000.00,
            "department": "Engineering"
        },
        {
            "id": 5,
            "email": "john.doe@company.com",  # Duplicate email to test consistency
            "first_name": "John",
            "last_name": "Doe",
            "phone": "(555) 123-4567",
            "ssn": "123-45-6789", 
            "salary": 75000.00,
            "department": "Engineering"
        }
    ]
    
    return [create_test_record("users", user) for user in sample_users]

def test_anonymization():
    """Test the anonymization connector with sample data."""
    print("Testing Airbyte Anonymization Connector")
    print("=" * 50)
    
    try:
        with open('test_config.json', 'r') as f:
            config = json.load(f)
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Error loading configuration: {e}")
        return False
    
    try:
        with open('test_catalog.json', 'r') as f:
            catalog_data = json.load(f)
        catalog = ConfiguredAirbyteCatalog(**catalog_data)
        print("✓ Catalog loaded successfully")
    except Exception as e:
        print(f"✗ Error loading catalog: {e}")
        return False
    
    try:
        sample_records = generate_sample_data()
        print(f"✓ Generated {len(sample_records)} sample records")
    except Exception as e:
        print(f"✗ Error generating sample data: {e}")
        return False
    
    try:
        from destination_anonymization import DestinationAnonymization
        
        connector = DestinationAnonymization()
        
        print("\n--- Testing spec() ---")
        spec = connector.spec(None)
        print(f"✓ Spec returned {len(spec)} configuration properties")
        
        print("\n--- Testing check() ---")
        check_result = connector.check(None, config)
        print(f"✓ Check result: {check_result.status}")
        if check_result.message:
            print(f"  Message: {check_result.message}")
        
        print("\n--- Testing write() (anonymization) ---")
        print("Original data:")
        for i, record in enumerate(sample_records):
            print(f"  Record {i+1}: {record.record.data}")
        
        print("\nAnonymized data:")
        anonymized_records = list(connector.write(config, catalog, sample_records))
        
        for i, record in enumerate(anonymized_records):
            if record.type == Type.RECORD:
                print(f"  Record {i+1}: {record.record.data}")
        
        print("\n--- Testing consistency ---")
        duplicate_records = [r for r in anonymized_records if r.type == Type.RECORD]
        if len(duplicate_records) >= 2:
            first_john = duplicate_records[0].record.data
            last_john = duplicate_records[-1].record.data
            
            if first_john.get('email') == last_john.get('email'):
                print("✓ Email anonymization is consistent")
            else:
                print("✗ Email anonymization is NOT consistent")
                print(f"  First: {first_john.get('email')}")
                print(f"  Last: {last_john.get('email')}")
        
        print("\n✓ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Error testing connector: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_anonymization()
    sys.exit(0 if success else 1)
