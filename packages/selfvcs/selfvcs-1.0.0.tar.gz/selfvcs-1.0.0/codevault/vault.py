#!/usr/bin/env python3
"""
CodeVault - A GitHub-like version control system with AI-powered auto-updates
"""
import json
import shutil
import hashlib
import difflib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import os
try:
    from groq import Groq # type: ignore
except ImportError:
    Groq = None

class CodeVault:
    """Main version control system"""
   
    def __init__(self, repo_path: str = ".codevault"):
        self.repo_path = Path(repo_path)
        self.repo_path.mkdir(exist_ok=True)
        self.commits_dir = self.repo_path / "commits"
        self.refs_dir = self.repo_path / "refs"
        self.metadata_file = self.repo_path / "metadata.json"
        self.index_file = self.repo_path / "index.json"
        # User config file (per machine)
        self.user_config_path = Path.home() / ".codevault" / "config.json"
       
        self.commits_dir.mkdir(exist_ok=True)
        self.refs_dir.mkdir(exist_ok=True)
       
        if not self.metadata_file.exists():
            self._init_metadata()
        self._ensure_user_config()
   
    def _init_metadata(self):
        """Initialize repository metadata"""
        metadata = {
            "created_at": datetime.now().isoformat(),
            "commits": [],
            "current_branch": "main",
            "auto_update_enabled": False,
            "version": "0.1.0",
            "tags": []
        }
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _ensure_user_config(self):
        """Ensure user config exists for storing credentials/settings."""
        cfg_dir = self.user_config_path.parent
        cfg_dir.mkdir(parents=True, exist_ok=True)
        if not self.user_config_path.exists():
            with open(self.user_config_path, 'w') as f:
                json.dump({"groq_api_key": ""}, f, indent=2)
   
    def _load_metadata(self) -> dict:
        """Load metadata, reinitializing if invalid or empty"""
        try:
            if not self.metadata_file.exists():
                raise FileNotFoundError("Metadata file not found")
            with open(self.metadata_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    raise ValueError("Empty metadata file")
                return json.loads(content)
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
            print(f"Warning: {e}. Reinitializing metadata...")
            self._init_metadata()
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
   
    def _save_metadata(self, metadata: dict):
        """Save metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _load_user_config(self) -> dict:
        """Load user config from home directory."""
        try:
            if not self.user_config_path.exists():
                self._ensure_user_config()
            with open(self.user_config_path, 'r') as f:
                content = f.read().strip()
                return json.loads(content) if content else {"groq_api_key": ""}
        except Exception:
            return {"groq_api_key": ""}

    def set_api_key(self, api_key: str) -> str:
        """Persist GROQ API key in user config."""
        cfg = self._load_user_config()
        cfg["groq_api_key"] = api_key.strip()
        self.user_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.user_config_path, 'w') as f:
            json.dump(cfg, f, indent=2)
        return "✓ GROQ API key saved to user config"
   
    def _get_file_hash(self, filepath: str) -> str:
        """Generate SHA-1 hash of file content"""
        sha1 = hashlib.sha1()
        with open(filepath, 'rb') as f:
            sha1.update(f.read())
        return sha1.hexdigest()[:8]
   
    def _detect_code_changes(self, filepath: str, prev_content: Optional[str] = None) -> str:
        """Detect what changed in the code"""
        with open(filepath, 'r', errors='ignore') as f:
            current_content = f.read()
       
        if prev_content is None:
            return "new file created"
       
        if prev_content == current_content:
            return "no changes"
       
        prev_lines = prev_content.splitlines()
        curr_lines = current_content.splitlines()
       
        diff = list(difflib.unified_diff(prev_lines, curr_lines, lineterm=''))
        summary = []
        added = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        removed = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
       
        if added > 0:
            summary.append(f"{added} lines added")
        if removed > 0:
            summary.append(f"{removed} lines removed")
       
        return ", ".join(summary) if summary else "modified"
   
    def _get_api_key(self) -> Optional[str]:
        """Resolve GROQ API key from env or user config."""
        api_key = os.getenv("GROQ_API_KEY") or os.getenv("CODEVAULT_GROQ_KEY")
        if api_key:
            return api_key
        cfg = self._load_user_config()
        return cfg.get("groq_api_key") or None

    def _generate_ai_commit_message(self, file_info: str, changes: str, content: str) -> Optional[str]:
        """Generate commit message using Groq API"""
        if Groq is None:
            return None
       
        api_key = self._get_api_key()
        if not api_key:
            print("GROQ_API_KEY not set; skipping AI generation")
            return None
       
        try:
            client = Groq(api_key=api_key)
            # Show only first 2000 chars to avoid token limit
            code_snippet = content[:2000]
           
            response = client.chat.completions.create(
                model="llama3-8b-8192",  # Fast model for commit messages
                messages=[{
                    "role": "user",
                    "content": f"""Analyze this code change and generate a concise, professional git commit message (one line, max 72 chars).
File(s): {file_info}
Changes: {changes}
Code snippet:
{code_snippet}
Return ONLY the commit message, nothing else."""
                }],
                max_tokens=150,
                temperature=0.1  # Low temp for consistent, professional output
            )
           
            commit_msg = response.choices[0].message.content.strip()
            return commit_msg[:72]  # Ensure max 72 chars
        except Exception as e:
            print(f"Groq generation failed: {e}")
            return None

    def _ai_analyze_change(self, changes_summary: str, code_snippet: str) -> Tuple[str, str, List[str]]:
        """Use AI to classify semantic type, risk level, and impacted areas.

        Returns: (semantic_type, risk_level, impacted_entities)
        """
        semantic_type = "chore"
        risk_level = "low"
        impacted: List[str] = []
        if Groq is None:
            return semantic_type, risk_level, impacted
        api_key = self._get_api_key()
        if not api_key:
            return semantic_type, risk_level, impacted
        try:
            client = Groq(api_key=api_key)
            resp = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{
                    "role": "user",
                    "content": (
                        "You are a code review assistant. Given a description of code changes and a snippet, "
                        "return a concise JSON object with fields: type (one of feat, fix, refactor, docs, test, chore), "
                        "risk (one of low, medium, high), impacted (array of function/module names). "
                        "Only return JSON.\n\n"
                        f"Changes: {changes_summary}\nSnippet:\n{code_snippet[:2000]}"
                    )
                }],
                max_tokens=200,
                temperature=0.1
            )
            content = resp.choices[0].message.content.strip()
            data = json.loads(content)
            semantic_type = str(data.get("type", semantic_type))
            risk_level = str(data.get("risk", risk_level))
            impacted_list = data.get("impacted", [])
            if isinstance(impacted_list, list):
                impacted = [str(x) for x in impacted_list][:20]
            return semantic_type, risk_level, impacted
        except Exception:
            return semantic_type, risk_level, impacted

    def _bump_version(self, current: str, semantic_type: str) -> Tuple[str, str]:
        """Return (new_version, bump_type) based on semantic type."""
        major, minor, patch = [int(x) for x in current.split('.')]
        bump = "patch"
        if semantic_type == "feat":
            minor += 1
            patch = 0
            bump = "minor"
        elif semantic_type == "fix":
            patch += 1
            bump = "patch"
        elif semantic_type == "refactor":
            patch += 1
            bump = "patch"
        else:
            patch += 1
            bump = "patch"
        return f"{major}.{minor}.{patch}", bump
   
    def push(self, file_patterns: List[str], message: Optional[str] = None, auto_detect: bool = False) -> str:
        """Push code changes to repository"""
       
        files_to_push = []
        for pattern in file_patterns:
            if os.path.isfile(pattern):
                files_to_push.append(pattern)
            elif os.path.isdir(pattern):
                for root, _, files in os.walk(pattern):
                    for file in files:
                        full_path = os.path.join(root, file)
                        if not any(exclude in root for exclude in ['.codevault', '__pycache__', '.git']):
                            files_to_push.append(full_path)
       
        if not files_to_push:
            return "No files found to push"
       
        metadata = self._load_metadata()
        timestamp = datetime.now().isoformat()
        commit_id = self._get_file_hash(files_to_push[0]) + datetime.now().strftime("%H%M%S")
        commit_dir = self.commits_dir / commit_id
        commit_dir.mkdir(exist_ok=True)
       
        commit_data = {
            "id": commit_id,
            "timestamp": timestamp,
            "files": [],
            "message": message or "Auto-commit",
            "insight": {
                "semantic_type": "chore",
                "risk": "low",
                "impacted": []
            },
            "tags": []
        }
       
        # Get previous contents from last commit
        prev_contents = {}
        if metadata["commits"]:
            last_id = metadata["commits"][-1]
            last_dir = self.commits_dir / last_id
            if last_dir.exists():
                with open(last_dir / "commit.json", 'r') as f:
                    last_data = json.load(f)
                for f_info in last_data["files"]:
                    snap_name = Path(f_info["name"]).as_posix().replace('/', '_')
                    snap_path = last_dir / f"{snap_name}.snapshot"
                    if snap_path.exists():
                        with open(snap_path, 'r', errors='ignore') as ff:
                            prev_contents[f_info["name"]] = ff.read()
       
        for filepath in files_to_push:
            try:
                with open(filepath, 'r', errors='ignore') as f:
                    content = f.read()
               
                prev_content = prev_contents.get(filepath)
                changes = self._detect_code_changes(filepath, prev_content)
               
                file_hash = self._get_file_hash(filepath)
               
                # Store file content
                file_data = {
                    "name": filepath,
                    "hash": file_hash,
                    "changes": changes,
                    "size": len(content)
                }
                commit_data["files"].append(file_data)
               
                # Snapshot with safe name
                snap_name = Path(filepath).as_posix().replace('/', '_')
                file_path = commit_dir / f"{snap_name}.snapshot"
                with open(file_path, 'w') as f:
                    f.write(content)
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
                continue
       
        # Generate AI message and insights if needed (after all files)
        if auto_detect and not message and commit_data["files"]:
            changes_summary = "; ".join([f"{fd['name']}: {fd['changes']}" for fd in commit_data["files"]])
            # Snippet from first file
            first_snap_name = Path(commit_data["files"][0]["name"]).as_posix().replace('/', '_')
            first_snap = commit_dir / f"{first_snap_name}.snapshot"
            if first_snap.exists():
                with open(first_snap, 'r', errors='ignore') as f:
                    code_snippet = f.read()[:2000]
            else:
                code_snippet = ""
            ai_msg = self._generate_ai_commit_message(
                f"{len(commit_data['files'])} files", changes_summary, code_snippet
            )
            if ai_msg:
                commit_data["message"] = ai_msg
            # AI insights
            sem_type, risk, impacted = self._ai_analyze_change(changes_summary, code_snippet)
            commit_data["insight"] = {
                "semantic_type": sem_type,
                "risk": risk,
                "impacted": impacted
            }
        else:
            # Even without auto-detect, compute a lightweight impacted list via heuristics
            impacted_heur: List[str] = []
            for fobj in commit_data["files"]:
                impacted_heur.append(Path(fobj["name"]).name)
            commit_data["insight"]["impacted"] = impacted_heur[:20]
       
        # Save commit metadata
        with open(commit_dir / "commit.json", 'w') as f:
            json.dump(commit_data, f, indent=2)
       
        # Update metadata
        metadata["commits"].append(commit_id)

        # Auto tag and version bump based on semantic type
        sem_type = commit_data["insight"].get("semantic_type", "chore")
        new_version, bump_type = self._bump_version(metadata.get("version", "0.1.0"), sem_type)
        if new_version != metadata.get("version"):
            metadata["version"] = new_version
            tag = {
                "commit": commit_id,
                "version": new_version,
                "bump": bump_type,
                "date": timestamp
            }
            metadata.setdefault("tags", []).append(tag)
        self._save_metadata(metadata)
       
        return (
            f"✓ Committed {len(commit_data['files'])} file(s) with ID: {commit_id}\n"
            f" Message: {commit_data['message']}\n"
            f" Type: {commit_data['insight'].get('semantic_type','chore')} | Risk: {commit_data['insight'].get('risk','low')} | Version: {metadata.get('version')}"
        )
   
    def pull(self, commit_id: str, extract_to: str = ".") -> str:
        """Pull/restore code from a commit"""
        commit_dir = self.commits_dir / commit_id
       
        if not commit_dir.exists():
            return f"Commit {commit_id} not found"
       
        with open(commit_dir / "commit.json", 'r') as f:
            commit_data = json.load(f)
       
        restored_count = 0
        for file_info in commit_data["files"]:
            original_path = file_info["name"]
            snap_name = Path(original_path).as_posix().replace('/', '_')
            snapshot_path = commit_dir / f"{snap_name}.snapshot"
           
            target_path = Path(extract_to) / original_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
           
            if snapshot_path.exists():
                shutil.copy(snapshot_path, target_path)
                restored_count += 1
       
        return f"✓ Restored {restored_count} file(s) from commit {commit_id}"
   
    def delete(self, commit_id: str) -> str:
        """Delete a commit"""
        commit_dir = self.commits_dir / commit_id
       
        if not commit_dir.exists():
            return f"Commit {commit_id} not found"
       
        shutil.rmtree(commit_dir)
       
        # Update metadata
        metadata = self._load_metadata()
        if commit_id in metadata["commits"]:
            metadata["commits"].remove(commit_id)
            self._save_metadata(metadata)
       
        return f"✓ Deleted commit {commit_id}"
   
    def log(self, limit: int = 10) -> str:
        """Display commit history"""
        metadata = self._load_metadata()
       
        commits = metadata["commits"][-limit:][::-1]  # Newest first
       
        if not commits:
            return "No commits found"
       
        output = "Commit History:\n" + "=" * 60 + "\n"
       
        for commit_id in commits:
            commit_dir = self.commits_dir / commit_id
            try:
                with open(commit_dir / "commit.json", 'r') as f:
                    commit_data = json.load(f)
               
                output += f"\nID: {commit_id}\n"
                output += f"Date: {commit_data['timestamp']}\n"
                output += f"Message: {commit_data['message']}\n"
                output += f"Files: {len(commit_data['files'])}\n"
                ins = commit_data.get("insight", {})
                if ins:
                    output += f"Type: {ins.get('semantic_type','')} | Risk: {ins.get('risk','')}\n"
                output += "-" * 60 + "\n"
            except Exception as e:
                output += f"Error reading commit {commit_id}: {e}\n"
       
        return output
   
    def status(self) -> str:
        """Show repository status"""
        metadata = self._load_metadata()
       
        status = f"""CodeVault Repository Status
{'=' * 40}
Created: {metadata['created_at']}
Total Commits: {len(metadata['commits'])}
Current Branch: {metadata['current_branch']}
Auto-update Enabled: {metadata['auto_update_enabled']}
Version: {metadata.get('version','0.1.0')}
"""
        return status

    def changelog(self, limit: int = 100) -> str:
        """Generate a simple changelog from commit history."""
        metadata = self._load_metadata()
        commits = metadata.get("commits", [])[-limit:][::-1]
        if not commits:
            return "No commits found"
        lines = ["# Changelog", ""]
        # Include latest version if exists
        latest_version = metadata.get("version")
        if latest_version:
            lines.append(f"## v{latest_version}")
            lines.append("")
        for cid in commits:
            cdir = self.commits_dir / cid
            try:
                with open(cdir / "commit.json", 'r') as f:
                    cdata = json.load(f)
                t = cdata.get("timestamp", "")
                msg = cdata.get("message", "")
                ins = cdata.get("insight", {})
                typ = ins.get("semantic_type", "")
                lines.append(f"- [{typ}] {msg} ({cid}) - {t}")
            except Exception:
                continue
        return "\n".join(lines)

    def insight(self, commit_id: str) -> str:
        """Show AI/heuristic insights for a commit."""
        cdir = self.commits_dir / commit_id
        if not cdir.exists():
            return f"Commit {commit_id} not found"
        try:
            with open(cdir / "commit.json", 'r') as f:
                cdata = json.load(f)
            ins = cdata.get("insight", {})
            lines = [
                f"Commit: {commit_id}",
                f"Message: {cdata.get('message','')}",
                f"Type: {ins.get('semantic_type','chore')}",
                f"Risk: {ins.get('risk','low')}",
                f"Impacted: {', '.join(ins.get('impacted', [])) if ins.get('impacted') else 'n/a'}"
            ]
            return "\n".join(lines)
        except Exception as e:
            return f"Error reading commit {commit_id}: {e}"

# Standalone main for testing (optional)
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CodeVault - Version Control System")
    # ... (omitted for brevity; use cli.py for full CLI)