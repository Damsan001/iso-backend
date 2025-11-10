# region Imports

from sqlalchemy import true
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.infrastructure.models import (
    Rol,
    Empresa,
    Usuario,
    AuditLog,
    Permiso,
    UsuarioPermiso,
)
from app.services.auth_service import check_auth_and_roles
from app.schemas.Dtos.AdminDtos import (
    RoleDTO,
    CreateRoleDTO,
    UpdateRoleDTO,
    PermissionDTO,
    CreatePermissionDTO,
    UpdatePermissionDTO,
)


# endregion


# region Empresas
def read_all_empresas(db: Session, user: dict):
    check_auth_and_roles(user, ["Administrador"])

    empresas = db.query(Empresa).all()
    return empresas


def search_empresas(db: Session, user: dict, empresa_id: int | None = None):
    check_auth_and_roles(user, ["Administrador"])
    filters = []

    if empresa_id is not None:
        filters.append(Empresa.empresa_id == empresa_id)

    filters.append(Empresa.estatus == "ACTIVA")

    condition = true() if not filters else None

    q = db.query(Empresa)
    if condition is not None:
        q = q.filter(condition)
    else:
        q = q.filter(*filters)

    return q.all()


# endregion


# region Roles
def read_all_roles(db: Session, user: dict):
    check_auth_and_roles(user, ["Administrador"])

    roles = (
        db.query(Rol)
        .filter(Rol.activo == True)
        .filter(Rol.empresa_id == user.get("empresa_id"))
        .all()
    )
    return [RoleDTO.model_validate(r) for r in roles]


def read_role_by_name(db: Session, user: dict, role_name: str):
    check_auth_and_roles(user, ["Administrador"])

    roles = (
        db.query(Rol)
        .filter(Rol.nombre.like(f"%{role_name}%"))
        .filter(Rol.empresa_id == user.get("empresa_id"))
        .filter(Rol.activo == True)
        .all()
    )
    if not roles:
        return None
    return [RoleDTO.model_validate(r) for r in roles]


def create_role_service(db: Session, user: dict, role_data: CreateRoleDTO):
    check_auth_and_roles(user, ["Administrador"])

    existing = (
        db.query(Rol)
        .filter(
            Rol.nombre == role_data.nombre, Rol.empresa_id == user.get("empresa_id")
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="El rol ya existe"
        )

    new_role = Rol(**role_data.model_dump())
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return RoleDTO.model_validate(new_role)


def update_role_service(
    db: Session, user: dict, role_id: int, role_data: CreateRoleDTO
):
    check_auth_and_roles(user, ["Administrador"])

    role = (
        db.query(Rol)
        .filter(Rol.rol_id == role_id)
        .filter(Rol.empresa_id == user.get("empresa_id"))
        .first()
    )
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado"
        )

    for key, value in role_data.model_dump().items():
        setattr(role, key, value)

    db.commit()
    db.refresh(role)
    return RoleDTO.model_validate(role)


def delete_role_service(db: Session, user: dict, role_id: int):
    check_auth_and_roles(user, ["Administrador"])

    role = (
        db.query(Rol)
        .filter(Rol.rol_id == role_id)
        .filter(Rol.empresa_id == user.get("empresa_id"))
        .first()
    )
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado"
        )

    role.activo = False
    db.commit()
    return {"message": "Rol eliminado exitosamente"}


def patch_role_service(db: Session, user: dict, role_id: int, role_data: UpdateRoleDTO):
    check_auth_and_roles(user, ["Administrador"])

    role = (
        db.query(Rol)
        .filter(Rol.rol_id == role_id)
        .filter(Rol.empresa_id == user.get("empresa_id"))
        .first()
    )
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado"
        )

    update_data = role_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(role, key, value)

    db.commit()
    db.refresh(role)
    return RoleDTO.model_validate(role)


