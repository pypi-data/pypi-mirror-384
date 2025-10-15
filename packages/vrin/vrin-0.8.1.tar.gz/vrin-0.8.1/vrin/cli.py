#!/usr/bin/env python3
"""
Command-line interface for the VRIN SDK
"""

import argparse
import json
import sys
import os
from typing import Optional
from .client import VRINClient
from .models import Document
from .exceptions import VRINError, JobFailedError, TimeoutError


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="VRIN Hybrid RAG SDK - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Insert knowledge
  vrin insert --content "Machine learning is a subset of AI" --title "ML Basics"
  
  # Query the knowledge base
  vrin query "What is machine learning?"
  
  # Check job status
  vrin status job_123
  
  # Insert and wait for completion
  vrin insert --content "Your content" --wait
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Insert command
    insert_parser = subparsers.add_parser('insert', help='Insert knowledge into the system')
    insert_parser.add_argument('--content', required=True, help='Knowledge content')
    insert_parser.add_argument('--title', help='Knowledge title')
    insert_parser.add_argument('--tags', nargs='+', help='Knowledge tags')
    insert_parser.add_argument('--source', help='Knowledge source')
    insert_parser.add_argument('--user-id', help='User ID')
    insert_parser.add_argument('--type', default='text', help='Content type')
    insert_parser.add_argument('--wait', action='store_true', help='Wait for completion')
    insert_parser.add_argument('--timeout', type=int, default=300, help='Timeout in seconds')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query the knowledge base')
    query_parser.add_argument('query', help='Search query')
    query_parser.add_argument('--user-id', help='User ID for personalized results')
    query_parser.add_argument('--max-results', type=int, default=10, help='Maximum results')
    query_parser.add_argument('--search-type', choices=['hybrid', 'sparse', 'dense'], 
                             default='hybrid', help='Search type')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check job status')
    status_parser.add_argument('job_id', help='Job ID to check')
    status_parser.add_argument('--wait', action='store_true', help='Wait for completion')
    status_parser.add_argument('--timeout', type=int, default=300, help='Timeout in seconds')
    
    # Batch insert command
    batch_parser = subparsers.add_parser('batch', help='Insert multiple knowledge items')
    batch_parser.add_argument('--file', required=True, help='JSON file with knowledge items')
    batch_parser.add_argument('--wait', action='store_true', help='Wait for completion')
    batch_parser.add_argument('--timeout', type=int, default=300, help='Timeout in seconds')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Get API key
    api_key = os.environ.get('VRIN_API_KEY')
    if not api_key:
        print("Error: VRIN_API_KEY environment variable not set")
        print("Please set your API key: export VRIN_API_KEY='your_api_key_here'")
        sys.exit(1)
    
    try:
        client = VRINClient(api_key=api_key)
        
        if args.command == 'insert':
            handle_insert(client, args)
        elif args.command == 'query':
            handle_query(client, args)
        elif args.command == 'status':
            handle_status(client, args)
        elif args.command == 'batch':
            handle_batch(client, args)
            
    except (VRINError, JobFailedError, TimeoutError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)


def handle_insert(client: VRINClient, args):
    """Handle knowledge insertion."""
    if args.wait:
        print("Inserting knowledge and waiting for completion...")
        job = client.insert_and_wait(
            content=args.content,
            title=args.title,
            tags=args.tags,
            source=args.source,
            user_id=args.user_id,
            document_type=args.type,
            timeout=args.timeout
        )
        print(f"✅ Knowledge processed successfully!")
        print(f"Job ID: {job.job_id}")
        print(f"Status: {job.status}")
        if job.completion_time:
            print(f"Completed at: {job.completion_time}")
    else:
        print("Inserting knowledge...")
        job = client.insert(
            content=args.content,
            title=args.title,
            tags=args.tags,
            source=args.source,
            user_id=args.user_id,
            document_type=args.type
        )
        print(f"✅ Knowledge inserted successfully!")
        print(f"Job ID: {job.job_id}")
        print(f"Status: {job.status}")
        print(f"Estimated completion: {job.estimated_completion}")


def handle_query(client: VRINClient, args):
    """Handle knowledge base query."""
    print(f"Querying: {args.query}")
    results = client.query(
        query=args.query,
        user_id=args.user_id,
        max_results=args.max_results,
        search_type=args.search_type
    )
    
    if not results:
        print("No results found.")
        return
    
    print(f"\nFound {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        print(f"Result {i}:")
        print(f"  Content: {result.content}")
        print(f"  Score: {result.score:.3f}")
        print(f"  Title: {result.title}")
        print(f"  Tags: {', '.join(result.tags) if result.tags else 'None'}")
        print(f"  Source: {result.source}")
        print(f"  Search Type: {result.search_type}")
        print()


def handle_status(client: VRINClient, args):
    """Handle job status check."""
    if args.wait:
        print(f"Waiting for job {args.job_id} to complete...")
        job = client.wait_for_job(args.job_id, timeout=args.timeout)
        print(f"✅ Job completed!")
    else:
        print(f"Checking status for job {args.job_id}...")
        job = client.get_job_status(args.job_id)
    
    print(f"Job ID: {job.job_id}")
    print(f"Status: {job.status}")
    print(f"Message: {job.message}")
    print(f"Progress: {job.progress}%")
    
    if job.creation_time:
        print(f"Created: {job.creation_time}")
    if job.completion_time:
        print(f"Completed: {job.completion_time}")
    if job.error_details:
        print(f"Error: {job.error_details}")


def handle_batch(client: VRINClient, args):
    """Handle batch knowledge insertion."""
    try:
        with open(args.file, 'r') as f:
            documents_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {args.file} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file {args.file}")
        sys.exit(1)
    
    # Convert to Document objects
    documents = []
    for doc_data in documents_data:
        documents.append(Document(**doc_data))
    
    print(f"Inserting {len(documents)} knowledge items...")
    jobs = client.batch_insert(documents)
    
    print(f"✅ Inserted {len(jobs)} knowledge items")
    for job in jobs:
        print(f"  - {job.job_id}: {job.status}")
    
    if args.wait:
        print("\nWaiting for all jobs to complete...")
        job_ids = [job.job_id for job in jobs]
        completed_jobs = client.batch_wait_for_jobs(job_ids, timeout=args.timeout)
        
        print(f"\n✅ All jobs completed!")
        for job in completed_jobs:
            status_icon = "✅" if job.is_completed else "❌"
            print(f"  {status_icon} {job.job_id}: {job.status}")
            if job.is_failed and job.error_details:
                print(f"    Error: {job.error_details}")


if __name__ == '__main__':
    main() 