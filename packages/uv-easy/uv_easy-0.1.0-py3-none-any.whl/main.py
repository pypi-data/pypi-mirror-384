#!/usr/bin/env python3
"""
uv_easy - uv를 더 쉽게 사용하기 위한 도구
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
        click.echo("❌ pyproject.toml 파일을 찾을 수 없습니다.", err=True)
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
        click.echo(f"❌ 버전을 읽는 중 오류가 발생했습니다: {e}", err=True)
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
            
        click.echo(f"✅ 버전이 {version}으로 업데이트되었습니다.")
    except Exception as e:
        click.echo(f"❌ 버전을 쓰는 중 오류가 발생했습니다: {e}", err=True)
        sys.exit(1)


def parse_version(version: str) -> Tuple[int, int, int]:
    """버전 문자열을 파싱하여 (major, minor, patch) 튜플을 반환합니다."""
    try:
        parts = version.split('.')
        if len(parts) != 3:
            raise ValueError("버전 형식이 올바르지 않습니다. (예: 1.2.3)")
        
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError as e:
        click.echo(f"❌ 버전 파싱 오류: {e}", err=True)
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
        click.echo(f"❌ 잘못된 증가 타입: {increment_type}", err=True)
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
            shell=False
        )
        return result
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ 명령어 실행 실패: {e}", err=True)
        if e.stdout:
            click.echo(f"stdout: {e.stdout}", err=True)
        if e.stderr:
            click.echo(f"stderr: {e.stderr}", err=True)
        sys.exit(1)


@click.group()
def cli():
    """uv를 더 쉽게 사용하기 위한 도구"""
    pass


@cli.group()
def version():
    """버전 관리 명령어"""
    pass


@version.command()
@click.option('--major', is_flag=True, help='메이저 버전을 증가시킵니다')
@click.option('--minor', is_flag=True, help='마이너 버전을 증가시킵니다')
@click.option('--patch', is_flag=True, help='패치 버전을 증가시킵니다')
def up(major: bool, minor: bool, patch: bool):
    """pyproject.toml의 버전을 증가시킵니다."""
    # 옵션 확인
    options = [major, minor, patch]
    if sum(options) != 1:
        click.echo("❌ --major, --minor, --patch 중 하나만 선택해야 합니다.", err=True)
        sys.exit(1)
    
    # 현재 버전 읽기
    current_version = read_version()
    click.echo(f"현재 버전: {current_version}")
    
    # 증가 타입 결정
    if major:
        increment_type = "major"
    elif minor:
        increment_type = "minor"
    else:  # patch
        increment_type = "patch"
    
    # 새 버전 계산
    new_version = increment_version(current_version, increment_type)
    
    # 버전 업데이트
    write_version(new_version)


@version.command()
def show():
    """현재 버전을 표시합니다."""
    current_version = read_version()
    click.echo(f"현재 버전: {current_version}")


@cli.command()
@click.option('--no-version-up', is_flag=True, help='버전을 증가시키지 않습니다')
@click.option('--major', is_flag=True, help='메이저 버전을 증가시킵니다')
@click.option('--minor', is_flag=True, help='마이너 버전을 증가시킵니다')
@click.option('--patch', is_flag=True, help='패치 버전을 증가시킵니다')
@click.option('--install', is_flag=True, help='빌드 후 현재 환경에 설치합니다')
def build(no_version_up: bool, major: bool, minor: bool, patch: bool, install: bool):
    """패키지를 빌드합니다."""
    # 버전 증가 옵션 확인
    version_options = [major, minor, patch]
    if not no_version_up and sum(version_options) != 1:
        click.echo("❌ --major, --minor, --patch 중 하나만 선택하거나 --no-version-up을 사용하세요.", err=True)
        sys.exit(1)
    
    # 1. 버전 증가 (옵션에 따라)
    if not no_version_up:
        current_version = read_version()
        click.echo(f"현재 버전: {current_version}")
        
        if major:
            increment_type = "major"
        elif minor:
            increment_type = "minor"
        else:  # patch
            increment_type = "patch"
        
        new_version = increment_version(current_version, increment_type)
        write_version(new_version)
    
    # 2. 빌드 실행
    click.echo("🔨 패키지를 빌드합니다...")
    result = run_command("uvx --from build pyproject-build")
    
    if result.stdout:
        click.echo(result.stdout)
    
    click.echo("✅ 빌드가 완료되었습니다.")
    
    # 3. 설치 (옵션에 따라)
    if install:
        click.echo("📦 패키지를 설치합니다...")
        
        # dist 디렉토리에서 wheel 파일 찾기
        dist_dir = Path("dist")
        if not dist_dir.exists():
            click.echo("❌ dist 디렉토리를 찾을 수 없습니다.", err=True)
            sys.exit(1)
        
        wheel_files = list(dist_dir.glob("*.whl"))
        if not wheel_files:
            click.echo("❌ wheel 파일을 찾을 수 없습니다.", err=True)
            sys.exit(1)
        
        # 가장 최근 wheel 파일 사용
        latest_wheel = max(wheel_files, key=lambda x: x.stat().st_mtime)
        
        # uv를 사용하여 설치
        install_result = run_command(f"uv pip install {latest_wheel}")
        
        if install_result.stdout:
            click.echo(install_result.stdout)
        
        click.echo("✅ 설치가 완료되었습니다.")


def main():
    """CLI 진입점"""
    cli()


if __name__ == "__main__":
    main()