def add_roles_to_user_service(
    db: Session, user: dict, user_id: int, role_ids: list[int]
):
    check_auth_and_roles(user, ["Administrador"])

    usuario = db.query(Usuario).filter(Usuario.usuario_id == user_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )

    roles_antes = [r.rol_id for r in usuario.roles]

    roles = db.query(Rol).filter(Rol.rol_id.in_(role_ids), Rol.activo == True).all()
    if not roles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron roles válidos",
        )

    usuario.roles.extend([r for r in roles if r not in usuario.roles])
    db.flush()
    roles_despues = [r.rol_id for r in usuario.roles]

    db.add(
        AuditLog(
            table_name="usuario_rol",
            operation="UPDATE",
            target_pk_id=user_id,
            target_pk={"usuario_id": user_id},
            actor=str(user.get("email")),
            before={"roles": roles_antes},
            after={"roles": roles_despues},
        )
    )

    db.commit()
    db.refresh(usuario)
    return {"message": "Roles agregados exitosamente"}


def remove_roles_from_user_service(
    db: Session, user: dict, user_id: int, role_ids: list[int]
):
    check_auth_and_roles(user, ["Administrador"])

    usuario = db.query(Usuario).filter(Usuario.usuario_id == user_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )

    roles_antes = [r.rol_id for r in usuario.roles]

    roles_to_remove = (
        db.query(Rol).filter(Rol.rol_id.in_(role_ids), Rol.activo == True).all()
    )
    found_role_ids = {r.rol_id for r in roles_to_remove}
    missing = set(role_ids) - found_role_ids
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Los siguientes roles no existen o no están activos: {list(missing)}",
        )

    for role in roles_to_remove:
        if role in usuario.roles:
            usuario.roles.remove(role)

    db.flush()  # Para que los cambios estén disponibles antes de auditar
    roles_despues = [r.rol_id for r in usuario.roles]

    db.add(
        AuditLog(
            table_name="usuario_rol",
            operation="DELETE",
            target_pk_id=user_id,
            target_pk={"usuario_id": user_id},
            actor=str(user.get("email")),
            before={"roles": roles_antes},
            after={"roles": roles_despues},
        )
    )

    db.commit()
    db.refresh(usuario)
    return {"message": "Roles eliminados exitosamente"}


def get_roles_by_user_service(db: Session, user: dict, user_id: int):
    check_auth_and_roles(user, ["Administrador"])
    usuario = db.query(Usuario).filter(Usuario.usuario_id == user_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )

    return [RoleDTO.model_validate(r) for r in usuario.roles if r.activo]


def get_permissions_by_role_service(db: Session, user: dict, role_id: int):
    check_auth_and_roles(user, ["Administrador"])
    rol = (
        db.query(Rol)
        .filter(Rol.rol_id == role_id, Rol.activo == True)
        .filter(Rol.empresa_id == user.get("empresa_id"))
        .first()
    )
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado"
        )
    return [PermissionDTO.model_validate(permiso) for permiso in rol.permisos]


# endregion


# region Permisos
def read_all_permissions(db: Session, user: dict):
    check_auth_and_roles(user, ["Administrador"])

    permisos = (
        db.query(Permiso)
        .filter(Permiso.empresa_id == user.get("empresa_id"))
        .filter(Permiso.activo == True)
        .all()
    )
    return [PermissionDTO.model_validate(p) for p in permisos]


def read_permission_by_name(db: Session, user: dict, permission_name: str):
    check_auth_and_roles(user, ["Administrador"])

    permisos = (
        db.query(Permiso)
        .filter(Permiso.nombre.like(f"%{permission_name}%"))
        .filter(Permiso.empresa_id == user.get("empresa_id"))
        .filter(Permiso.activo == True)
        .all()
    )
    if not permisos:
        return None
    return [PermissionDTO.model_validate(p) for p in permisos]


