#coding=utf-8

"""
Agent backend base module.
"""

class AgentBackendBase(object):
    """
    Agent backend base class.
    """

    def __init__(self, vagent, config, **kwargs):
        """
        Initialize the agent backend with the given configuration.

        :param vagent: The verification agent instance.
        :param config: Configuration dictionary for the backend.
        """
        self.vagent = vagent
        self.config = config
        self.kwargs = kwargs
        self._stat_msg_count_ai = 0
        self._stat_msg_count_tool = 0
        self._stat_msg_count_system = 0

    def init(self):
        """
        Initialize the backend.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def get_human_message(self, text: str):
        """
        Create and return a human message with the given text.

        :param text: The text content of the human message.
        :return: A HumanMessage instance.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def get_system_message(self, text: str):
        """
        Create and return a system message with the given text.

        :param text: The text content of the system message.
        :return: A SystemMessage instance.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def messages_get_raw(self):
        """
        Retrieve raw messages from the backend.

        :return: A list of raw messages.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def do_work_values(self, instructions, config):
        """
        Perform work based on the given instructions and configuration.

        :param instructions: Instructions for the work to be done.
        :param config: Configuration for the work.
        :return: Results of the work performed.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def do_work_stream(self, instructions, config):
        """
        Perform work in a streaming manner based on the given instructions and configuration.

        :param instructions: Instructions for the work to be done.
        :param config: Configuration for the work.
        :return: A generator yielding results of the work performed.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    # Optional methods
    def start_or_resume_thread(self):
        """
        Start or resume a structured backend conversation.

        Backends that expose a persistent agent kernel (for example Codex
        app-server) should override this method. Legacy command-line and
        LangChain backends can keep the default no-op behavior.
        """
        return None

    def run_turn(self, prompt, config=None):
        """
        Run one structured backend turn.

        This is intentionally separate from do_work_values(): VeriAgent's
        outer loop maps one supervised round to one backend turn, while legacy
        backends may still only support opaque work execution.
        """
        return self.do_work_values({"messages": [prompt]}, config or {})

    def stream_events(self, turn_handle=None):
        """
        Yield structured backend events for the active turn when supported.
        """
        return iter(())

    def interrupt(self):
        """
        Interrupt the active backend turn when supported.
        """
        return False

    def current_thread_id(self):
        """
        Return the current backend thread/session id when supported.
        """
        return None

    def current_turn_id(self):
        """
        Return the current backend turn id when supported.
        """
        return None

    def last_turn_summary(self):
        """
        Return structured metadata for the most recent backend turn.
        """
        return {}

    def requires_verification_only_mcp(self) -> bool:
        """
        Whether the backend owns generic file/shell tools itself.

        Codex-bound backends should return True so VeriAgent only exposes
        verification-domain tools over MCP.
        """
        return False

    def get_message_manage_node(self):
        """
        Get the message management node.

        :return: The message management node.
        """
        return None

    def get_work_config(self):
        """
        Get the work configuration.
        :return: The work configuration.
        """
        return {}

    def exit(self):
        """
        Clean up resources before exiting the backend.
        """
        pass

    def close(self):
        """
        Close backend resources.

        This mirrors the Codex SDK naming while preserving the historical
        VeriAgent exit() hook.
        """
        return self.exit()

    def set_debug(self, debug):
        """
        Set the debug mode for the backend.

        :param debug: Boolean indicating whether to enable debug mode.
        """
        pass

    def token_total(self) -> int:
        """
        Get the total number of tokens processed.

        :return: Total token count.
        """
        return -1

    def token_speed(self) -> float:
        """
        Get the token processing speed.

        :return: Token speed.
        """
        return -1.0

    def get_statistics(self) -> dict:
        """
        Get statistics related to the backend.

        :return: A dictionary of statistics.
        """
        return {
            "message_in": -1,
            "message_out": -1,
        }

    def model_name(self) -> str:
        """
        Get the name of the model used in the backend.

        :return: Model name.
        """
        return "UnknownModel"

    def temperature(self) -> float:
        """
        Get the temperature setting of the model.

        :return: Temperature value.
        """
        return -1.0

    def on_stage_complete(self, stage):
        """
        Callback method called when a stage is finished.

        :param stage: The stage that has finished.
        """
        pass

    def reset_chat(self, force=False):
        """
        Reset the chat state, if applicable.
        """
        pass
