# Agent.py
from dotenv import load_dotenv
import os

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import noise_cancellation
from livekit.plugins import google

from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION, generate_email_prompt, summarize_email_prompt
from tools import get_weather, search_web, send_email

load_dotenv()


# -------------------------
# Assistant Definition
# -------------------------
class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                voice="Aoede",
                temperature=0.8,
            ),
            tools=[
                get_weather,
                search_web,
                send_email
            ],
        )


# -------------------------
# Helper function to generate + send email
# -------------------------
async def generate_and_send_email(session, to_email, subject, topic, from_account):
    """
    Generates an email using AI and sends it using the selected Gmail account.
    """
    # Generate email content via AI
    generated_message = await session.generate_reply(
        instructions=generate_email_prompt.format(
            from_account=from_account,
            to_email=to_email,
            topic=topic
        )
    )

    # Send the email using your multi-account tool
    result = await send_email(
        to_email=to_email,
        subject=subject,
        message=generated_message,
        from_account=from_account
    )

    print(result)
    return result


# -------------------------
# Main entrypoint
# -------------------------
async def entrypoint(ctx: agents.JobContext):
    # Start the agent session
    session = AgentSession()

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    # -------------------------
    # Example: Generate and send email
    # -------------------------
    # This is where you tell the agent to create & send an email
    await generate_and_send_email(
        session=session,
        to_email="professor@example.com",
        subject="Assignment Extension Request",
        topic="requesting an extension for assignment submission",
        from_account="miguel07"
    )

    # Continue with normal session instructions if needed
    await session.generate_reply(
        instructions=SESSION_INSTRUCTION,
    )


# -------------------------
# Run app
# -------------------------
if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint)
    )