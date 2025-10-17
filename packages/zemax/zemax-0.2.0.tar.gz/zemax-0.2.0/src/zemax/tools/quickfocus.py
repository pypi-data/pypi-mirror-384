from zemax.core import ZemaxStandAlone
def quick_focus(zs : ZemaxStandAlone, logger):
    try:
        zosapi = zs.ZOSAPI
        s = zs.TheSystem
        tools = s.Tools
        tools.RemoveAllVariables()
        qf = tools.OpenQuickFocus()
        qf.Criterion = zosapi.Tools.General.QuickFocusCriterion.SpotSizeRadial #TODO make it variable
        qf.UseCentroid = True
        qf.RunAndWaitForCompletion()
        qf.Close()
        return True

    except Exception as e:
        logger.warning("QuickFocus failed: %s", e)
        return False
