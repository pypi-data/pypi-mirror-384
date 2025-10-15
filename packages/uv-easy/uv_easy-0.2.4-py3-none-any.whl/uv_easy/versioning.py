"""
버전 관리 및 Git 태그 관련 기능
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

import click
import toml


def get_pyproject_path() -> Path:
    """pyproject.toml 파일의 경로를 반환합니다."""
    current_dir = Path.cwd()
    pyproject_path = current_dir / "pyproject.toml"
    
    if not pyproject_path.exists():
        click.echo("[ERROR] pyproject.toml 파일을 찾을 수 없습니다.", err=True)
        sys.exit(1)
    
    return pyproject_path


def read_version() -> str:
    """pyproject.toml에서 현재 버전을 읽어옵니다."""
    pyproject_path = get_pyproject_path()
    
    try:
        with open(pyproject_path, 'r', encoding='utf-8') as f:
            data = toml.load(f)
            return data['project']['version']
    except Exception as e:
        click.echo(f"[ERROR] 버전을 읽는 중 오류가 발생했습니다: {e}", err=True)
        sys.exit(1)


def write_version(version: str) -> None:
    """pyproject.toml에 새로운 버전을 씁니다."""
    pyproject_path = get_pyproject_path()
    
    try:
        with open(pyproject_path, 'r', encoding='utf-8') as f:
            data = toml.load(f)
        
        data['project']['version'] = version
        
        with open(pyproject_path, 'w', encoding='utf-8') as f:
            toml.dump(data, f)
            
        click.echo(f"[OK] 버전이 {version}으로 업데이트되었습니다.")
    except Exception as e:
        click.echo(f"[ERROR] 버전을 쓰는 중 오류가 발생했습니다: {e}", err=True)
        sys.exit(1)


def parse_version(version: str) -> Tuple[int, int, int]:
    """버전 문자열을 파싱하여 (major, minor, patch) 튜플을 반환합니다."""
    try:
        parts = version.split('.')
        if len(parts) != 3:
            raise ValueError("버전 형식이 올바르지 않습니다. (예: 1.2.3)")
        
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError as e:
        click.echo(f"[ERROR] 버전 파싱 오류: {e}", err=True)
        sys.exit(1)


def increment_version(version: str, increment_type: str) -> str:
    """버전을 증가시킵니다."""
    major, minor, patch = parse_version(version)
    
    if increment_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif increment_type == "minor":
        minor += 1
        patch = 0
    elif increment_type == "patch":
        patch += 1
    else:
        click.echo(f"[ERROR] 잘못된 증가 타입: {increment_type}", err=True)
        sys.exit(1)
    
    return f"{major}.{minor}.{patch}"


def run_command(command: str, check: bool = True) -> subprocess.CompletedProcess:
    """명령어를 실행합니다."""
    try:
        result = subprocess.run(
            command.split(),
            check=check,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            shell=False
        )
        return result
    except subprocess.CalledProcessError as e:
        click.echo(f"[ERROR] 명령어 실행 실패: {e}", err=True)
        if e.stdout:
            click.echo(f"stdout: {e.stdout}", err=True)
        if e.stderr:
            click.echo(f"stderr: {e.stderr}", err=True)
        sys.exit(1)


def get_current_branch() -> str:
    """현재 Git 브랜치 이름을 반환합니다."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            # fallback: 기본 브랜치 확인
            result = subprocess.run(
                ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                # refs/remotes/origin/main -> main
                return result.stdout.strip().split('/')[-1]
            else:
                # 최종 fallback
                return "main"
                
    except Exception:
        return "main"


def create_git_tag(version: str, push: bool = True) -> None:
    """Git 태그를 생성하고 푸시합니다."""
    tag_name = f"v{version}"
    
    # Git 태그 생성
    click.echo(f"[TAG] Git 태그 '{tag_name}' 생성 중...")
    result = run_command(f"git tag {tag_name}")
    
    if push:
        # 현재 브랜치 확인
        current_branch = get_current_branch()
        click.echo(f"[PUSH] Git 태그 '{tag_name}' 푸시 중... (브랜치: {current_branch})")
        run_command(f"git push origin {current_branch} --tags")
        click.echo(f"[OK] Git 태그 '{tag_name}' 생성 및 푸시 완료")
    else:
        click.echo(f"[OK] Git 태그 '{tag_name}' 생성 완료 (푸시 안함)")


def analyze_git_commits() -> str:
    """Git 커밋 로그를 분석하여 버전 증가 타입을 결정합니다."""
    try:
        # 최근 커밋들 가져오기
        result = subprocess.run(
            ["git", "log", "--oneline", "-10"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode != 0:
            click.echo("[WARNING] Git 로그를 읽을 수 없습니다. patch 버전으로 증가합니다.")
            return "patch"
        
        commits = result.stdout.strip().split('\n')
        
        # 커밋 메시지 분석
        has_breaking_change = False
        has_feat = False
        has_fix = False
        
        for commit in commits:
            commit_msg = commit.lower()
            if 'breaking change' in commit_msg or '!' in commit_msg:
                has_breaking_change = True
            elif commit_msg.startswith('feat'):
                has_feat = True
            elif commit_msg.startswith('fix'):
                has_fix = True
        
        # 버전 증가 타입 결정
        if has_breaking_change:
            return "major"
        elif has_feat:
            return "minor"
        elif has_fix:
            return "patch"
        else:
            return "patch"
            
    except Exception as e:
        click.echo(f"[WARNING] 커밋 분석 중 오류: {e}. patch 버전으로 증가합니다.")
        return "patch"