def create_permission_service(
    db: Session, user: dict, permission_data: CreatePermissionDTO
):
    check_auth_and_roles(user, ["Administrador"])

    existing = (
        db.query(Permiso)
        .filter(
            Permiso.nombre == permission_data.nombre,
            Permiso.empresa_id == user.get("empresa_id"),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="El permiso ya existe"
        )

    new_permission = Permiso(**permission_data.model_dump())
    db.add(new_permission)
    db.commit()
    db.refresh(new_permission)
    return PermissionDTO.model_validate(new_permission)


def update_permission_service(
    db: Session, user: dict, permission_id: int, permission_data: CreatePermissionDTO
):
    check_auth_and_roles(user, ["Administrador"])

    permission = (
        db.query(Permiso)
        .filter(Permiso.permiso_id == permission_id)
        .filter(Permiso.empresa_id == user.get("empresa_id"))
        .first()
    )
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Permiso no encontrado"
        )

    for key, value in permission_data.model_dump().items():
        setattr(permission, key, value)

    db.commit()
    db.refresh(permission)
    return PermissionDTO.model_validate(permission)


def patch_permission_service(
    db: Session, user: dict, permission_id: int, permission_data: UpdatePermissionDTO
):
    check_auth_and_roles(user, ["Administrador"])

    permission = (
        db.query(Permiso)
        .filter(Permiso.permiso_id == permission_id)
        .filter(Permiso.empresa_id == user.get("empresa_id"))
        .first()
    )
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Permiso no encontrado"
        )

    update_data = permission_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(permission, key, value)

    db.commit()
    db.refresh(permission)
    return PermissionDTO.model_validate(permission)


def delete_permission_service(db: Session, user: dict, permission_id: int):
    check_auth_and_roles(user, ["Administrador"])

    permission = (
        db.query(Permiso)
        .filter(Permiso.permiso_id == permission_id)
        .filter(Permiso.empresa_id == user.get("empresa_id"))
        .first()
    )
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Permiso no encontrado"
        )

    permission.activo = False
    db.commit()
    db.refresh(permission)
    return {"message": "Permiso eliminado exitosamente"}


def add_permissions_to_user_service(
    db: Session, user: dict, user_id: int, permission_ids: list[int]
):
    check_auth_and_roles(user, ["Administrador"])

    usuario = db.query(Usuario).filter(Usuario.usuario_id == user_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )

    permisos_antes = [p.permiso_id for p in usuario.permisos_directos]

    permisos = (
        db.query(Permiso)
        .filter(Permiso.permiso_id.in_(permission_ids), Permiso.activo == True)
        .all()
    )
    if not permisos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron permisos válidos",
        )

    nuevos = []
    for permiso in permisos:
        existe = (
            db.query(UsuarioPermiso)
            .filter_by(usuario_id=user_id, permiso_id=permiso.permiso_id)
            .first()
        )
        if not existe:
            up = UsuarioPermiso(
                usuario_id=user_id, permiso_id=permiso.permiso_id, concedido=True
            )
            db.add(up)
            nuevos.append(permiso.permiso_id)

    db.flush()
    permisos_despues = [p.permiso_id for p in usuario.permisos_directos]

    db.add(
        AuditLog(
            table_name="usuario_permiso",
            operation="UPDATE",
            target_pk_id=user_id,
            target_pk={"usuario_id": user_id},
            actor=str(user.get("email")),
            before={"permisos": permisos_antes},
            after={"permisos": permisos_despues},
        )
    )

    db.commit()
    db.refresh(usuario)
    return {"message": f"Permisos agregados exitosamente: {nuevos}"}


def remove_permissions_from_user_service(
    db: Session, user: dict, user_id: int, permission_ids: list[int]
):
    check_auth_and_roles(user, ["Administrador"])

    usuario = db.query(Usuario).filter(Usuario.usuario_id == user_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )

    permisos_antes = [p.permiso_id for p in usuario.permisos_directos]

    permisos_to_remove = (
        db.query(Permiso)
        .filter(Permiso.permiso_id.in_(permission_ids), Permiso.activo == True)
        .all()
    )
    found_permission_ids = {p.permiso_id for p in permisos_to_remove}
    missing = set(permission_ids) - found_permission_ids
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Los siguientes permisos no existen o no están activos: {list(missing)}",
        )

    for permiso in permisos_to_remove:
        if permiso in usuario.permisos_directos:
            usuario.permisos_directos.remove(permiso)

    db.flush()  # Para que los cambios estén disponibles antes de auditar
    permisos_despues = [p.permiso_id for p in usuario.permisos_directos]

    db.add(
        AuditLog(
            table_name="usuario_permiso",
            operation="DELETE",
            target_pk_id=user_id,
            target_pk={"usuario_id": user_id},
            actor=str(user.get("email")),
            before={"permisos": permisos_antes},
            after={"permisos": permisos_despues},
        )
    )

    db.commit()
    db.refresh(usuario)
    return {"message": "Permisos eliminados exitosamente"}


