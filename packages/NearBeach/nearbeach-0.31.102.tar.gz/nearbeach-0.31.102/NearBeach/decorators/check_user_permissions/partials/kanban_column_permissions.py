from NearBeach.models import Group, KanbanColumn, ObjectAssignment, UserGroup
from django.db.models import Max, Q


# Internal Function
def kanban_column_permissions(request, kwargs):
    # Default user level is 0
    user_group_results = UserGroup.objects.filter(
        is_deleted=False,
        username=request.user,
    )

    if len(kwargs) > 0:
        # Determine if there are any cross over with user groups and object_lookup groups
        group_results = Group.objects.filter(
            Q(
                is_deleted=False,
                # The object_lookup groups
                group_id__in=ObjectAssignment.objects.filter(
                    is_deleted=False,
                    kanban_board_id__in=KanbanColumn.objects.filter(
                        kanban_column_id=kwargs["kanban_column_id"],
                    ).values("kanban_board_id"),
                ).values("group_id"),
            )
            & Q(group_id__in=user_group_results.values("group_id"))
        )

        # Check to make sure the user groups intersect
        if len(group_results) == 0:
            # There are no matching groups - i.e. the user does not have any permission
            return False, 0, False

    # Get the max permission value from user_group_results
    user_level = user_group_results.aggregate(
        Max("permission_set__kanban_board")
    )["permission_set__kanban_board__max"]

    return True, user_level, False

