import click
from importlib.resources import files


def add_site_repos_to_rc(path_to_site_repos):
    path_to_rc = files("imsi").joinpath("imsi.site.rc")
    with open(path_to_rc, "a") as f:
        # append IMSI_DEFAULT_CONFIG_REPOS=path_to_site_repos
        f.write(f"\nIMSI_DEFAULT_CONFIG_REPOS={path_to_site_repos}\n")
    click.echo(f"Added IMSI_DEFAULT_CONFIG_REPOS={path_to_site_repos} to {path_to_rc}")


@click.command()
@click.option('--path-to-site-repos', help='Location on disk where site-repos are stored. Will add value to the imsi.site.rc file. Not meant for regular imsi users, only for system install.', required=True)
def post_install(path_to_site_repos):
    add_site_repos_to_rc(path_to_site_repos)
