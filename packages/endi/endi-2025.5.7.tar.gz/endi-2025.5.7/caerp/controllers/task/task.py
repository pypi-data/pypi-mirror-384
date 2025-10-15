from caerp.models.task.task import Task


def get_task_params_from_other_task(request, user, task: Task) -> dict:
    """
    Get task parameters from another task.
    Can be used to generate invoice from estimation, or create an invoice into
    a same business ...

    Args:
        request: The current request object.
    """
    return dict(
        user=user,
        company=task.company,
        project=task.project,
        phase_id=task.phase_id,
        payment_conditions=task.payment_conditions,
        address=task.address,
        workplace=task.workplace,
        mentions=[mention for mention in task.mentions if mention.active],
        business_type_id=task.business_type_id,
        mode=task.mode,
        display_ttc=task.display_ttc,
        decimal_to_display=task.decimal_to_display,
        business_id=task.business_id,
    )
