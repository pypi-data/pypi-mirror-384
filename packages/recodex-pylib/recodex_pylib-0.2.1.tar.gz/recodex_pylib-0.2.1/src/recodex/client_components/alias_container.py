class AliasContainer:
    """Class that handles the resolution of presenter and action aliases defined in aliases.yaml.
    """

    def __init__(self, definitions):
        self.definitions = definitions
        self.__presenter_suffix = '_presenter'

        self.__init_raw_resolve_dict()
        self.__init_default_aliases()

    def __init_raw_resolve_dict(self):
        # create a map from raw (with the 'presenter'/'action' prefix/suffix) presenter names to actions
        raw_presenter_to_action_map: dict[str, list[str]] = {}
        for operation_id in self.definitions.keys():
            presenter_pos = operation_id.find(self.__presenter_suffix)
            if presenter_pos == -1:
                raise RuntimeError(
                    f"The operationId '{operation_id}' does not contain the '{self.__presenter_suffix}' substring"
                )

            presenter_name = operation_id[0: presenter_pos] + self.__presenter_suffix
            action_name = operation_id[presenter_pos + len(self.__presenter_suffix) + 1:]

            if presenter_name in raw_presenter_to_action_map:
                raw_presenter_to_action_map[presenter_name].append(action_name)
            else:
                raw_presenter_to_action_map[presenter_name] = [action_name]
        self.raw_presenter_to_action_map = raw_presenter_to_action_map

    def __init_default_aliases(self):
        # maps aliases to raw presenter name
        presenter_aliases: dict[str, str] = {}
        # a list of presenter names without the '_presenter' suffix (used in 'did you mean... error messages')
        base_presenter_aliases: list[str] = []
        for presenter_name in self.raw_presenter_to_action_map.keys():
            # keep the raw name as a valid alias
            presenter_aliases[presenter_name] = presenter_name

            # add raw name without the '_presenter' suffix
            shortened_name = presenter_name[: -len(self.__presenter_suffix)]
            presenter_aliases[shortened_name] = presenter_name

            base_presenter_aliases.append(shortened_name)
        self.presenter_aliases = presenter_aliases
        self.base_presenter_aliases = base_presenter_aliases

        # maps raw presenter names to a dict from action aliases to raw action names
        action_aliases: dict[str, dict[str, str]] = {}
        # maps raw presenter names to a list of action aliases without the 'action_' prefix
        base_action_aliases: dict[str, list[str]] = {}
        for presenter_name, action_names in self.raw_presenter_to_action_map.items():
            aliases = {}
            base_aliases = []
            for action_name in action_names:
                # keep the raw name as a valid alias
                aliases[action_name] = action_name

                # add raw name without the 'action_' prefix
                shortened_name = action_name[len('action_'):]
                aliases[shortened_name] = action_name

                base_aliases.append(shortened_name)
            action_aliases[presenter_name] = aliases
            base_action_aliases[presenter_name] = base_aliases
        self.action_aliases = action_aliases
        self.base_action_aliases = base_action_aliases

    def __get_raw_presenter_name_or_throw(self, presenter):
        if presenter not in self.presenter_aliases:
            msg = f"'{presenter}' is not a known presenter name or alias. Use one of the presenters below:"
            for presenter_alias in self.base_presenter_aliases:
                msg += f"\n{presenter_alias}"
            raise RuntimeError(msg)
        return self.presenter_aliases[presenter]

    def __get_raw_action_name_or_throw(self, presenter, action):
        raw_presenter_name = self.__get_raw_presenter_name_or_throw(presenter)
        aliases = self.action_aliases[raw_presenter_name]
        if action not in aliases:
            msg = f"'{action}' is not a known action name or alias. Use one of the actions below:"
            for action_alias in self.base_action_aliases[raw_presenter_name]:
                msg += f"\n{action_alias}"
            raise RuntimeError(msg)
        return aliases[action]

    def add_presenter_alias(self, presenter, alias):
        raw_presenter_name = self.__get_raw_presenter_name_or_throw(presenter)

        if alias in self.presenter_aliases:
            raise RuntimeError(
                f"Presenter alias '{alias}' is already registered for the '{self.presenter_aliases[alias]}' presenter"
            )

        # the value has to be the raw presenter name
        self.presenter_aliases[alias] = raw_presenter_name

    def add_action_alias(self, presenter, action, alias):
        raw_presenter_name = self.__get_raw_presenter_name_or_throw(presenter)
        raw_action_name = self.__get_raw_action_name_or_throw(presenter, action)
        aliases = self.action_aliases[raw_presenter_name]

        if alias in aliases:
            raise RuntimeError(
                f"The action alias '{alias}' is already registered for the '{aliases[alias]}' action"
            )

        # the value has to be the raw action name
        aliases[alias] = raw_action_name

    def get_operation_id(self, presenter: str, action: str) -> str:
        """Returns an ID identifying the endpoint.

        Args:
            presenter (str): The name of the presenter or alias.
            action (str): The name of the action or alias.

        Raises:
            RuntimeError: Thrown when the presenter of action could not be resolved.

        Returns:
            str: Returns an ID identifying the endpoint.
        """

        raw_presenter_name = self.__get_raw_presenter_name_or_throw(presenter)
        raw_action_name = self.__get_raw_action_name_or_throw(presenter, action)
        return f"{raw_presenter_name}_{raw_action_name}"

    def get_presenters(self) -> list[str]:
        """Returns a list of presenters in snake case without the '_presenter' suffix.

        Returns:
            list[str]: Returns a list of presenters in snake case without the '_presenter' suffix.
        """
        return self.base_presenter_aliases

    def get_actions(self, presenter: str) -> list[str]:
        """Returns a list of actions in snake case without the 'action_' prefix.

        Args:
            presenter (str): The presenter containing the actions. Can be any presenter alias.

        Returns:
            list[str]: Returns a list of actions in snake case without the 'action_' prefix.
        """
        base_presenter = self.__get_raw_presenter_name_or_throw(presenter)
        return self.base_action_aliases[base_presenter]
