from typing import Optional
from gql import gql

from .core.keycloak import DeviceFlowAuth, DeviceAuthConfig
from .core.gql import init_gql, execute_gql

# 전역 상태
_SSO_SERVER: Optional[str] = None
_API_SERVER: Optional[str] = None
_auth: Optional[DeviceFlowAuth] = None

def init_auth(sso_server: str, api_server: str):
    global _SSO_SERVER, _API_SERVER, _auth
    _SSO_SERVER = sso_server
    _API_SERVER = api_server

    if not _auth:
        _auth = DeviceFlowAuth(
            DeviceAuthConfig(
                api_server_url=_API_SERVER,
                sso_server_url=_SSO_SERVER,
                client_id="sso-client",
            ),
        )

    authenticated = _auth.refresh_if_needed()
    if not authenticated: _auth.login(open_browser=True)

    _set_auth_for_gql()

def _set_auth_for_gql():
    global _API_SERVER, _auth
    _auth.refresh_if_needed()
    init_gql(_API_SERVER, _auth.get_access_token())

def _exec_with_auto_refresh(doc, variables: Optional[dict] = None):
    """execute_gql 래퍼: UNAUTHENTICATED이면 토큰 리프레시 후 1회 재시도.
    리프레시 실패 시엔 에러를 그대로 전파.
    """
    try:
        return execute_gql(doc, variables or {})
    except Exception as e:
        # 토큰 리프레시 시도
        if _auth is None or not _auth.refresh_if_needed():
            # 리프레시 실패 시 에러
            raise
        # 새 토큰으로 GQL 클라이언트 재생성 후 한 번 더 시도
        _set_auth_for_gql()
        return execute_gql(doc, variables or {})

def get_twin_data():
    FindEntitiesByTags = gql("""
    query FindEntitiesByTags($tags: [String!]!) {
        findEntitiesByTags(input: { tags: $tags }) {
            id
            properties
            system_properties
            createdAt
            updatedAt
            deletedAt
        }
    }
    """)
    EntitiesTree = gql("""
    query EntitiesTree($ids: [ID!]!) {
        entitiesTree(ids: $ids) {
            id
            properties
            system_properties
        }
    }
    """)

    tags = ["rack"]
    tagged_racks = _exec_with_auto_refresh(FindEntitiesByTags, {"tags": tags}).get("findEntitiesByTags", [])

    ids = [rack["id"] for rack in tagged_racks]
    racks = _exec_with_auto_refresh(EntitiesTree, {"ids": ids}).get("entitiesTree", [])

    sorted_racks = sorted(
        racks,
        key=lambda d: (d["properties"]["worldPosition"][0], d["properties"]["worldPosition"][1])
    )
    return sorted_racks
