ROLE_PERMISSIONS = {
    "driver": {
        "view_self_runs": True,
        "report_run": True,
    },
    "field_officer": {
        "create_vehicle": True,
        "assign_vehicle": True,
        "create_driver": True,
        "view_team_reports": True,
        "transfer_vehicle": True,
        "record_service": True,
    },
    "executive": {
        "create_vehicle": True,
        "assign_vehicle": True,
        "create_field_officer": True,
        "view_all_reports": True,
        "transfer_vehicle": True,
        "record_service": True,
    },
}




def has_permission(user_role: str, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(user_role, {})
    return perms.get(permission, False)