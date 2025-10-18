"""
Absfuyu: Web
------------
Web, ``request``, ``BeautifulSoup`` stuff

Version: 5.12.0
Date updated: 17/10/2025 (dd/mm/yyyy)
"""

# Library
# ---------------------------------------------------------------------------
import requests
from bs4 import BeautifulSoup

from absfuyu.logger import logger


# Function
# ---------------------------------------------------------------------------
def soup_link(link: str) -> BeautifulSoup:
    """
    ``BeautifulSoup`` the link

    Parameters
    ----------
    link : str
        Link to BeautifulSoup

    Returns
    -------
    BeautifulSoup
        ``BeautifulSoup`` instance
    """
    try:
        page = requests.get(link)
        soup = BeautifulSoup(page.content, "html.parser")
        logger.debug("Soup completed!")
        return soup
    except Exception:
        logger.error("Can't soup")
        raise SystemExit("Something wrong")  # noqa: B904


def gen_random_commit_msg() -> str:
    """
    Generate random commit message

    Returns
    -------
    str
        Random commit message
    """
    out = soup_link("https://whatthecommit.com/").get_text()[34:-20]
    logger.debug(out)
    return out  # type: ignore
