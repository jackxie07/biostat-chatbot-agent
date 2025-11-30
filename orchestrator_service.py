from BiostatChatbot import BiostatChatbot, GEMINI_API_KEY
from adk_runtime import ADKOrchestratorClient


class OrchestratorAgent:
    """
    Orchestrator facade. Prefers ADK multi-agent graph if configured; falls
    back to the local BiostatChatbot flow otherwise.
    """

    def __init__(self, model_name: str = "gemini-1.5-flash", user_name: str = "songgu.xie"):
        self.adk_client = ADKOrchestratorClient()
        self.core = BiostatChatbot(api_key=GEMINI_API_KEY, model_name=model_name, user_name=user_name)

    def handle_message(self, user_input: str) -> str:
        """
        Single entry point used by the Flask endpoint. Uses ADK agent graph
        when configured; otherwise mirrors the prior local control flow.
        """
        if self.adk_client.configured:
            try:
                return self.adk_client.send_message(user_input)
            except NotImplementedError:
                # ADK client present but not yet implemented; fall back to local behavior
                pass

        bot = self.core
        if bot.analysis_detail is None:
            analysis_name = bot.find_stat_method(user_input)
            bot.set_analysis(analysis_name)
            _, ask_for = bot.filter_response(user_input, initial_input=True)
        elif bot.info_complete:
            _, ask_for = bot.update_info(user_input)
        else:
            _, ask_for = bot.filter_response(user_input)

        if bot.confirm_proceed:
            url = bot.execute_analysis()
            return bot.present_output(url)

        return bot.ask_for_info(ask_for)
