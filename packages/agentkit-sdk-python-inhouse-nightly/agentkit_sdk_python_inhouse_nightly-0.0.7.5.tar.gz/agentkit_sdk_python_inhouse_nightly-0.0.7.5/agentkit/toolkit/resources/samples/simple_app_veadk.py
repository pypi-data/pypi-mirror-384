import logging
import os

from veadk import Agent, Runner
from veadk.tools.demo_tools import get_city_weather
from veadk.tracing.telemetry.exporters.apmplus_exporter import APMPlusExporter
from veadk.tracing.telemetry.exporters.cozeloop_exporter import CozeloopExporter
from veadk.tracing.telemetry.exporters.tls_exporter import TLSExporter
from veadk.tracing.telemetry.opentelemetry_tracer import OpentelemetryTracer

from agentkit.apps import AgentkitSimpleApp

logger = logging.getLogger(__name__)


app = AgentkitSimpleApp()

exporters = [
    APMPlusExporter() if os.getenv("ENABLE_APMPLUS", "").lower() == "true" else None,
    CozeloopExporter() if os.getenv("ENABLE_COZELOOP", "").lower() == "true" else None,
    TLSExporter() if os.getenv("ENABLE_TLS", "").lower() == "true" else None,
]
tracer = OpentelemetryTracer(
    exporters=[exporter for exporter in exporters if exporter is not None]
)

agent = Agent(tracers=[tracer], tools=[get_city_weather])
runner = Runner(agent=agent)


@app.entrypoint
async def run(payload: dict, headers: dict) -> str:
    prompt = payload["prompt"]
    user_id = headers["user_id"]
    session_id = headers["session_id"]

    logger.info(
        f"Running agent with prompt: {prompt}, user_id: {user_id}, session_id: {session_id}"
    )
    response = await runner.run(messages=prompt, user_id=user_id, session_id=session_id)

    logger.info(f"Run response: {response}")
    return response


@app.ping
def ping() -> str:
    return "pong!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
