#!/usr/bin/env python3
"""
Database migration management script for SothemaAI auth service.
Provides commands to run, rollback, and check migration status.
"""

import os
import sys
import argparse
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MigrationManager:
    """Manages database migrations for the auth service"""

    def __init__(self, service_dir):
        self.service_dir = service_dir
        self.alembic_cmd = ['python3', '-m', 'alembic']

    def run_command(self, args, cwd=None):
        """Run an alembic command"""
        cmd = self.alembic_cmd + args
        cwd = cwd or self.service_dir

        try:
            import os
            os.chdir(cwd)
            cmd_str = ' '.join(cmd)
            result = os.system(cmd_str)
            if result == 0:
                logger.info("Command succeeded: {}".format(cmd_str))
                return True
            else:
                logger.error("Command failed: {}".format(cmd_str))
                return False
        except Exception as e:
            logger.error("Error running command: {}".format(e))
            return False

    def current(self):
        """Show current migration status"""
        logger.info("Checking current migration status...")
        return self.run_command(['current'])

    def history(self):
        """Show migration history"""
        logger.info("Showing migration history...")
        return self.run_command(['history'])

    def upgrade(self, revision='head'):
        """Upgrade to a specific revision"""
        logger.info("Upgrading to revision: {}".format(revision))
        return self.run_command(['upgrade', revision])

    def downgrade(self, revision):
        """Downgrade to a specific revision"""
        logger.info("Downgrading to revision: {}".format(revision))
        return self.run_command(['downgrade', revision])

    def revision(self, message, autogenerate=True):
        """Create a new revision"""
        args = ['revision']
        if autogenerate:
            args.append('--autogenerate')
        args.extend(['-m', message])
        logger.info("Creating new revision: {}".format(message))
        return self.run_command(args)

def main():
    parser = argparse.ArgumentParser(description='Database migration management for SothemaAI auth service')
    parser.add_argument('command', choices=['current', 'history', 'upgrade', 'downgrade', 'revision'],
                       help='Migration command to run')
    parser.add_argument('--revision', '-r', default='head',
                       help='Revision to upgrade/downgrade to (default: head)')
    parser.add_argument('--message', '-m', default='',
                       help='Message for new revision')

    args = parser.parse_args()

    # Get the service directory
    service_dir = os.path.dirname(os.path.abspath(__file__))

    manager = MigrationManager(service_dir)

    success = False

    if args.command == 'current':
        success = manager.current()
    elif args.command == 'history':
        success = manager.history()
    elif args.command == 'upgrade':
        success = manager.upgrade(args.revision)
    elif args.command == 'downgrade':
        success = manager.downgrade(args.revision)
    elif args.command == 'revision':
        if not args.message:
            logger.error("Message is required for revision command")
            return 1
        success = manager.revision(args.message)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())