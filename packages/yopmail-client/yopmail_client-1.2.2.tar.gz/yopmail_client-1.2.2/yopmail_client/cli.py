"""
Command-line interface for YOPmail client.

This module provides a CLI entry point for the YOPmail client,
allowing users to interact with YOPmail services from the command line.
"""

import argparse
import logging
import sys
from typing import List, Optional

from .client import YOPMailClient
from .utils import Message


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def print_messages(messages: List[Message], show_details: bool = False) -> None:
    """Print messages in a formatted way."""
    if not messages:
        print("No messages found.")
        return
    
    print(f"Found {len(messages)} message(s):")
    print("-" * 50)
    
    for i, msg in enumerate(messages, 1):
        print(f"{i}. Subject: {msg.subject}")
        if show_details:
            print(f"   ID: {msg.id}")
            print(f"   Sender: {msg.sender or 'Unknown'}")
            print(f"   Time: {msg.time or 'Unknown'}")
        print()


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="YOPmail Client - Interact with YOPmail disposable email service"
    )
    
    parser.add_argument(
        "mailbox",
        help="Mailbox name (without @yopmail.com)"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List messages in inbox"
    )
    
    parser.add_argument(
        "--fetch", "-f",
        type=str,
        metavar="MESSAGE_ID",
        help="Fetch specific message by ID"
    )
    
    parser.add_argument(
        "--send", "-s",
        action="store_true",
        help="Send an email message"
    )
    
    parser.add_argument(
        "--to",
        type=str,
        help="Recipient email address (must be @yopmail.com)"
    )
    
    parser.add_argument(
        "--subject",
        type=str,
        help="Email subject"
    )
    
    parser.add_argument(
        "--body",
        type=str,
        help="Email body content"
    )
    
    parser.add_argument(
        "--rss",
        action="store_true",
        help="Get RSS feed URL for the mailbox"
    )
    
    parser.add_argument(
        "--rss-data",
        action="store_true",
        help="Get RSS feed data for the mailbox"
    )
    
    parser.add_argument(
        "--rss-mailbox",
        type=str,
        help="Specific mailbox for RSS feed (default: current mailbox)"
    )
    
    parser.add_argument(
        "--details", "-d",
        action="store_true",
        help="Show detailed message information"
    )
    
    parser.add_argument(
        "--page", "-p",
        type=int,
        default=1,
        help="Page number for message listing (default: 1)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize client
        config = {"timeout": args.timeout}
        client = YOPMailClient(args.mailbox, config=config)
        
        with client:
            # Open inbox
            print(f"Opening inbox for {args.mailbox}@yopmail.com...")
            client.open_inbox()
            
            if args.list:
                # List messages
                messages = client.list_messages(page=args.page)
                print_messages(messages, show_details=args.details)
                
            elif args.fetch:
                # Fetch specific message
                print(f"Fetching message {args.fetch}...")
                content = client.fetch_message(args.fetch)
                print(f"Message content ({len(content)} characters):")
                print("-" * 50)
                print(content[:500] + "..." if len(content) > 500 else content)
                
            elif args.send:
                # Send email message
                if not args.to or not args.subject or not args.body:
                    print("Error: --to, --subject, and --body are required for sending emails")
                    sys.exit(1)
                
                print(f"Sending email to {args.to}...")
                try:
                    result = client.send_message(args.to, args.subject, args.body)
                    if result["success"]:
                        print(f"Message sent successfully!")
                        print(f"Recipient: {result['recipient']}")
                        print(f"Subject: {result['subject']}")
                    else:
                        print(f"Failed to send message: {result.get('message', 'Unknown error')}")
                        sys.exit(1)
                except ValueError as e:
                    print(f"Validation error: {e}")
                    sys.exit(1)
                except Exception as e:
                    print(f"Send failed: {e}")
                    sys.exit(1)
                
            elif args.rss:
                # Get RSS feed URL
                target_mailbox = args.rss_mailbox or args.mailbox
                rss_url = client.get_rss_feed_url(target_mailbox)
                print(f"RSS Feed URL for {target_mailbox}@yopmail.com:")
                print(f"  {rss_url}")
                
            elif args.rss_data:
                # Get RSS feed data
                target_mailbox = args.rss_mailbox or args.mailbox
                print(f"Getting RSS feed data for {target_mailbox}@yopmail.com...")
                try:
                    rss_data = client.get_rss_feed_data(target_mailbox)
                    print(f"RSS Feed URL: {rss_data['rss_url']}")
                    print(f"Message Count: {rss_data['message_count']}")
                    
                    if rss_data['messages']:
                        print("\nRecent Messages:")
                        for i, msg in enumerate(rss_data['messages'][:5], 1):
                            print(f"  {i}. {msg['subject']} (from: {msg['sender']})")
                            print(f"     Date: {msg['date']}")
                            print(f"     URL: {msg['url']}")
                            print()
                    else:
                        print("No messages found in RSS feed")
                        
                except Exception as e:
                    print(f"RSS feed error: {e}")
                    sys.exit(1)
                
            else:
                # Default: show inbox info
                info = client.get_inbox_info()
                print(f"Inbox for {info['mailbox']}@yopmail.com:")
                print(f"Messages: {info['message_count']}")
                
                if info['has_messages']:
                    print("\nRecent messages:")
                    for msg in info['messages'][:5]:  # Show first 5
                        print(f"  - {msg['subject']} (from: {msg['sender'] or 'Unknown'})")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
