"""Command-line interface for CodeVault"""
import argparse
from codevault.vault import CodeVault
def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(
        description="CodeVault - GitHub-like Version Control System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  codevault init Initialize repository
  codevault push src/ -m "Add features" Push with manual message
  codevault push script.py --auto-detect Push with AI-generated message
  codevault log -n 20 Show last 20 commits
  codevault pull abc123 -o ./restored Restore commit to directory
  codevault delete abc123 Delete a commit
  codevault status Show repo status
        """
    )
   
    subparsers = parser.add_subparsers(dest="command", help="Commands")
   
    # Push command
    push_parser = subparsers.add_parser("push", help="Push code changes")
    push_parser.add_argument("files", nargs="+", help="Files or directories to push")
    push_parser.add_argument("-m", "--message", help="Commit message")
    push_parser.add_argument("--auto-detect", action="store_true", help="Use AI to generate commit message")
   
    # Pull command
    pull_parser = subparsers.add_parser("pull", help="Restore code from commit")
    pull_parser.add_argument("commit_id", help="Commit ID to restore")
    pull_parser.add_argument("-o", "--output", default=".", help="Output directory")
   
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a commit")
    delete_parser.add_argument("commit_id", help="Commit ID to delete")
   
    # Log command
    log_parser = subparsers.add_parser("log", help="Show commit history")
    log_parser.add_argument("-n", "--limit", type=int, default=10, help="Number of commits to show")
   
    # Status command
    subparsers.add_parser("status", help="Show repository status")

    # Auth command
    auth_parser = subparsers.add_parser("auth", help="Authentication settings")
    auth_sub = auth_parser.add_subparsers(dest="auth_command")
    auth_set = auth_sub.add_parser("set", help="Set GROQ API key")
    auth_set.add_argument("api_key", help="GROQ API key")

    # Changelog command
    changelog_parser = subparsers.add_parser("changelog", help="Generate changelog")
    changelog_parser.add_argument("-n", "--limit", type=int, default=100, help="Max commits to include")

    # Insight command
    insight_parser = subparsers.add_parser("insight", help="Show commit insight")
    insight_parser.add_argument("commit_id", help="Commit ID to inspect")
   
    # Init command
    subparsers.add_parser("init", help="Initialize repository")
   
    args = parser.parse_args()
   
    vault = CodeVault()
   
    if args.command == "push":
        result = vault.push(args.files, args.message, args.auto_detect)
    elif args.command == "pull":
        result = vault.pull(args.commit_id, args.output)
    elif args.command == "delete":
        result = vault.delete(args.commit_id)
    elif args.command == "log":
        result = vault.log(args.limit)
    elif args.command == "status":
        result = vault.status()
    elif args.command == "init":
        result = "✓ Repository initialized at .codevault/"
    elif args.command == "auth":
        if args.auth_command == "set":
            result = vault.set_api_key(args.api_key)
        else:
            result = "Use: codevault auth set <api-key>"
    elif args.command == "changelog":
        result = vault.changelog(args.limit)
    elif args.command == "insight":
        result = vault.insight(args.commit_id)
    else:
        parser.print_help()
        return
   
    print(result)
if __name__ == "__main__":
    main()