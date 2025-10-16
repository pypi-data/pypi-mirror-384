from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from dataflow.models import (
    user as m_user,
    session as m_session,
    org_associations as m_org_associations,
    role as m_role,
    organization as m_organization
)

def get_user_from_session(session_id: str, db: Session):
    """
    Retrieve user information based on the session ID.
    """
    user = (
        db.query(
            m_user.User,
            m_org_associations.OrganizationUser.role_id,
            m_role.Role.name,
            m_role.Role.base_role,
            m_org_associations.OrganizationUser.active_server_id,
            m_org_associations.OrganizationUser.show_server_page,
            m_org_associations.OrganizationUser.active_env_short_name,
            m_org_associations.OrganizationUser.active_env_type,
            m_org_associations.OrganizationUser.monthly_allocation,
            m_organization.Organization.uid
        )
        .join(m_session.Session, m_session.Session.user_id == m_user.User.user_id)
        .outerjoin(
            m_org_associations.OrganizationUser,
            and_(
                m_org_associations.OrganizationUser.user_id == m_user.User.user_id,
                m_org_associations.OrganizationUser.org_id == m_user.User.active_org_id
            )
        )
        .outerjoin(m_role.Role, m_role.Role.id == m_org_associations.OrganizationUser.role_id)
        .outerjoin(
            m_organization.Organization,
            m_organization.Organization.id == m_user.User.active_org_id  # join to Organization
        )
        .filter(m_session.Session.session_id == session_id)
        .first()
    )

    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")

    user_obj, role_id, role_name, base_role, active_server_id, show_server_page, active_env_short_name, active_env_type, monthly_allocation, uid = user
    user_obj.role_id = role_id
    user_obj.role = role_name
    user_obj.base_role = base_role
    user_obj.current_server_id = active_server_id
    user_obj.show_server_page = show_server_page
    user_obj.active_env = active_env_short_name
    user_obj.active_env_type = active_env_type
    user_obj.monthly_allocation = monthly_allocation
    user_obj.org_uid = str(uid)

    return user_obj