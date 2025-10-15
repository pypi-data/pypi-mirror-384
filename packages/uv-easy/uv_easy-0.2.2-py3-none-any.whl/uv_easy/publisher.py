"""
PyPI/TestPyPI 업로드 관련 기능
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import click

from .versioning import read_version


def publish_to_pypi(test: bool = False, json_output: bool = False) -> dict:
    """PyPI 또는 TestPyPI에 패키지를 업로드합니다."""
    repository = "testpypi" if test else "pypi"
    
    # dist 디렉토리 확인
    dist_dir = Path("dist")
    if not dist_dir.exists():
        click.echo("[ERROR] dist 디렉토리를 찾을 수 없습니다. 먼저 빌드를 실행하세요.", err=True)
        sys.exit(1)
    
    # dist 디렉토리에 파일이 있는지 확인
    dist_files = list(dist_dir.glob("*"))
    if not dist_files:
        click.echo("[ERROR] dist 디렉토리가 비어있습니다. 먼저 빌드를 실행하세요.", err=True)
        sys.exit(1)
    
    click.echo(f"[UPLOAD] {repository.upper()}에 패키지를 업로드합니다...")
    click.echo("업로드할 파일들:")
    for file in dist_files:
        click.echo(f"  - {file.name}")
    
    # Windows에서 UTF-8 환경 변수 설정
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONLEGACYWINDOWSSTDIO'] = '1'
    
    # twine upload 명령어 구성
    upload_cmd = ["twine", "upload", "dist/*"]
    if test:
        upload_cmd.extend(["--repository", "testpypi"])
    
    # twine upload 실행
    try:
        result = subprocess.run(
            upload_cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env
        )
        
        if result.stdout:
            click.echo(result.stdout)
        
        click.echo(f"[OK] {repository.upper()} 업로드가 완료되었습니다!")
        
        # 결과 정보 수집
        current_version = read_version()
        artifacts = [str(f) for f in dist_files]
        
        result_data = {
            "version": current_version,
            "repository": repository,
            "artifacts": artifacts
        }
        
        # JSON 출력이 요청된 경우
        if json_output:
            print(json.dumps(result_data, indent=2))
        
        return result_data
        
    except subprocess.CalledProcessError as e:
        click.echo(f"[ERROR] {repository.upper()} 업로드 실패:", err=True)
        if e.stdout:
            click.echo(f"stdout: {e.stdout}", err=True)
        if e.stderr:
            click.echo(f"stderr: {e.stderr}", err=True)
        sys.exit(1)
