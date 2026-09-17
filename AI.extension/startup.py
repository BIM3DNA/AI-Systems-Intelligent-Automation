"""Register BIMCode AI in pyRevit's persistent extension-startup engine."""

from pyrevit import HOST_APP, script

try:
    from bimcode_ai_pane.lifecycle import start
    start(HOST_APP.uiapp)
except Exception as error:
    script.get_logger().error("BIMCode AI startup failed: {0}".format(error))
