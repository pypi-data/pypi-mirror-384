from __future__ import annotations
from typing import Any, Optional, Mapping

try:
    from gql import gql, Client
    from gql.transport.requests import RequestsHTTPTransport
except Exception as e:
    raise ImportError(
        "GraphQL HTTP 클라이언트가 없습니다. "
        "pip install 'smu-ontwins-demo[http]' 또는 'gql[requests]' 를 설치하세요."
    ) from e

# 전역 상태
_client: Optional[Client] = None
_xdomain: Optional[str] = None

# Query
GET_DOMAINS = gql("""
query GetDomains {
  getDomains {
    id
    properties
  }
}
""")

def _make_client(base_url: str, token: str, extra_headers: Optional[Mapping[str, str]] = None) -> Client:
    headers = {"Authorization": f"Bearer {token}"}
    if extra_headers:
        headers.update(extra_headers)
    transport = RequestsHTTPTransport(
        url=f"{base_url.rstrip('/')}/graphql",
        headers=headers,
        timeout=30,
    )
    # 스키마 페치 생략으로 빠르게
    return Client(transport=transport, fetch_schema_from_transport=False)

def init_gql(base_url: str, token: str) -> str:
    """부트스트랩(무 X-Domain) → 도메인 조회 → X-Domain 붙여 최종 클라이언트 생성.
    반환값: 선택된 X-Domain ID
    """
    global _client, _xdomain

    # 1) 부트스트랩 클라이언트로 도메인 조회
    bootstrap = _make_client(base_url, token)
    data = bootstrap.execute(GET_DOMAINS) or {}
    domains = data.get("getDomains") or []

    if not domains:
        raise RuntimeError("getDomains 결과가 비어있습니다. X-Domain을 설정할 수 없습니다.")
    # 필요에 따라 특정 기준으로 선택하도록 바꿔도 됨
    _xdomain = domains[0].get("id")
    if not _xdomain:
        raise RuntimeError("도메인 객체에 id가 없습니다.")

    # 2) X-Domain 헤더를 붙여 최종 클라이언트 구성
    _client = _make_client(base_url, token, {"X-Domain": _xdomain})
    return _xdomain

def execute_gql(doc, variables: Optional[dict] = None) -> Any:
    """초기화된 클라이언트로 쿼리/뮤테이션 실행"""
    if _client is None:
        raise RuntimeError("GraphQL 클라이언트가 초기화되지 않았습니다. init_gql(...)을 먼저 호출하세요.")
    return _client.execute(doc, variable_values=(variables or {}))
