from models.raid_wizard_session import RaidWizardSession


class WizardService:
    """
    Manages active raid creation wizard sessions.
    """

    _sessions: dict[int, RaidWizardSession] = {}

    @classmethod
    def create_session(cls, owner_id: int) -> RaidWizardSession:
        """
        Starts a new wizard session for a user.
        """

        session = RaidWizardSession(owner_id=owner_id)

        cls._sessions[owner_id] = session

        return session

    @classmethod
    def get_session(cls, owner_id: int) -> RaidWizardSession | None:
        """
        Returns the user's active wizard session.
        """

        return cls._sessions.get(owner_id)

    @classmethod
    def remove_session(cls, owner_id: int):
        """
        Removes a wizard session.
        """

        cls._sessions.pop(owner_id, None)

    @classmethod
    def has_session(cls, owner_id: int) -> bool:
        """
        Returns True if the user has an active wizard.
        """

        return owner_id in cls._sessions