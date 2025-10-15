import json
from .scout_agent import ScoutAgent
from scoutsdk import ScoutAPI
from scouttypes import ConversationMessage, MessageRole


class ScoutAgentRunner:
    def __init__(self, agents: list[ScoutAgent]) -> None:
        self._agents = agents

    def handoff_instructions(self, agents: list[ScoutAgent]) -> str:
        agents_definition = ""
        for agent in agents:
            agents_definition += f"{agent.id}: {agent.handoff_description}"

        return f"""
    If you cannot have the ability or function to answer the request, you MUST handoff to one of the following agent.

    {agents_definition}

    If you need to handoff, response exactly without any backticks or anything:
    {{"handoff_to": "agent_id"}}
    """

    def agent_by_ids(self, agent_ids: list[str]) -> list[ScoutAgent]:
        return [agent for agent in self._agents if agent.id in agent_ids]

    def agent_by_id(self, agent_id: str) -> ScoutAgent:
        return next(agent for agent in self._agents if agent.id == agent_id)

    def _agent_instruction_with_handoffs(self, agent: ScoutAgent) -> str:
        instructions = agent.resolved_instructions
        if agent.handoff_ids and len(agent.handoff_ids) > 0:
            instructions += "\n" + self.handoff_instructions(
                self.agent_by_ids(agent.handoff_ids)
            )
        return instructions

    def execute_agent(
        self,
        agent: ScoutAgent,
        conversation: list[ConversationMessage],
        debug: bool = False,
    ) -> list[ConversationMessage]:
        if debug:
            print(f" {agent.id}\n    {conversation[-1].content}")
        messages = [
            ConversationMessage(
                role=MessageRole.SYSTEM,
                content=self._agent_instruction_with_handoffs(agent),
            )
        ]
        messages += conversation
        result = ScoutAPI().chat.completion(
            messages=messages,
            tools=agent.tools,
            model=agent.model_id,
            allowed_tools=agent.allowed_tools,
        )
        last_response = result.messages[-1].content

        completion_conversation = conversation + result.messages
        if isinstance(last_response, str):
            try:
                json_content = json.loads(last_response)
                handoff_id = json_content.get("handoff_to")
                if handoff_id:
                    return self.execute_handoff(
                        agent, handoff_id, completion_conversation, debug=debug
                    )
            except json.JSONDecodeError:
                pass
        return completion_conversation

    def execute_handoff(
        self,
        calling_agent: ScoutAgent,
        handoff_id: str,
        conversation: list[ConversationMessage],
        debug: bool = False,
    ) -> list[ConversationMessage]:
        agent_to_call = self.agent_by_id(handoff_id)

        if not agent_to_call:
            raise Exception(f"Agent {handoff_id} not found.")
        conversation.append(
            ConversationMessage(
                role=MessageRole.USER,
                content=f"{calling_agent.id} agent has transfered the conversation to you.",
            )
        )
        return self.execute_agent(agent_to_call, conversation, debug=debug)
