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
            encoding='utf-8',
            errors='replace',
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


@cli.command()
def publish():
    """dist 디렉토리의 패키지를 PyPI에 업로드합니다."""
    # dist 디렉토리 확인
    dist_dir = Path("dist")
    if not dist_dir.exists():
        click.echo("❌ dist 디렉토리를 찾을 수 없습니다. 먼저 빌드를 실행하세요.", err=True)
        sys.exit(1)
    
    # dist 디렉토리에 파일이 있는지 확인
    dist_files = list(dist_dir.glob("*"))
    if not dist_files:
        click.echo("❌ dist 디렉토리가 비어있습니다. 먼저 빌드를 실행하세요.", err=True)
        sys.exit(1)
    
    click.echo("📦 PyPI에 패키지를 업로드합니다...")
    click.echo("업로드할 파일들:")
    for file in dist_files:
        click.echo(f"  - {file.name}")
    
    # Windows에서 UTF-8 환경 변수 설정
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONLEGACYWINDOWSSTDIO'] = '1'
    
    # twine upload 실행
    try:
        result = subprocess.run(
            ["twine", "upload", "dist/*"],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env
        )
        
        if result.stdout:
            click.echo(result.stdout)
        
        click.echo("✅ PyPI 업로드가 완료되었습니다!")
        
    except subprocess.CalledProcessError as e:
        click.echo("❌ PyPI 업로드 실패:", err=True)
        if e.stdout:
            click.echo(f"stdout: {e.stdout}", err=True)
        if e.stderr:
            click.echo(f"stderr: {e.stderr}", err=True)
        sys.exit(1)


@cli.command()
def ready_pypi():
    """pyproject.toml에 PyPI 배포를 위한 project.urls를 추가합니다."""
    pyproject_path = get_pyproject_path()
    
    try:
        # 현재 pyproject.toml 읽기
        with open(pyproject_path, 'r', encoding='utf-8') as f:
            data = toml.load(f)
        
        # project.urls가 이미 있는지 확인
        if 'urls' in data.get('project', {}):
            click.echo("⚠️  project.urls가 이미 존재합니다.")
            click.echo("현재 URLs:")
            for key, value in data['project']['urls'].items():
                click.echo(f"  {key}: {value}")
            
            if not click.confirm("기존 URLs를 덮어쓰시겠습니까?"):
                click.echo("작업이 취소되었습니다.")
                return
        
        # 기본 URLs 추가
        project_name = data['project']['name']
        default_urls = {
            "Homepage": f"https://github.com/hakunamta00700/{project_name}",
            "Repository": f"https://github.com/hakunamta00700/{project_name}",
            "Issues": f"https://github.com/hakunamta00700/{project_name}/issues",
            "Documentation": f"https://github.com/hakunamta00700/{project_name}#readme"
        }
        
        # project.urls 추가
        if 'project' not in data:
            data['project'] = {}
        
        data['project']['urls'] = default_urls
        
        # 파일에 쓰기
        with open(pyproject_path, 'w', encoding='utf-8') as f:
            toml.dump(data, f)
        
        click.echo("✅ PyPI 배포를 위한 URLs가 추가되었습니다:")
        for key, value in default_urls.items():
            click.echo(f"  {key}: {value}")
        
        click.echo("\n💡 다음 단계:")
        click.echo("1. GitHub 저장소가 생성되었는지 확인하세요")
        click.echo("2. uv_easy build로 패키지를 빌드하세요")
        click.echo("3. uv_easy publish로 PyPI에 업로드하세요")
        
    except Exception as e:
        click.echo(f"❌ URLs 추가 중 오류가 발생했습니다: {e}", err=True)
        sys.exit(1)


def main():
    """CLI 진입점"""
    cli()


if __name__ == "__main__":
    main()
