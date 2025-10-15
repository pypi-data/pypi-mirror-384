"""
GitHub Actions Workflow 생성 관련 기능
"""

import sys
from pathlib import Path

import click


def generate_github_workflow(test: bool = False, release: bool = False) -> None:
    """GitHub Actions workflow 파일을 생성합니다."""
    
    workflow_dir = Path(".github/workflows")
    workflow_dir.mkdir(parents=True, exist_ok=True)
    
    workflow_file = workflow_dir / "publish.yml"
    
    # 기본 workflow 템플릿
    workflow_content = f"""name: Publish to {'TestPyPI' if test else 'PyPI'}
on:
  push:
    tags:
      - "v*"

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install uv
        uses: astral-sh/uv-action@v1
        with:
          version: "latest"
      
      - name: Install dependencies
        run: uv sync
      
      - name: Build package
        run: uv_easy build --no-version-up
      
      - name: Publish to {'TestPyPI' if test else 'PyPI'}
        run: uv_easy publish {'--test' if test else ''} --json
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{{{ secrets.{'TESTPYPI_API_TOKEN' if test else 'PYPI_API_TOKEN'} }}}}"""

    # Release 옵션이 활성화된 경우 추가 단계
    if release:
        workflow_content += f"""

      - name: Generate Changelog
        run: uv_easy changelog --tag v${{{{ steps.publish.outputs.version }}}}

      - name: Create GitHub Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
        with:
          tag_name: v${{{{ steps.publish.outputs.version }}}}
          release_name: Release v${{{{ steps.publish.outputs.version }}}}
          body_path: CHANGELOG.md
          draft: false
          prerelease: {'true' if test else 'false'}"""

    # workflow 파일 작성
    try:
        with open(workflow_file, 'w', encoding='utf-8') as f:
            f.write(workflow_content)
        
        click.echo(f"[OK] GitHub Actions workflow가 생성되었습니다: {workflow_file}")
        click.echo("\n다음 단계:")
        
        if test:
            click.echo("1. GitHub 저장소에 TESTPYPI_API_TOKEN 시크릿을 추가하세요")
            click.echo("2. git tag v0.1.0 && git push origin main --tags로 테스트하세요")
        else:
            click.echo("1. GitHub 저장소에 PYPI_API_TOKEN 시크릿을 추가하세요")
            click.echo("2. git tag v0.1.0 && git push origin main --tags로 배포하세요")
        
        if release:
            click.echo("3. 자동으로 GitHub Release가 생성됩니다")
        
    except Exception as e:
        click.echo(f"❌ Workflow 생성 중 오류: {e}", err=True)
        sys.exit(1)


def generate_git_cliff_config() -> None:
    """git-cliff 설정 파일을 생성합니다."""
    config_content = '''[changelog]
header = "## Changelog"
body = """
    ## [{{ version }}] - {{ timestamp | date(format="%Y-%m-%d") }}
    {% for group, commits in commits | group_by(attribute="group") %}
    ### {{ group | upper_first }}
    {% for commit in commits %}
    - {{ commit.message | upper_first }} ({{ commit.id | truncate(length=8, end="") }})
    {% endfor %}
    {% endfor %}
"""
footer = ""

[git]
conventional_commits = true
filter_unconventional = true
split_commits = true
commit_parsers = [
    { message = "^feat", group = "Features" },
    { message = "^fix", group = "Bug Fixes" },
    { message = "^docs", group = "Documentation" },
    { message = "^style", group = "Styling" },
    { message = "^refactor", group = "Code Refactoring" },
    { message = "^perf", group = "Performance Improvements" },
    { message = "^test", group = "Tests" },
    { message = "^build", group = "Build System" },
    { message = "^ci", group = "Continuous Integration" },
    { message = "^chore", group = "Chore" },
    { message = "^revert", group = "Reverts" },
]
'''
    
    try:
        with open("cliff.toml", 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        click.echo("[OK] git-cliff 설정 파일이 생성되었습니다: cliff.toml")
        
    except Exception as e:
        click.echo(f"❌ git-cliff 설정 파일 생성 중 오류: {e}", err=True)
        sys.exit(1)
