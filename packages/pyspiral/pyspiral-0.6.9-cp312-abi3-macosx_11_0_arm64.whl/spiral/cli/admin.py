from spiral.api.types import OrgId
from spiral.cli import CONSOLE, AsyncTyper, state

app = AsyncTyper()


@app.command()
def sync(
    org_id: OrgId | None = None,
):
    state.settings.api._admin.sync_orgs()

    for membership in state.settings.api._admin.sync_memberships(org_id):
        CONSOLE.print(membership)
