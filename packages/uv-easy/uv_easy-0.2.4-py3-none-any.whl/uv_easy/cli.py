"""
uv_easy CLI 진입점
"""

import click

from .versioning import (
    read_version, write_version, increment_version, 
    create_git_tag, analyze_git_commits
)
from .builder import clean_build_artifacts, build_package, install_package
from .publisher import publish_to_pypi
from .changelog import generate_changelog
from .workflow import generate_github_workflow, generate_git_cliff_config


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
@click.option('--auto', is_flag=True, help='Git 커밋을 분석하여 자동으로 버전을 증가시킵니다')
@click.option('--no-push', is_flag=True, help='Git 태그를 푸시하지 않습니다')
def up(major: bool, minor: bool, patch: bool, auto: bool, no_push: bool):
    """pyproject.toml의 버전을 증가시키고 Git 태그를 생성합니다."""
    # 옵션 확인
    manual_options = [major, minor, patch]
    if auto and sum(manual_options) > 0:
        click.echo("❌ --auto 옵션과 다른 버전 옵션을 함께 사용할 수 없습니다.", err=True)
        return
    
    if not auto and sum(manual_options) != 1:
        click.echo("❌ --major, --minor, --patch 중 하나만 선택하거나 --auto를 사용하세요.", err=True)
        return
    
    # 현재 버전 읽기
    current_version = read_version()
    click.echo(f"현재 버전: {current_version}")
    
    # 증가 타입 결정
    if auto:
        increment_type = analyze_git_commits()
        click.echo(f"커밋 분석 결과: {increment_type} 버전 증가")
    elif major:
        increment_type = "major"
    elif minor:
        increment_type = "minor"
    else:  # patch
        increment_type = "patch"
    
    # 새 버전 계산
    new_version = increment_version(current_version, increment_type)
    
    # 버전 업데이트
    write_version(new_version)
    
    # Git 태그 생성 및 푸시
    create_git_tag(new_version, push=not no_push)


@version.command()
def show():
    """현재 버전을 표시합니다."""
    current_version = read_version()
    click.echo(f"현재 버전: {current_version}")


@cli.command()
@click.option('--tag', help='특정 태그에 대한 changelog 생성')
@click.option('--output', '-o', default='CHANGELOG.md', help='출력 파일명')
def changelog(tag: str, output: str):
    """git-cliff를 사용하여 changelog를 생성합니다."""
    generate_changelog(tag=tag, output_file=output)


@cli.command()
@click.option('--no-version-up', is_flag=True, help='버전을 증가시키지 않습니다')
@click.option('--major', is_flag=True, help='메이저 버전을 증가시킵니다')
@click.option('--minor', is_flag=True, help='마이너 버전을 증가시킵니다')
@click.option('--patch', is_flag=True, help='패치 버전을 증가시킵니다')
@click.option('--auto', is_flag=True, help='Git 커밋을 분석하여 자동으로 버전을 증가시킵니다')
@click.option('--install', is_flag=True, help='빌드 후 현재 환경에 설치합니다')
@click.option('--no-push', is_flag=True, help='Git 태그를 푸시하지 않습니다')
def build(no_version_up: bool, major: bool, minor: bool, patch: bool, 
          auto: bool, install: bool, no_push: bool):
    """패키지를 빌드합니다."""
    # 버전 증가 옵션 확인
    version_options = [major, minor, patch]
    if not no_version_up and not auto and sum(version_options) != 1:
        click.echo("❌ --major, --minor, --patch 중 하나만 선택하거나 --auto를 사용하거나 --no-version-up을 사용하세요.", err=True)
        return
    
    # 1. 빌드 정리
    clean_build_artifacts()
    
    # 2. 버전 증가 (옵션에 따라)
    if not no_version_up:
        current_version = read_version()
        click.echo(f"현재 버전: {current_version}")
        
        if auto:
            increment_type = analyze_git_commits()
            click.echo(f"커밋 분석 결과: {increment_type} 버전 증가")
        elif major:
            increment_type = "major"
        elif minor:
            increment_type = "minor"
        else:  # patch
            increment_type = "patch"
        
        new_version = increment_version(current_version, increment_type)
        write_version(new_version)
        
        # Git 태그 생성 및 푸시
        create_git_tag(new_version, push=not no_push)
    
    # 3. 빌드 실행
    build_package()
    
    # 4. 설치 (옵션에 따라)
    if install:
        install_package()


@cli.command()
@click.option('--test', is_flag=True, help='TestPyPI에 업로드합니다')
@click.option('--json', 'json_output', is_flag=True, help='JSON 형태로 결과를 출력합니다')
def publish(test: bool, json_output: bool):
    """dist 디렉토리의 패키지를 PyPI 또는 TestPyPI에 업로드합니다."""
    publish_to_pypi(test=test, json_output=json_output)


@cli.group()
def init():
    """초기화 명령어"""
    pass


@init.command()
@click.option('--test', is_flag=True, help='TestPyPI용 workflow 생성')
@click.option('--release', is_flag=True, help='GitHub Release 자동화 포함')
def workflow(test: bool, release: bool):
    """GitHub Actions workflow 파일을 생성합니다."""
    generate_github_workflow(test=test, release=release)


@init.command()
def cliff_config():
    """git-cliff 설정 파일을 생성합니다."""
    generate_git_cliff_config()


@cli.command()
def ready_pypi():
    """pyproject.toml에 PyPI 배포를 위한 project.urls를 추가합니다."""
    from .versioning import get_pyproject_path
    import toml
    
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
