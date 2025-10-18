#!/usr/bin/env python3
"""
Script to render SCCB issue template using Jinja2.
Provides GWCelery-specific values and enables template defaults.
"""
import os

from jinja2 import Environment, FileSystemLoader


def render_sccb_template(template_path, output_path, **kwargs):
    """Render SCCB template with given parameters."""

    # Set up Jinja2 environment
    template_dir = os.path.dirname(template_path)
    template_name = os.path.basename(template_path)
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)

    # Render template with provided variables
    rendered = template.render(**kwargs)

    # Write to output file
    with open(output_path, 'w') as f:
        f.write(rendered)

    print(f"Template rendered successfully to {output_path}")


def main():
    """Main function to render SCCB template from environment variables."""

    # Get required environment variables
    version = os.getenv('VERSION', 'UNKNOWN')
    ci_project_url = os.getenv('CI_PROJECT_URL', 'UNKNOWN')
    changes_filename = os.getenv('CHANGES_FILENAME', 'CHANGES.md')
    last_version = os.getenv('LAST_VERSION', '')
    last_major_minor_version = os.getenv('LAST_MAJOR_MINOR_VERSION', '')
    major_minor_version = os.getenv('MAJOR_MINOR_VERSION', '')

    # Build minimal template variables - template handles defaults
    template_vars = {
        'version': version,
        'source_url': f'<https://pypi.org/packages/source/g/'
        f'gwcelery/gwcelery-{version}.tar.gz>',
        'description': (
            f'See [change log]({ci_project_url}/-/blob/v{version}/'
            f'{changes_filename}) and [diff from last release]'
            f'({ci_project_url}/-/compare/v{last_version}...v{version}).'
            if last_version else f'See [change log]({ci_project_url}/-/blob/'
            f'v{version}/{changes_filename}).'
        ),

        # Request type logic
        'is_new_package': not last_major_minor_version,
        'is_backwards_compatible': (
            bool(last_major_minor_version) and
            major_minor_version == last_major_minor_version
        ),
        'is_backwards_incompatible': (
            bool(last_major_minor_version) and
            major_minor_version != last_major_minor_version
        ),

        # Enable GWCelery-specific defaults and LLAI voting
        'use_gwcelery_defaults': True
    }

    # Note: We don't need to define distributions or impacted_systems
    # The template handles these with sensible defaults

    # Render template
    template_path = 'gwcelery/templates/sccb_template.jinja2'
    output_path = 'rendered_sccb_template.md'

    render_sccb_template(template_path, output_path, **template_vars)


if __name__ == '__main__':
    main()
