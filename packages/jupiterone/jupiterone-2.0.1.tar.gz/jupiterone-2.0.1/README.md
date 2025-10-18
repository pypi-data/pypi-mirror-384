# JupiterOne Python SDK

[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)


A Python library for the [JupiterOne API](https://docs.jupiterone.io/reference).

## Installation

Requires Python 3.6+

`pip install jupiterone`

## Usage

##### Create a new client:

```python
from jupiterone import JupiterOneClient

j1 = JupiterOneClient(
    account='<yourAccountId>',
    token='<yourApiToken>',
    url='https://graphql.us.jupiterone.io',
    sync_url='https://api.us.jupiterone.io'
)

```

## Regional or Custom Tenant Support

For users with J1 accounts in the EU region for example, 
the 'url' parameter will need to be updated to "https://graphql.eu.jupiterone.io"
and the 'sync_url' parameter will need to be updated to "https://api.eu.jupiterone.io".

If no 'url' parameter is passed, 
the default of "https://graphql.us.jupiterone.io" is used,
and if no 'sync_url' parameter is passed,
the default of "https://api.us.jupiterone.io" is used.

## Method Examples:

### *See the examples/ directory for comprehensive usage examples:

#### **Core API Examples**
- `examples/01_client_setup_and_queries.py` - Client setup and basic J1QL queries
- `examples/02_entity_management.py` - Entity creation, updates, and deletion
- `examples/03_relationship_management.py` - Relationship management and traversal
- `examples/examples.py` - General API usage examples and patterns

#### **Integration & Management**
- `examples/04_integration_management.py` - Integration instance management and sync jobs
- `examples/05_alert_rules_and_smartclasses.py` - Alert rules and SmartClass operations
- `examples/06_advanced_operations.py` - Advanced API operations and workflows

#### **Specialized Features**
- `examples/07_account_parameters_list_example.py` - Account parameter management
- `examples/08_questions_management.py` - Complete question management workflows
- `examples/09_custom_file_transfer_example.py` - Custom File Transfer (CFT) integration examples
- `examples/create_integration_instance_example.py` - Integration instance creation examples

#### **Utility & Data Examples**
- `examples/J1QLdeferredResponse.py` - Deferred response query handling
- `examples/customFileTransferUploadData.py` - Custom file transfer data examples
- `examples/examples2.py` - Additional example patterns

##### Execute a query:

```python
# Basic query
QUERY = 'FIND Host'
query_result = j1.query_v1(query=QUERY)

# Including deleted entities
query_result = j1.query_v1(query=QUERY, include_deleted=True)

# Tree query
QUERY = 'FIND Host RETURN TREE'
query_result = j1.query_v1(query=QUERY)

# Complex query with properties
QUERY = 'FIND Host as h WITH platform = "linux" RETURN h.displayName, h.platform, h.ipAddress'
query_result = j1.query_v1(query=QUERY)

# Query with relationships
QUERY = 'FIND Host as h THAT HAS Application as a RETURN h.displayName, a.displayName.displayName'
query_result = j1.query_v1(query=QUERY)

# Using cursor query to return full set of paginated results
QUERY = "FIND (Device | Person)"
cursor_query_r = j1._cursor_query(query=QUERY)

# Using cursor query with parallel processing
QUERY = "FIND (Device | Person)"
cursor_query_r = j1._cursor_query(query=QUERY, max_workers=5)

# Using limit and skip query for pagination
QUERY = "FIND User"
limit_skip_result = j1._limit_and_skip_query(query=QUERY, skip=0, limit=100)

# Using deferredResponse with J1QL to return large datasets
QUERY = "FIND UnifiedDevice"
deferred_response_query_r = j1.query_with_deferred_response(query=QUERY)

# Deferred response with custom polling
deferred_response_query_r = j1.query_with_deferred_response(
    query=QUERY,
    polling_interval=30,  # seconds
    max_retries=10
)
```

##### Create an entity:

Note that the CreateEntity mutation behaves like an upsert, so a non-existent entity will be created or an existing entity will be updated.

```python
import time

# Basic entity creation
properties = {
    'myProperty': 'myValue',
    'tag.myTagProperty': 'value_will_be_a_tag'
}

entity = j1.create_entity(
   entity_key='my-unique-key',
   entity_type='my_type',
   entity_class='MyClass',
   properties=properties
)
print(entity['entity'])

# Create entity with complex properties
complex_properties = {
    'displayName': 'My Application Server',
    'tag.Environment': 'production',
    'tag.Team': 'engineering',
    'ipAddress': '192.168.1.100',
    'port': 8080,
    'isActive': True
}

entity = j1.create_entity(
   entity_key='app-server-001',
   entity_type='application_server',
   entity_class='Host',
   properties=complex_properties
)
```

#### Update an existing entity:
Only send in properties you want to add or update, other existing properties will not be modified.

```python
# Basic property update
properties = {
    'newProperty': 'newPropertyValue'
}

j1.update_entity(
    entity_id='<id-of-entity-to-update>',
    properties=properties
)

# Update with tags and complex properties
update_properties = {
    'tag.Status': 'maintenance',
    'lastUpdated': int(time.time()) * 1000,
    'isActive': False
}

j1.update_entity(
    entity_id='<id-of-entity-to-update>',
    properties=update_properties
)
```

#### Delete an entity:

```python
# Delete by entity ID
j1.delete_entity(entity_id='<id-of-entity-to-delete>')

# Delete with timestamp and hard delete option
j1.delete_entity(
    entity_id='<id-of-entity-to-delete>',
    timestamp=int(time.time()) * 1000,
    hard_delete=True  # Set to False for soft delete
)

# Soft delete (entity marked as deleted but not permanently removed)
j1.delete_entity(
    entity_id='<id-of-entity-to-delete>',
    hard_delete=False
)
```

##### Create a relationship

```python
# Basic relationship creation
j1.create_relationship(
    relationship_key='this_entity_relates_to_that_entity',
    relationship_type='my_relationship_type',
    relationship_class='MYRELATIONSHIP',
    from_entity_id='<id-of-source-entity>',
    to_entity_id='<id-of-destination-entity>'
)

# Create relationship with properties
j1.create_relationship(
    relationship_key='<user-entity-id>:user_accesses_application:<application-entity-id>',
    relationship_type='user_accesses_application',
    relationship_class='ACCESSES',
    from_entity_id='<user-entity-id>',
    to_entity_id='<application-entity-id>',
    properties={
        'accessLevel': 'read',
        'grantedOn': int(time.time()) * 1000,
        'grantedBy': 'admin@company.com'
    }
)

# Create relationship with complex properties
j1.create_relationship(
    relationship_key='<host-entity-id>:host_installed_software:<software-entity-id>',
    relationship_type='host_installed_software',
    relationship_class='INSTALLED',
    from_entity_id='<host-entity-id>',
    to_entity_id='<software-entity-id>',
    properties={
        'installedOn': int(time.time()) * 1000,
        'version': '2.1.0',
        'installPath': '/usr/local/bin/software',
        'permissions': ['read', 'execute']
    }
)
```

##### Update a relationship

```python
# Basic relationship update
j1.update_relationship(
    relationship_id='<id-of-relationship-to-update>',
    from_entity_id='<id-of-source-entity>',
    to_entity_id='<id-of-destination-entity>',
    properties={
        "<relationship-property-name>": "<relationship-property-updated-value>",
    },
)

# Update relationship with complex properties
j1.update_relationship(
    relationship_id='<id-of-relationship-to-update>',
    from_entity_id='<id-of-source-entity>',
    to_entity_id='<id-of-destination-entity>',
    properties={
        'accessLevel': 'write',
        'lastModified': int(time.time()) * 1000,
        'modifiedBy': 'security_team',
        'expiresOn': int(time.time() + 86400) * 1000  # 24 hours from now
    }
)

# Update relationship with tags
j1.update_relationship(
    relationship_id='<id-of-relationship-to-update>',
    from_entity_id='<id-of-source-entity>',
    to_entity_id='<id-of-destination-entity>',
    properties={
        'tag.Status': 'active',
        'tag.Priority': 'high',
        'tag.ReviewRequired': 'true'
    }
)

# Update relationship with custom timestamp
j1.update_relationship(
    relationship_id='<id-of-relationship-to-update>',
    from_entity_id='<id-of-source-entity>',
    to_entity_id='<id-of-destination-entity>',
    properties={
        'lastUpdated': int(time.time()) * 1000
    },
    timestamp=int(time.time()) * 1000  # Custom timestamp
)
```

##### Delete a relationship

```python
# Delete by relationship ID
j1.delete_relationship(relationship_id='<id-of-relationship-to-delete>')

# Delete with timestamp
j1.delete_relationship(
    relationship_id='<id-of-relationship-to-delete>',
    timestamp=int(time.time()) * 1000
)
```

##### Fetch Graph Entity Properties

```python
# Fetch all entity properties
properties = j1.fetch_all_entity_properties()
print(f"Found {len(properties)} entity properties")

# Properties are returned as a list of property objects
for prop in properties:
    print(f"Property: {prop.get('name')} - Type: {prop.get('type')}")
```

##### Fetch Graph Entity Tags

```python
# Fetch all entity tags
tags = j1.fetch_all_entity_tags()
print(f"Found {len(tags)} entity tags")

# Tags are returned as a list of tag objects
for tag in tags:
    print(f"Tag: {tag.get('name')} - Values: {tag.get('values')}")
```

##### Fetch Entity Raw Data

```python
# Fetch raw data for a specific entity
raw_data = j1.fetch_entity_raw_data(entity_id='<id-of-entity>')
print(f"Raw data keys: {list(raw_data.keys())}")

# Access specific raw data sections
if 'aws' in raw_data:
    aws_data = raw_data['aws']
    print(f"AWS data: {aws_data}")

if 'azure' in raw_data:
    azure_data = raw_data['azure']
    print(f"Azure data: {azure_data}")
```

##### Create Integration Instance

```python
# Basic integration instance creation
instance = j1.create_integration_instance(
    instance_name="AWS Production Account", 
    instance_description="Production AWS account integration"
)
print(f"Created instance: {instance['instance']['_id']}")

# Create integration instance with resource group assignment
instance = j1.create_integration_instance(
    instance_name="AWS Development Account", 
    instance_description="Development AWS account integration",
    resource_group_id="your-resource-group-id"
)

# Create integration instance with custom definition and resource group
instance = j1.create_integration_instance(
    instance_name="Custom Integration", 
    instance_description="Custom integration for internal systems",
    integration_definition_id="your-integration-definition-id",
    resource_group_id="your-resource-group-id"
)
```

##### Start Synchronization Job

```python
# Start sync job for an integration instance
sync_job = j1.start_sync_job(
    instance_id=instance_id,
    sync_mode="PATCH",
    source="integration-external"
)

sync_job_id = sync_job['job'].get('id')
print(f"Started sync job: {sync_job_id}")

# The returned job ID is used for subsequent operations
job_id = sync_job_id
```

##### Upload Batch of Entities

```python
# Prepare entities payload
entities_payload = [
    {
      "_key": "server-001",
      "_type": "aws_ec2_instance",
      "_class": "Host",
      "displayName": "web-server-001",
      "instanceId": "i-1234567890abcdef0",
      "instanceType": "t3.micro",
      "state": "running",
      "tag.Environment": "production",
      "tag.Team": "engineering"
    },
    {
      "_key": "server-002",
      "_type": "aws_ec2_instance",
      "_class": "Host",
      "displayName": "web-server-002",
      "instanceId": "i-0987654321fedcba0",
      "instanceType": "t3.small",
      "state": "running",
      "tag.Environment": "staging",
      "tag.Team": "engineering"
    },
    {
      "_key": "database-001",
      "_type": "aws_rds_instance",
      "_class": "Database",
      "displayName": "prod-database",
      "dbInstanceIdentifier": "prod-db",
      "engine": "postgres",
      "dbInstanceClass": "db.t3.micro",
      "tag.Environment": "production",
      "tag.Team": "data"
    }
]

# Upload entities batch
result = j1.upload_entities_batch_json(
    instance_job_id='<id-of-integration-sync-job>',
    entities_list=entities_payload
)
print(f"Uploaded {len(entities_payload)} entities")
```

##### Upload Batch of Relationships

```python
# Prepare relationships payload
relationships_payload = [
    {
      "_key": "server-001:aws_ec2_instance_connects_aws_rds_instance:database-001",
      "_class": "CONNECTS",
      "_type": "aws_ec2_instance_connects_aws_rds_instance",
      "_fromEntityKey": "server-001",
      "_toEntityKey": "database-001",
      "port": 5432,
      "protocol": "tcp",
      "encrypted": True
    },
    {
      "_key": "server-002:aws_ec2_instance_connects_aws_rds_instance:database-001",
      "_class": "CONNECTS",
      "_type": "aws_ec2_instance_connects_aws_rds_instance",
      "_fromEntityKey": "server-002",
      "_toEntityKey": "database-001",
      "port": 5432,
      "protocol": "tcp",
      "encrypted": True
    },
    {
      "_key": "user-001:aws_iam_user_owns_aws_ec2_instance:server-001",
      "_class": "OWNS",
      "_type": "aws_iam_user_owns_aws_ec2_instance",
      "_fromEntityKey": "user-001",
      "_toEntityKey": "server-001",
      "ownershipType": "creator"
    }
]

# Upload relationships batch
result = j1.upload_relationships_batch_json(
    instance_job_id='<id-of-integration-sync-job>',
    relationships_list=relationships_payload
)
print(f"Uploaded {len(relationships_payload)} relationships")
```

##### Upload Batch of Entities and Relationships

```python
# Prepare combined payload
combined_payload = {
    "entities": [
    {
      "_key": "vpc-001",
      "_type": "aws_vpc",
      "_class": "Network",
      "displayName": "production-vpc",
      "vpcId": "vpc-12345678",
      "cidrBlock": "10.0.0.0/16",
      "state": "available",
      "tag.Environment": "production",
      "tag.Purpose": "web_servers"
    },
    {
      "_key": "subnet-001",
      "_type": "aws_subnet",
      "_class": "Network",
      "displayName": "public-subnet-1a",
      "subnetId": "subnet-12345678",
      "cidrBlock": "10.0.1.0/24",
      "availabilityZone": "us-east-1a",
      "state": "available"
    }
],
    "relationships": [
    {
      "_key": "vpc-001:aws_vpc_contains_aws_subnet:subnet-001",
      "_class": "CONTAINS",
      "_type": "aws_vpc_contains_aws_subnet",
      "_fromEntityKey": "vpc-001",
      "_toEntityKey": "subnet-001"
    },
    {
      "_key": "subnet-001:aws_subnet_contains_aws_ec2_instance:server-001",
      "_class": "CONTAINS",
      "_type": "aws_subnet_contains_aws_ec2_instance",
      "_fromEntityKey": "subnet-001",
      "_toEntityKey": "server-001"
    }
]
}

# Upload combined batch
result = j1.upload_combined_batch_json(
    instance_job_id='<id-of-integration-sync-job>',
    combined_payload=combined_payload
)
print(f"Uploaded {len(combined_payload['entities'])} entities and {len(combined_payload['relationships'])} relationships")
```

##### Finalize Synchronization Job

```python
# Finalize the sync job
result = j1.finalize_sync_job(instance_job_id='<id-of-integration-sync-job>')
print(f"Finalized sync job: {result['job'].get('id')}")

# Check job status
if result['job']['status'] == 'COMPLETED':
    print("Sync job completed successfully")
elif result['job']['status'] == 'FAILED':
    print(f"Sync job failed: {result['job'].get('error', 'Unknown error')}")
```

##### Custom File Transfer (CFT) Integration Methods

```python
# Get a pre-signed URL for file upload
upload_info = j1.get_cft_upload_url(
    integration_instance_id='<id-of-integration-instance>',
    filename='data.csv',
    dataset_id='<id-of-dataset>'
)
print(f"Upload URL: {upload_info['uploadUrl']}")
print(f"Expires at: {upload_info['expiresAt']}")

# Upload a CSV file to the CFT integration
upload_result = j1.upload_cft_file(
    upload_url=upload_info['uploadUrl'],
    file_path='/path/to/your/data.csv'
)
print(f"Upload status: {upload_result['status_code']}")
print(f"Upload success: {upload_result['success']}")

# Invoke the CFT integration to process the uploaded file
invoke_result = j1.invoke_cft_integration(
    integration_instance_id='<id-of-integration-instance>'
)
if invoke_result is True:
    print("CFT integration invoked successfully")
elif invoke_result == 'ALREADY_RUNNING':
    print("CFT integration is already running")
else:
    print("Failed to invoke CFT integration")

# Complete workflow example
def upload_and_process_data(j1, instance_id, dataset_id, file_path):
    """Complete workflow for CFT data upload and processing"""
    try:
        # Step 1: Get upload URL
        upload_info = j1.get_cft_upload_url(instance_id, 'data.csv', dataset_id)
        
        # Step 2: Upload file
        upload_result = j1.upload_cft_file(upload_info['uploadUrl'], file_path)
        if not upload_result['success']:
            raise Exception(f"Upload failed: {upload_result['status_code']}")
        
        # Step 3: Invoke processing
        invoke_result = j1.invoke_cft_integration(instance_id)
        if invoke_result is True:
            print("Data uploaded and processing started successfully")
        else:
            print(f"Processing status: {invoke_result}")
            
    except Exception as e:
        print(f"Error in CFT workflow: {e}")

# Usage
upload_and_process_data(j1, 'instance-123', 'dataset-456', '/path/to/data.csv')
```

##### Fetch Integration Instance Jobs

```python
# Fetch all jobs for an integration instance
jobs = j1.fetch_integration_jobs(instance_id='<id-of-integration-instance>')
print(f"Found {len(jobs)} jobs for instance")

# Process job information
for job in jobs:
    print(f"Job ID: {job['_id']}")
    print(f"Status: {job['status']}")
    print(f"Started: {job.get('startedOn')}")
    print(f"Completed: {job.get('completedOn')}")
    print("---")
```

##### Fetch Integration Instance Job Events

```python
# Fetch events for a specific job
events = j1.fetch_integration_job_events(
    instance_id='<id-of-integration-instance>',
    instance_job_id='<id-of-integration-instance-job>'
)
print(f"Found {len(events)} events for job")

# Process event information
for event in events:
    print(f"Event: {event.get('event')}")
    print(f"Timestamp: {event.get('timestamp')}")
    print(f"Message: {event.get('message')}")
    print("---")
```

##### Create SmartClass

```python
# Create a new SmartClass
smartclass = j1.create_smartclass(
    smartclass_name='ProductionServers',
    smartclass_description='All production servers across cloud providers'
)
print(f"Created SmartClass: {smartclass['smartclass']['_id']}")
```

##### Create SmartClass Query

```python
# Add a query to the SmartClass
query = 'FIND Host WITH tag.Environment = "production"'
smartclass_query = j1.create_smartclass_query(
    smartclass_id='<id-of-smartclass>',
    query=query,
    query_description='Find all hosts tagged as production'
)
print(f"Added query to SmartClass: {smartclass_query['query']['_id']}")

# Add multiple queries to build a comprehensive SmartClass
queries = [
    ('FIND Host WITH tag.Environment = "production"', 'Production hosts'),
    ('FIND Database WITH tag.Environment = "production"', 'Production databases'),
    ('FIND Application WITH tag.Environment = "production"', 'Production applications')
]

for query_text, description in queries:
    j1.create_smartclass_query(
        smartclass_id='<id-of-smartclass>',
        query=query_text,
        query_description=description
    )
```

##### Run SmartClass Evaluation

```python
# Evaluate the SmartClass
evaluation = j1.evaluate_smartclass(smartclass_id='<id-of-smartclass>')
print(f"Started SmartClass evaluation: {evaluation['evaluation']['_id']}")

# Check evaluation status
if evaluation['evaluation']['status'] == 'COMPLETED':
    print("SmartClass evaluation completed")
    print(f"Entities found: {evaluation['evaluation'].get('entityCount', 0)}")
```

##### Get SmartClass Details

```python
# Get detailed information about a SmartClass
smartclass_details = j1.get_smartclass_details(smartclass_id='<id-of-smartclass>')
print(f"SmartClass: {smartclass_details['smartclass']['name']}")
print(f"Description: {smartclass_details['smartclass']['description']}")
print(f"Queries: {len(smartclass_details.get('queries', []))}")

# List all queries in the SmartClass
for query in smartclass_details.get('queries', []):
    print(f"Query: {query['query']}")
    print(f"Description: {query['description']}")
    print("---")
```

##### Generate J1QL from Natural Language Prompt

```python
# Generate J1QL from natural language
prompt = "Find all AWS EC2 instances that are running and tagged as production"
j1ql_result = j1.generate_j1ql(natural_language_prompt=prompt)
print(f"Generated J1QL: {j1ql_result['j1ql']}")

# More complex natural language queries
complex_prompts = [
    "Show me all databases that are not encrypted",
    "Find users who have admin access to production systems",
    "List all applications that haven't been updated in the last 30 days",
    "Show me all network connections between development and production environments"
]

for prompt in complex_prompts:
    result = j1.generate_j1ql(natural_language_prompt=prompt)
    print(f"Prompt: {prompt}")
    print(f"Generated J1QL: {result['j1ql']}")
    print("---")
```

##### Question Management Methods

```python
# Create a new question
question = j1.create_question(
    title="Security Compliance Check",
    queries=[
        {
            "query": "FIND User WITH mfaEnabled=false",
            "name": "UsersWithoutMFA",
            "resultsAre": "BAD"
        },
        {
            "query": "FIND Host WITH encrypted=false",
            "name": "UnencryptedHosts",
            "resultsAre": "BAD"
        }
    ],
    description="Check for security compliance violations",
    tags=["security", "compliance"],
    showTrend=True,
    pollingInterval="ONE_DAY"
)
print(f"Created question: {question['title']} (ID: {question['id']})")

# List existing questions
questions = j1.list_questions()
print(f"Found {len(questions)} questions")

# Search for specific questions
security_questions = j1.list_questions(search_query="security")
compliance_questions = j1.list_questions(tags=["compliance"])

# Get question details
question_details = j1.get_question_details(question_id=question['id'])
print(f"Question: {question_details['title']}")
print(f"Description: {question_details['description']}")
print(f"Queries: {len(question_details['queries'])}")

# Update an existing question
updated_question = j1.update_question(
    question_id=question['id'],
    title="Updated Security Compliance Check",
    description="Enhanced security compliance monitoring",
    tags=["security", "compliance", "enhanced"]
)
print(f"Updated question: {updated_question['title']}")

# Update specific fields only
j1.update_question(
    question_id=question['id'],
    description="Updated description only"
)

# Update queries with validation
updated_queries = [
    {
        "query": "FIND User WITH mfaEnabled=false AND active=true",
        "name": "ActiveUsersWithoutMFA",
        "resultsAre": "BAD"
    }
]
j1.update_question(
    question_id=question['id'],
    queries=updated_queries
)

# Delete a question
deleted_question = j1.delete_question(question_id=question['id'])
print(f"Deleted question: {deleted_question['title']}")

# Complete workflow example
def manage_security_questions(j1):
    """Complete workflow for managing security questions"""
    try:
        # Create a comprehensive security question
        security_question = j1.create_question(
            title="Production Security Audit",
            queries=[
                {
                    "query": "FIND Host WITH tag.Environment='production' AND encrypted=false",
                    "name": "UnencryptedProdHosts",
                    "resultsAre": "BAD"
                },
                {
                    "query": "FIND User WITH privileged=true AND lastLoginOn < date.now - 90 days",
                    "name": "InactivePrivilegedUsers",
                    "resultsAre": "BAD"
                }
            ],
            description="Comprehensive production security audit",
            tags=["security", "production", "audit"],
            showTrend=True,
            pollingInterval="ONE_DAY"
        )
        
        print(f"Created security question: {security_question['title']}")
        
        # Update the question with additional queries
        additional_queries = [
            {
                "query": "FIND Database WITH backupEnabled=false",
                "name": "DatabasesWithoutBackup",
                "resultsAre": "BAD"
            }
        ]
        
        updated_question = j1.update_question(
            question_id=security_question['id'],
            queries=additional_queries
        )
        
        print(f"Updated question with additional queries")
        
        # List all security questions
        all_security_questions = j1.list_questions(tags=["security"])
        print(f"Total security questions: {len(all_security_questions)}")
        
        # Clean up - delete the test question
        j1.delete_question(question_id=security_question['id'])
        print("Test question cleaned up")
        
    except Exception as e:
        print(f"Error in security question workflow: {e}")

# Usage
manage_security_questions(j1)
```

##### List Alert Rules

```python
# List all alert rules
alert_rules = j1.list_alert_rules()
print(f"Found {len(alert_rules)} alert rules")

# Process alert rule information
for rule in alert_rules:
    print(f"Rule ID: {rule['_id']}")
    print(f"Name: {rule['name']}")
    print(f"Description: {rule['description']}")
    print(f"Severity: {rule['severity']}")
    print(f"Status: {rule['status']}")
    print("---")
```

##### Get Alert Rule Details

```python
# Get detailed information about a specific alert rule
rule_details = j1.get_alert_rule_details(rule_id='<id-of-alert-rule>')
print(f"Rule: {rule_details['rule']['name']}")
print(f"Description: {rule_details['rule']['description']}")
print(f"J1QL: {rule_details['rule']['j1ql']}")
print(f"Severity: {rule_details['rule']['severity']}")
print(f"Polling Interval: {rule_details['rule']['pollingInterval']}")

# Check action configurations
if 'actionConfigs' in rule_details['rule']:
    print("Action Configurations:")
    for action in rule_details['rule']['actionConfigs']:
        print(f"  Type: {action['type']}")
        if action['type'] == 'WEBHOOK':
            print(f"  Endpoint: {action['endpoint']}")
        elif action['type'] == 'TAG_ENTITIES':
            print(f"  Tags: {action['tags']}")
```

##### Create Alert Rule

```python
# Basic alert rule creation
# polling_interval can be DISABLED, THIRTY_MINUTES, ONE_HOUR, FOUR_HOURS, EIGHT_HOURS, TWELVE_HOURS, ONE_DAY, or ONE_WEEK
# severity can be INFO, LOW, MEDIUM, HIGH, or CRITICAL

alert_rule = j1.create_alert_rule(
    name="Unencrypted Databases",
    description="Alert when databases are found without encryption",
    tags=['security', 'compliance'],
    polling_interval="ONE_DAY",
    severity="HIGH",
    j1ql="FIND Database WITH encrypted = false"
)
print(f"Created alert rule: {alert_rule['rule']['_id']}")

# Create alert rule with more complex J1QL
complex_rule = j1.create_alert_rule(
    name="Production Access Violations",
    description="Alert when non-admin users access production resources",
    tags=['security', 'access-control', 'production'],
    polling_interval="THIRTY_MINUTES",
    severity="CRITICAL",
    j1ql="""
    FIND User AS u 
    THAT HAS AccessPolicy AS ap 
    THAT ALLOWS * AS resource 
    WHERE resource.tag.Environment = 'production' 
    AND ap.accessLevel = 'admin' 
    AND u.tag.Role != 'admin'
    """
)

# Create alert rule with advanced configuration options
advanced_rule = j1.create_alert_rule(
    name="Advanced Security Monitoring",
    description="Comprehensive security monitoring with custom settings",
    tags=['security', 'monitoring'],
    polling_interval="ONE_HOUR",
    severity="HIGH",
    j1ql="FIND Finding WITH severity = 'HIGH'",
    query_name="security_findings",  # Custom query name
    trigger_actions_on_new_entities_only=False,  # Trigger on all entities
    ignore_previous_results=True,  # Ignore previous evaluation results
    notify_on_failure=True,  # Notify on evaluation failures
    templates={  # Custom templates for alert content
        "AlertSummary": "Security Finding: {{item.displayName}} - Severity: {{item.severity}}",
        "DetailedReport": "Finding ID: {{item._id}}\nDescription: {{item.description}}\nSeverity: {{item.severity}}"
    }
)
```

##### Create Alert Rule with Action Config

```python
# Webhook action configuration
webhook_action_config = {
            "type": "WEBHOOK",
            "endpoint": "https://webhook.domain.here/endpoint",
            "headers": {
              "Authorization": "Bearer <SECRET>",
            },
            "method": "POST",
            "body": {
              "queryData": "{{queries.query0.data}}"
            }
}

# Tag entities action configuration
tag_entities_action_config = {
            "type": "TAG_ENTITIES",
            "entities": "{{queries.query0.data}}",
            "tags": [
              {
                "name": "tagKey",
                "value": "tagValue"
              }
            ]
}

# Jira ticket creation action configuration
create_jira_ticket_action_config = {
          "integrationInstanceId" : "5b0eee42-60f5-467a-8125-08666f1383da",
          "type" : "CREATE_JIRA_TICKET",
          "entityClass" : "Record",
          "summary" : "Jira Task created via JupiterOne Alert Rule",
          "issueType" : "Task",
          "project" : "PROS",
          "additionalFields" : {
            "description" : {
              "type" : "doc",
              "version" : 1,
              "content" : [
                {
                  "type" : "paragraph",
                  "content" : [
                    {
                      "type" : "text",
                      "text" : "{{alertWebLink}}\n\n**Affected Items:**\n\n* {{queries.query0.data|mapProperty('displayName')|join('\n* ')}}"
                    }
                  ]
                }
              ]
            },
            "j1webLink" : "{{alertWebLink}}",
            "customfield_1234": "text-value",
            "customfield_5678": {
                "value": "select-value"
            },
            "labels" : [
              "label1","label2"
            ],
          }
}

# Create alert rule with webhook action
alert_rule = j1.create_alert_rule(
    name="Security Violation Alert",
    description="Alert security team of policy violations",
    tags=['security', 'automation'],
    polling_interval="ONE_HOUR",
    severity="HIGH",
    j1ql="FIND Finding WITH severity = 'HIGH'",
    action_configs=webhook_action_config
)

# Create alert rule with multiple actions
multiple_actions = [
    webhook_action_config,
    tag_entities_action_config
]

alert_rule = j1.create_alert_rule(
    name="Comprehensive Security Alert",
    description="Alert and tag security violations",
    tags=['security', 'compliance'],
    polling_interval="FOUR_HOURS",
    severity="MEDIUM",
    j1ql="FIND Finding WITH severity = ('HIGH' OR 'CRITICAL')",
    action_configs=multiple_actions
)
```

##### Delete Alert Rule

```python
# Delete an alert rule
result = j1.delete_alert_rule(rule_id='<id-of-alert-rule>')
print(f"Deleted alert rule: {result['rule']['_id']}")

# Verify deletion by attempting to get details (should fail)
try:
    j1.get_alert_rule_details(rule_id='<id-of-alert-rule>')
except Exception as e:
    print(f"Rule successfully deleted: {e}")
```

##### Update Alert Rule

```python
# polling_interval can be DISABLED, THIRTY_MINUTES, ONE_HOUR, FOUR_HOURS, EIGHT_HOURS, TWELVE_HOURS, ONE_DAY, or ONE_WEEK
# tag_op can be OVERWRITE or APPEND
# severity can be INFO, LOW, MEDIUM, HIGH, or CRITICAL
# action_configs_op can be OVERWRITE or APPEND

# Basic alert rule configuration
alert_rule_config_alert = [
    {
        "type": "CREATE_ALERT"
    }
]

# Tag entities configuration
alert_rule_config_tag = [
    {
        "type": "TAG_ENTITIES",
        "entities": "{{queries.query0.data}}",
        "tags": [
            {
                "name": "tagName",
                "value": "tagValue"
            }
        ]
    }
]

# Webhook configuration
alert_rule_config_webhook = [
    {
        "type": "WEBHOOK",
        "endpoint": "https://webhook.example",
        "headers": {
            "Authorization": "Bearer <TOKEN>"
        },
        "method": "POST",
        "body": {
            "queryData": "{{queries.query0.data}}"
        }
    }
]

# Jira ticket configuration
create_jira_ticket_action_config = {
          "integrationInstanceId" : "5b0eee42-60f5-467a-8125-08666f1383da",
          "type" : "CREATE_JIRA_TICKET",
          "entityClass" : "Record",
          "summary" : "Jira Task created via JupiterOne Alert Rule",
          "issueType" : "Task",
          "project" : "PROS",
          "additionalFields" : {
            "description" : {
              "type" : "doc",
              "version" : 1,
              "content" : [
                {
                  "type" : "paragraph",
                  "content" : [
                    {
                      "type" : "text",
                      "text" : "{{alertWebLink}}\n\n**Affected Items:**\n\n* {{queries.query0.data|mapProperty('displayName')|join('\n* ')}}"
                    }
                  ]
                }
              ]
            },
            "j1webLink" : "{{alertWebLink}}",
            "customfield_1234": "text-value",
            "customfield_5678": {
                "value": "select-value"
            },
            "labels" : [
              "label1","label2"
            ],
          }
}

# Multiple action configurations
alert_rule_config_multiple = [
    {
        "type": "WEBHOOK",
        "endpoint": "https://webhook.example",
        "headers": {
            "Authorization": "Bearer <TOKEN>"
        },
        "method": "POST",
        "body": {
            "queryData": "{{queries.query0.data}}"
        }
    },
    {
        "type": "TAG_ENTITIES",
        "entities": "{{queries.query0.data}}",
        "tags": [
            {
                "name": "tagName",
                "value": "tagValue"
            }
        ]
    }
]

# Update alert rule with comprehensive changes
updated_rule = j1.update_alert_rule(
    rule_id="<id-of-alert-rule>",
    name="Updated Alert Rule Name",
    description="Updated Alert Rule Description",
    j1ql="FIND Finding WITH severity = 'HIGH'",
    polling_interval="ONE_WEEK",
    tags=['tag1', 'tag2', 'tag3'],
    tag_op="OVERWRITE",
    severity="INFO",
    action_configs=alert_rule_config_tag,
    action_configs_op="OVERWRITE",
    query_name="updated_findings",  # Update query name
    trigger_actions_on_new_entities_only=False,  # Update trigger behavior
    ignore_previous_results=True,  # Update result handling
    notify_on_failure=False,  # Update notification settings
    templates={  # Update templates
        "NewTemplate": "Updated: {{item.displayName}} - {{item.severity}}"
    }
)

# Update only tags (overwrite existing)
j1.update_alert_rule(
    rule_id='<id-of-alert-rule>',
    tags=['newTag1', 'newTag2'],
    tag_op="OVERWRITE"
)

# Append additional tags
j1.update_alert_rule(
    rule_id='<id-of-alert-rule>',
    tags=['additionalTag1', 'additionalTag2'],
    tag_op="APPEND"
)

# Update only the J1QL query
j1.update_alert_rule(
    rule_id='<id-of-alert-rule>',
    j1ql="FIND Finding WITH severity = ('HIGH' OR 'CRITICAL')"
)

# Update polling interval and severity
j1.update_alert_rule(
    rule_id='<id-of-alert-rule>',
    polling_interval="THIRTY_MINUTES",
    severity="HIGH"
)

# Update advanced configuration parameters
j1.update_alert_rule(
    rule_id='<id-of-alert-rule>',
    query_name="custom_query_name",  # Update query name
    trigger_actions_on_new_entities_only=True,  # Only trigger on new entities
    ignore_previous_results=False,  # Consider previous results
    notify_on_failure=True  # Notify on evaluation failures
)

# Update templates for alert content
j1.update_alert_rule(
    rule_id='<id-of-alert-rule>',
    templates={
        "SecurityAlert": "Security Issue: {{item.displayName}}",
        "ComplianceReport": "Compliance Violation: {{item.description}}"
    }
)
```

##### Evaluate Alert Rule

```python
# Manually evaluate an alert rule
evaluation = j1.evaluate_alert_rule(rule_id='<id-of-alert-rule>')
print(f"Started evaluation: {evaluation['evaluation']['_id']}")

# Check evaluation status
if evaluation['evaluation']['status'] == 'COMPLETED':
    print("Evaluation completed successfully")
    print(f"Entities found: {evaluation['evaluation'].get('entityCount', 0)}")
elif evaluation['evaluation']['status'] == 'FAILED':
    print(f"Evaluation failed: {evaluation['evaluation'].get('error', 'Unknown error')}")
```

##### Get Compliance Framework Item

```python
# Get details of a compliance framework item
item_details = j1.get_compliance_framework_item_details(item_id="<id-of-item>")
print(f"Item: {item_details['item']['name']}")
print(f"Description: {item_details['item']['description']}")
print(f"Category: {item_details['item']['category']}")
print(f"Status: {item_details['item']['status']}")

# Access compliance requirements
if 'requirements' in item_details['item']:
    print("Requirements:")
    for req in item_details['item']['requirements']:
        print(f"  - {req['description']}")
```

##### List Alert Rule Evaluation Results

```python
# List evaluation results for a specific rule
evaluations = j1.list_alert_rule_evaluation_results(rule_id="<id-of-rule>")
print(f"Found {len(evaluations)} evaluations")

# Process evaluation results
for evaluation in evaluations:
    print(f"Evaluation ID: {evaluation['_id']}")
    print(f"Status: {evaluation['status']}")
    print(f"Started: {evaluation.get('startedOn')}")
    print(f"Completed: {evaluation.get('completedOn')}")
    print(f"Entities found: {evaluation.get('entityCount', 0)}")
    print("---")
```

##### Fetch Evaluation Result Download URL

```python
# Get download URL for evaluation results
download_url = j1.fetch_evaluation_result_download_url(
    raw_data_key="RULE_EVALUATION/<id-of-evaluation>/query0.json"
)
print(f"Download URL: {download_url['url']}")

# The URL is typically valid for a limited time
print(f"URL expires: {download_url.get('expires')}")
```

##### Fetch Downloaded Evaluation Results

```python
# Download and process evaluation results
download_url = "https://download.us.jupiterone.io/<id-of-rule>/RULE_EVALUATION/<id-of-evaluation>/<epoch>/query0.json?token=<TOKEN>&Expires=<epoch>"
results = j1.fetch_downloaded_evaluation_results(download_url=download_url)

print(f"Downloaded {len(results)} results")

# Process the results
for result in results:
    print(f"Entity: {result.get('displayName', result.get('_id'))}")
    print(f"Type: {result.get('_type')}")
    print(f"Class: {result.get('_class')}")
    print("---")
```

##### Get Integration Definition Details

```python
# Get details for AWS integration
# examples: 'aws', 'azure', 'google_cloud'
aws_details = j1.get_integration_definition_details(integration_type="aws")
print(f"AWS Integration: {aws_details['definition']['name']}")
print(f"Description: {aws_details['definition']['description']}")

# Get details for Azure integration
azure_details = j1.get_integration_definition_details(integration_type="azure")
print(f"Azure Integration: {azure_details['definition']['name']}")

# Get details for Google Cloud integration
gcp_details = j1.get_integration_definition_details(integration_type="google_cloud")
print(f"Google Cloud Integration: {gcp_details['definition']['name']}")

# Access configuration fields
if 'configFields' in aws_details['definition']:
    print("AWS Configuration Fields:")
    for field in aws_details['definition']['configFields']:
        print(f"  - {field['name']}: {field['type']}")
```

##### Fetch Integration Instances

```python
# Fetch all instances of a specific integration type
aws_instances = j1.fetch_integration_instances(definition_id="<id-of-definition>")
print(f"Found {len(aws_instances)} AWS integration instances")

# Process instance information
for instance in aws_instances:
    print(f"Instance ID: {instance['_id']}")
    print(f"Name: {instance['name']}")
    print(f"Description: {instance['description']}")
    print(f"Status: {instance['status']}")
    print(f"Last sync: {instance.get('lastSyncJob', {}).get('completedOn')}")
    print("---")
```

##### Fetch Integration Instance Details

```python
# Get detailed information about a specific integration instance
instance_details = j1.get_integration_instance_details(instance_id="<id-of-integration-instance>")
print(f"Instance: {instance_details['instance']['name']}")
print(f"Description: {instance_details['instance']['description']}")
print(f"Status: {instance_details['instance']['status']}")
print(f"Definition: {instance_details['instance']['definition']['name']}")

# Access configuration
if 'config' in instance_details['instance']:
    print("Configuration:")
    for key, value in instance_details['instance']['config'].items():
        if key != 'password':  # Don't print sensitive data
            print(f"  {key}: {value}")

# Access recent jobs
if 'recentJobs' in instance_details['instance']:
    print("Recent Jobs:")
    for job in instance_details['instance']['recentJobs']:
        print(f"  Job ID: {job['_id']}")
        print(f"  Status: {job['status']}")
        print(f"  Started: {job.get('startedOn')}")
        print(f"  Completed: {job.get('completedOn')}")
```

##### Get Account Parameter Details

```python
# Get details of a specific parameter
param_details = j1.get_parameter_details(name="ParameterName")
print(f"Parameter: {param_details['parameter']['name']}")
print(f"Value: {param_details['parameter']['value']}")
print(f"Secret: {param_details['parameter']['secret']}")
print(f"Created: {param_details['parameter']['createdOn']}")
print(f"Updated: {param_details['parameter']['updatedOn']}")

# Get details for common parameters
common_params = [
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AZURE_CLIENT_ID",
    "GCP_PROJECT_ID"
]

for param_name in common_params:
    try:
        details = j1.get_parameter_details(name=param_name)
        print(f"{param_name}: {'***' if details['parameter']['secret'] else details['parameter']['value']}")
    except Exception as e:
        print(f"{param_name}: Not found")
```

##### List Account Parameters

```python
# List all account parameters
parameters = j1.list_account_parameters()
print(f"Found {len(parameters)} parameters")

# Process parameter information
for param in parameters:
    print(f"Parameter: {param['name']}")
    print(f"Secret: {param['secret']}")
    print(f"Created: {param['createdOn']}")
    print(f"Updated: {param['updatedOn']}")
    if not param['secret']:
        print(f"Value: {param['value']}")
    print("---")

# Filter parameters by type
secret_params = [p for p in parameters if p['secret']]
non_secret_params = [p for p in parameters if not p['secret']]

print(f"Secret parameters: {len(secret_params)}")
print(f"Non-secret parameters: {len(non_secret_params)}")
```

##### Create or Update Account Parameter

```python
# Create a new parameter
result = j1.create_update_parameter(
    name="API_ENDPOINT", 
    value="https://api.example.com", 
    secret=False
)
print(f"Created/Updated parameter: {result['parameter']['name']}")

# Create a secret parameter
result = j1.create_update_parameter(
    name="DATABASE_PASSWORD", 
    value="super-secret-password", 
    secret=True
)
print(f"Created/Updated secret parameter: {result['parameter']['name']}")

# Update an existing parameter
result = j1.create_update_parameter(
    name="API_ENDPOINT", 
    value="https://new-api.example.com", 
    secret=False
)
print(f"Updated parameter: {result['parameter']['name']}")

# Common parameter creation examples
common_parameters = [
    ("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE", True),
    ("AWS_SECRET_ACCESS_KEY", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", True),
    ("AZURE_CLIENT_ID", "12345678-1234-1234-1234-123456789012", True),
    ("AZURE_CLIENT_SECRET", "azure-secret-key", True),
    ("GCP_PROJECT_ID", "my-gcp-project", False),
    ("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX", True),
    ("JIRA_URL", "https://company.atlassian.net", False),
    ("JIRA_USERNAME", "jira-user@company.com", False),
    ("JIRA_API_TOKEN", "jira-api-token", True)
]

for name, value, is_secret in common_parameters:
    try:
        result = j1.create_update_parameter(name=name, value=value, secret=is_secret)
        print(f"Created/Updated {name}")
    except Exception as e:
        print(f"Failed to create/update {name}: {e}")
```
