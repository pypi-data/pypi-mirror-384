#!/usr/bin/env python3
"""
Script to convert the upstream SCCB issue template to a Jinja2 template.
This creates a template that by default matches upstream exactly, but can be
customized for specific projects like GWCelery.
"""
import re
import sys


def convert_upstream_to_jinja(content):
    """Convert upstream SCCB template content to Jinja2 template format."""

    # Keep all content - replace description insertion comment with conditional
    # logic. These strings are copied directly from SCCB template.
    description_comment = '''<!-- Insert description of changes here,
     e.g. link to release notes, changelog, ...

NOTE: the most important thing to include here is a list of changes that could potentially affect other software, which other software might be affected (to the best of your understanding), and a description of what is motivating the change.

**Upgrade requests will not be approved until this information is provided**, so please provide in the initial request to facilitate the process.

-->'''

    # Replace both the standalone FIXME and the description comment together
    pattern = r'FIXME\s*\n\s*<!-- Insert description.*?-->\s*\n'
    replacement = ('{% if description -%}\n{{ description }}\n{%- else -%}'
                   '\nFIXME\n\n' + description_comment + '\n{%- endif %}\n\n')
    content = re.sub(pattern, replacement, content,
                     flags=re.DOTALL | re.MULTILINE)

    # Add header with macro and GWCelery defaults
    header = '''{%- macro checkbox(checked=false) -%}
[{{'x' if checked else ' '}}]
{%- endmacro -%}

{% if use_gwcelery_defaults -%}
{% set package_name = 'gwcelery' -%}
{% set development_url = '<https://git.ligo.org/emfollow/gwcelery>' -%}
{% set distributions = {
    'conda': false, 'debian_bullseye': false, 'debian_bookworm': false,
    'gwcelery': true, 'igwn_pool': false, 'rocky_linux_8': false,
    'rocky_linux_9': false, 'other': false
} -%}
{% set impacted_systems = {'low_latency_pipeline': true, 'dmt': false} -%}
{% set include_llai_voting = true -%}
{% endif -%}

'''
    content = header + content

    # All replacements as simple string substitutions
    replacements = {
        'FIXME <!-- insert package name -->':
            "{{ package_name or 'FIXME <!-- insert package name -->' }}",
        'FIXME <!-- insert updated package version -->':
            "{{ version or 'FIXME <!-- insert updated package version -->' }}",
        'FIXME <!-- insert http(s) URL to tarball, must be publicly '
        'accessible -->':
            "{{ source_url or 'FIXME <!-- insert http(s) URL to tarball, "
            "must be publicly accessible -->' }}",
        'FIXME <!-- insert http(s) URL to VCS -->':
            "{{ development_url or 'FIXME <!-- insert http(s) URL to "
            "VCS -->' }}",

        # Request types
        '- [ ] this is a new package':
            '- {{ checkbox(is_new_package) }} this is a new package',
        '- [ ] this is a backwards-compatible update':
            '- {{ checkbox(is_backwards_compatible) }} this is a '
            'backwards-compatible update',
        '- [ ] this is a backwards-incompatible update [API/ABI changes]':
            '- {{ checkbox(is_backwards_incompatible) }} this is a '
            'backwards-incompatible update [API/ABI changes]',

        # Distributions (preserving upstream defaults)
        '- [x] [Conda (conda-forge)]':
            '- {{ checkbox(distributions.conda if distributions is defined '
            'else true) }} [Conda (conda-forge)]',
        '- [ ] [Debian 11 (Bullseye)]':
            '- {{ checkbox(distributions.debian_bullseye if distributions '
            'is defined else false) }} [Debian 11 (Bullseye)]',
        '- [ ] [Debian 12 (Bookworm)]':
            '- {{ checkbox(distributions.debian_bookworm if distributions '
            'is defined else false) }} [Debian 12 (Bookworm)]',
        '- [ ] [GWCelery]':
            '- {{ checkbox(distributions.gwcelery if distributions is '
            'defined else false) }} [GWCelery]',
        '- [ ] [IGWN Pool]':
            '- {{ checkbox(distributions.igwn_pool if distributions is '
            'defined else false) }} [IGWN Pool]',
        '- [ ] [Rocky Linux 8]':
            '- {{ checkbox(distributions.rocky_linux_8 if distributions is '
            'defined else false) }} [Rocky Linux 8]',
        '- [ ] [Rocky Linux 9]':
            '- {{ checkbox(distributions.rocky_linux_9 if distributions is '
            'defined else false) }} [Rocky Linux 9]',
        '- [ ] Other | <!-- please link to details of the deployment '
        'strategy, or describe them immediately below -->':
            '- {{ checkbox(distributions.other if distributions is defined '
            'else false) }} Other | {{ distributions.other_description if '
            'distributions is defined and distributions.other else '
            '\'<!-- please link to details of the deployment strategy, or '
            'describe them immediately below -->\' }}',

        # Systems
        '- [ ] Low-latency pipeline':
            '- {{ checkbox(impacted_systems.low_latency_pipeline if '
            'impacted_systems is defined else false) }} Low-latency pipeline',
        '- [ ] Data Monitoring Tool (DMT)':
            '- {{ checkbox(impacted_systems.dmt if impacted_systems is '
            'defined else false) }} Data Monitoring Tool (DMT)',
    }

    # Apply all replacements
    for old, new in replacements.items():
        content = content.replace(old, new)

    # Add LLAI section
    llai = '''{% if include_llai_voting -%}
#### LLAI Voting

- [ ] @stuart.anderson
- [ ] @sara.vallero
- [ ] @pfc

{% endif -%}'''
    content = content.replace('#### SCCB Voting', llai + '#### SCCB Voting')

    return content


def main():
    """Main function to convert upstream template."""
    if len(sys.argv) != 3:
        print("Usage: python convert_upstream_to_jinja.py <input_file> "
              "<output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r') as f:
        content = f.read()

    jinja_content = convert_upstream_to_jinja(content)

    with open(output_file, 'w') as f:
        f.write(jinja_content)

    print(f"Converted upstream template saved to {output_file}")


if __name__ == '__main__':
    main()
