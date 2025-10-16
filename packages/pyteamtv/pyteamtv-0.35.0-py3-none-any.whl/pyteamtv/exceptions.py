class PyTeamTVError(Exception):
    pass


class TeamNotFound(PyTeamTVError):
    pass


class InputError(PyTeamTVError):
    pass


class TokenMissing(PyTeamTVError):
    pass


class ConfigurationError(PyTeamTVError):
    pass
