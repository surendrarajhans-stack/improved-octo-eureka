from enum import Enum

from fastapi import Depends, HTTPException, status


class UserRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    HOSPITAL_ADMIN = "HOSPITAL_ADMIN"
    DOCTOR = "DOCTOR"
    NURSE = "NURSE"
    RECEPTIONIST = "RECEPTIONIST"
    LAB_TECHNICIAN = "LAB_TECHNICIAN"
    RADIOLOGIST = "RADIOLOGIST"
    PHARMACIST = "PHARMACIST"
    CASHIER = "CASHIER"
    HR_MANAGER = "HR_MANAGER"
    ACCOUNTANT = "ACCOUNTANT"
    STORE_MANAGER = "STORE_MANAGER"
    PATIENT = "PATIENT"
    GUEST = "GUEST"


class Permission(str, Enum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    PRINT = "PRINT"
    EXPORT = "EXPORT"


ALL_PERMISSIONS = set(Permission)
LIMITED_PERMISSIONS = {Permission.READ}
CLINICAL_PERMISSIONS = {Permission.READ, Permission.CREATE, Permission.UPDATE, Permission.PRINT}
ADMIN_PERMISSIONS = {Permission.READ, Permission.CREATE, Permission.UPDATE, Permission.DELETE, Permission.PRINT, Permission.EXPORT}

ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.SUPER_ADMIN: ALL_PERMISSIONS,
    UserRole.HOSPITAL_ADMIN: ALL_PERMISSIONS,
    UserRole.DOCTOR: CLINICAL_PERMISSIONS | {Permission.EXPORT},
    UserRole.NURSE: {Permission.READ, Permission.CREATE, Permission.UPDATE, Permission.PRINT},
    UserRole.RECEPTIONIST: {Permission.READ, Permission.CREATE, Permission.UPDATE, Permission.PRINT},
    UserRole.LAB_TECHNICIAN: CLINICAL_PERMISSIONS,
    UserRole.RADIOLOGIST: CLINICAL_PERMISSIONS,
    UserRole.PHARMACIST: CLINICAL_PERMISSIONS,
    UserRole.CASHIER: {Permission.READ, Permission.CREATE, Permission.UPDATE, Permission.PRINT, Permission.EXPORT},
    UserRole.HR_MANAGER: ADMIN_PERMISSIONS,
    UserRole.ACCOUNTANT: ADMIN_PERMISSIONS,
    UserRole.STORE_MANAGER: ADMIN_PERMISSIONS,
    UserRole.PATIENT: LIMITED_PERMISSIONS,
    UserRole.GUEST: set(),
}


def has_permission(role: UserRole | str, permission: Permission | str) -> bool:
    return Permission(permission) in ROLE_PERMISSIONS.get(UserRole(role), set())


def require_permission(permission: Permission):
    from app.api.deps import get_current_active_user

    def checker(current_user=Depends(get_current_active_user)):
        if not has_permission(current_user.role, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return checker
