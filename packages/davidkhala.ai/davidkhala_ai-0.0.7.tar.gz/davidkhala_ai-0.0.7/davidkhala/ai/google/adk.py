from google.adk.agents import Agent

def with_opik(agent:Agent, **options):
    from opik.integrations.adk import OpikTracer

    _ = OpikTracer(
        name=agent.name,
        metadata={
            "model": agent.model,
            "framework": "google-adk",
        },
        **options
    )
    agent.before_agent_callback = _.before_agent_callback
    agent.after_agent_callback = _.after_agent_callback
    agent.before_model_callback = _.before_model_callback
    agent.after_model_callback = _.after_model_callback
    agent.before_tool_callback = _.before_tool_callback
    agent.after_tool_callback = _.after_tool_callback

