import pss.schema
import pss.psstypes

settings = pss.Settings(
    prog="Learning Observer",
    description="A system for monitoring",
    epilog="For more information, see PSS documentation."
)

settings.register_field(
    name="server_port",
    command_line_flags=["-p", "--port"],
    type=pss.psstypes.TYPES.port,
    description="The port Learning Observer should run on.",
    default=8888
)

settings.load()
settings.validate()
