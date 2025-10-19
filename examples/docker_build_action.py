"""
Example: Docker Build and Push Action

This action builds a Docker image, scans it for vulnerabilities, and pushes it
to a container registry with proper tagging.
"""

import os
import re
import subprocess
from pathlib import Path

from github_action_toolkit import (
    EventPayload,
    JobSummary,
    add_mask,
    error,
    get_user_input,
    get_user_input_as,
    group,
    info,
    set_output,
    warning,
)


def validate_image_name(image: str) -> bool:
    """Validate Docker image name format."""
    pattern = r'^[a-z0-9]+(?:[._-][a-z0-9]+)*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*$'
    return bool(re.match(pattern, image.lower()))


def get_image_tags(event: EventPayload, tag_prefix: str) -> list[str]:
    """Generate appropriate tags based on the event."""
    tags = []

    # Always add commit SHA tag
    tags.append(f'{tag_prefix}:{event.sha[:8]}')

    # Add branch/PR tags
    if event.is_pr():
        pr_number = event.get_pr_number()
        if pr_number:
            tags.append(f'{tag_prefix}:pr-{pr_number}')
    elif event.ref.startswith('refs/heads/'):
        branch = event.ref.replace('refs/heads/', '')
        # Clean branch name for tag
        clean_branch = re.sub(r'[^a-z0-9._-]', '-', branch.lower())
        tags.append(f'{tag_prefix}:{clean_branch}')

        # Add 'latest' for main/master
        if branch in ['main', 'master']:
            tags.append(f'{tag_prefix}:latest')

    return tags


def docker_login(registry: str, username: str, password: str):
    """Login to Docker registry."""
    add_mask(password)  # Mask password from logs

    result = subprocess.run(
        ['docker', 'login', registry, '-u', username, '--password-stdin'],
        input=password.encode(),
        capture_output=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f'Docker login failed: {result.stderr.decode()}')

    info(f'✓ Logged into {registry}')


def docker_build(dockerfile: Path, context: Path, image_tag: str, build_args: dict) -> str:
    """Build Docker image."""
    cmd = ['docker', 'build', '-f', str(dockerfile), '-t', image_tag]

    # Add build args
    for key, value in build_args.items():
        cmd.extend(['--build-arg', f'{key}={value}'])

    cmd.append(str(context))

    info(f'Building image: {image_tag}')
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f'Docker build failed:\n{result.stderr}')

    # Get image ID
    result = subprocess.run(
        ['docker', 'images', '-q', image_tag], capture_output=True, text=True
    )
    image_id = result.stdout.strip()

    info(f'✓ Built image: {image_id[:12]}')
    return image_id


def docker_push(image_tag: str):
    """Push Docker image to registry."""
    info(f'Pushing {image_tag}...')

    result = subprocess.run(['docker', 'push', image_tag], capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f'Docker push failed:\n{result.stderr}')

    info(f'✓ Pushed {image_tag}')


def scan_image(image_tag: str) -> dict:
    """Scan image for vulnerabilities (example using trivy)."""
    info(f'Scanning {image_tag} for vulnerabilities...')

    result = subprocess.run(
        ['trivy', 'image', '--format', 'json', '--quiet', image_tag],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        warning(f'Image scan completed with warnings')
        return {}

    # Parse scan results (simplified)
    # In production, parse the JSON and extract vulnerability counts
    info('✓ Security scan complete')
    return {'critical': 0, 'high': 2, 'medium': 5, 'low': 10}


def create_summary(image: str, tags: list[str], image_id: str, scan_results: dict):
    """Create job summary for the build."""
    summary = JobSummary()

    summary.add_heading('Docker Build Summary', 1)

    # Build info
    summary.add_table(
        [
            ['Property', 'Value'],
            ['Image', image],
            ['Image ID', image_id[:12]],
            ['Tags', str(len(tags))],
        ]
    )

    # Tags
    summary.add_separator()
    summary.add_heading('Image Tags', 2)
    for tag in tags:
        summary.add_raw(f'- `{tag}`\n')

    # Security scan
    if scan_results:
        summary.add_separator()
        summary.add_heading('Security Scan', 2)
        summary.add_table(
            [
                ['Severity', 'Count'],
                ['Critical', str(scan_results.get('critical', 0))],
                ['High', str(scan_results.get('high', 0))],
                ['Medium', str(scan_results.get('medium', 0))],
                ['Low', str(scan_results.get('low', 0))],
            ]
        )

        if scan_results.get('critical', 0) > 0:
            summary.add_separator()
            summary.add_quote('⚠️ Critical vulnerabilities detected!')

    summary.write()


def main():
    """Main action entry point."""
    # Get inputs
    image_name = get_user_input('image-name')
    if not image_name:
        error('image-name is required', title='Missing Input')
        return 1

    if not validate_image_name(image_name):
        error(
            f'Invalid image name: {image_name}. '
            'Must contain only lowercase letters, numbers, and separators.',
            title='Invalid Input',
        )
        return 1

    registry = get_user_input('registry') or 'docker.io'
    dockerfile = Path(get_user_input('dockerfile') or 'Dockerfile')
    context = Path(get_user_input('context') or '.')
    push_enabled = get_user_input_as('push', bool, default_value=True)
    scan_enabled = get_user_input_as('scan', bool, default_value=True)

    # Get credentials (mask them)
    username = get_user_input('username')
    password = get_user_input('password')
    if password:
        add_mask(password)

    # Validate files exist
    if not dockerfile.exists():
        error(f'Dockerfile not found: {dockerfile}', title='File Not Found')
        return 1

    if not context.exists():
        error(f'Build context not found: {context}', title='Directory Not Found')
        return 1

    info(f'Building {image_name} from {dockerfile}')

    # Get event info for tagging
    event = EventPayload()
    full_image_name = f'{registry}/{image_name}'
    tags = get_image_tags(event, full_image_name)

    info(f'Will create {len(tags)} tags')

    # Build arguments
    build_args = {
        'BUILD_DATE': event.sha,
        'VCS_REF': event.sha[:8],
    }

    image_id = None
    scan_results = {}

    try:
        # Build image
        with group('Building Image'):
            image_id = docker_build(dockerfile, context, tags[0], build_args)

        # Tag with all tags
        with group('Tagging Image'):
            for tag in tags[1:]:
                subprocess.run(['docker', 'tag', tags[0], tag], check=True)
                info(f'✓ Tagged as {tag}')

        # Security scan
        if scan_enabled:
            with group('Security Scan'):
                scan_results = scan_image(tags[0])

        # Push to registry
        if push_enabled:
            if not username or not password:
                warning(
                    'Username/password not provided, skipping push',
                    title='Push Skipped',
                )
            else:
                with group('Pushing to Registry'):
                    docker_login(registry, username, password)
                    for tag in tags:
                        docker_push(tag)
        else:
            info('Push disabled, skipping')

        # Create summary
        with group('Creating Summary'):
            create_summary(full_image_name, tags, image_id or '', scan_results)

        # Set outputs
        set_output('image', full_image_name)
        set_output('tags', ','.join(tags))
        if image_id:
            set_output('image-id', image_id)

        info('✓ Docker build and push complete')
        return 0

    except Exception as e:
        error(f'Action failed: {e}', title='Build Failed')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