def get_permissions_by_user_service(db: Session, user: dict, user_id: int):
    check_auth_and_roles(user, ["Administrador"])
    usuario = db.query(Usuario).filter(Usuario.usuario_id == user_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )

    return [
        PermissionDTO.model_validate(p) for p in usuario.permisos_directos if p.activo
    ]


def add_permissions_to_role_service(
    db: Session, user: dict, role_id: int, permission_ids: list[int]
):
    check_auth_and_roles(user, ["Administrador"])
    rol = db.query(Rol).filter(Rol.rol_id == role_id, Rol.activo == True).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    permisos = (
        db.query(Permiso)
        .filter(Permiso.permiso_id.in_(permission_ids), Permiso.activo == True)
        .all()
    )
    if not permisos:
        raise HTTPException(
            status_code=404, detail="No se encontraron permisos válidos"
        )

    permisos_antes = [p.permiso_id for p in rol.permisos]
    nuevos = []
    for permiso in permisos:
        if permiso not in rol.permisos:
            rol.permisos.append(permiso)
            nuevos.append(permiso.permiso_id)

    db.flush()
    permisos_despues = [p.permiso_id for p in rol.permisos]
    db.add(
        AuditLog(
            table_name="rol_permiso",
            operation="UPDATE",
            target_pk_id=role_id,
            target_pk={"rol_id": role_id},
            actor=str(user.get("email")),
            before={"permisos": permisos_antes},
            after={"permisos": permisos_despues},
        )
    )
    db.commit()
    db.refresh(rol)
    return {"message": f"Permisos agregados exitosamente: {nuevos}"}


def remove_permissions_from_role_service(
    db: Session, user: dict, role_id: int, permission_ids: list[int]
):
    check_auth_and_roles(user, ["Administrador"])
    rol = db.query(Rol).filter(Rol.rol_id == role_id, Rol.activo == True).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    permisos_antes = [p.permiso_id for p in rol.permisos]
    permisos_to_remove = (
        db.query(Permiso)
        .filter(Permiso.permiso_id.in_(permission_ids), Permiso.activo == True)
        .all()
    )
    found_permission_ids = {p.permiso_id for p in permisos_to_remove}
    missing = set(permission_ids) - found_permission_ids
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Los siguientes permisos no existen o no están activos: {list(missing)}",
        )

    for permiso in permisos_to_remove:
        if permiso in rol.permisos:
            rol.permisos.remove(permiso)

    db.flush()
    permisos_despues = [p.permiso_id for p in rol.permisos]
    db.add(
        AuditLog(
            table_name="rol_permiso",
            operation="DELETE",
            target_pk_id=role_id,
            target_pk={"rol_id": role_id},
            actor=str(user.get("email")),
            before={"permisos": permisos_antes},
            after={"permisos": permisos_despues},
        )
    )
    db.commit()
    db.refresh(rol)
    return {"message": "Permisos eliminados exitosamente"}


def get_permissions_by_role_service(db: Session, user: dict, role_id: int):
    check_auth_and_roles(user, ["Administrador"])
    rol = (
        db.query(Rol)
        .filter(Rol.rol_id == role_id, Rol.activo == True)
        .filter(Rol.empresa_id == user.get("empresa_id"))
        .first()
    )
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado"
        )
    return [
        PermissionDTO.model_validate(permiso)
        for permiso in rol.permisos
        if permiso.activo
    ]


# endregion
