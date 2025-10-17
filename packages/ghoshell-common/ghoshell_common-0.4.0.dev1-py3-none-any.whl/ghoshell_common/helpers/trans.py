from gettext import dgettext, dngettext

__all__ = ['gettext', 'ngettext']

_DOMAIN = 'GhostInShells'


def gettext(message):
    return dgettext(_DOMAIN, message)


def ngettext(singular, plural, n):
    return dngettext(_DOMAIN, singular, plural, n)
