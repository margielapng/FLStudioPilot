from fastapi import APIRouter
from api.models.schemas import CommandRequest, CommandResponse
from core.ai.command_parser import parse_command
from core.fl_bridge import bridge_client

router = APIRouter(prefix="/commands", tags=["commands"])


@router.post("/", response_model=CommandResponse)
async def handle_command(req: CommandRequest):
    parsed = parse_command(req.text)

    if not parsed:
        return CommandResponse(
            success=False,
            message=f'Command not understood: "{req.text}". Try: play, stop, set bpm 140, mute channel 1.',
        )

    result = await bridge_client.send_command(parsed["action"], parsed["params"])

    return CommandResponse(
        success=result.get("ok", False),
        action=parsed["action"],
        params=parsed["params"],
        message=result.get("message", "Done"),
        fl_result=str(result),
    )


@router.get("/status")
async def get_fl_status():
    return await bridge_client.get_status()
