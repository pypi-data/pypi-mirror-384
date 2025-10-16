"""
# Markten / Actions / Email

Actions for composing emails
"""

from markten import ActionSession
from markten.actions.__action import markten_action

from .__misc import open

__encoding_replacements = {
    # % needs to appear first, or we will double-encode everything
    "%": "%25",
    '"': "%22",
    " ": "%20",
    "\n": "%0D%0A",
    "?": "%3F",
    "&": "%26",
}


def __replace_all(s: str) -> str:
    for original, replacement in __encoding_replacements.items():
        s = s.replace(original, replacement)
    return s


def __make_params(params: dict[str, str | None]) -> str:
    return "&".join(
        f"{key}={__replace_all(value)}"
        for key, value in params.items()
        if value is not None
    )


@markten_action
async def compose(
    action: ActionSession,
    to: str | list[str],
    /,
    cc: str | list[str] | None = None,
    subject: str | None = None,
    body: str | None = None,
) -> None:
    """Compose an email to the given recipient(s)

    This launches a composer in user's preferred mail client, with the given
    information pre-filled.

    Parameters
    ----------
    to : str | list[str]
        Email address(es) to send to.
    cc : str | list[str]
        Email address(es) to send a carbon copy of the email to.
    subject : str
        Email subject.
    body : str
        Email body.

    Implementation based on RFC6086
    https://www.rfc-editor.org/rfc/rfc6068
    """
    # TODO: Support attachments, eg by using `xdg-email` command on Linux.
    # Perhaps I could also support specific email apps (eg Thunderbird) to
    # allow for specifying things like the sender. Doing that would be very
    # painful compared to a generic solution though.
    if isinstance(to, list):
        to = ",".join(to)

    if isinstance(cc, list):
        cc = ",".join(cc)

    options = __make_params(
        {
            "cc": cc,
            "subject": subject,
            "body": body,
        }
    )

    command = f"mailto:{to}?{options}"

    await open(action, command)
