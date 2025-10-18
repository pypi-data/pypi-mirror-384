import argparse
from rhsupportlib import RHsupportClient
from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_http_headers


mcp = FastMCP("rhsupportmcp")


@mcp.tool()
def create_case(context: Context,
                parameters: dict) -> dict:
    """Create case"""
    offlinetoken = get_http_headers().get('offlinetoken')
    rhc = RHsupportClient(offlinetoken, context=context)
    return rhc.create_case(parameters)


@mcp.tool()
def create_attachment(context: Context,
                      case: str, path: str):
    """Create attachment"""
    offlinetoken = get_http_headers().get('offlinetoken')
    rhc = RHsupportClient(offlinetoken, context=context)
    return rhc.create_attachment(case, path)


@mcp.tool()
def create_comment(context: Context,
                   case: str, comment: str):
    """Create comment"""
    offlinetoken = get_http_headers().get('offlinetoken')
    rhc = RHsupportClient(offlinetoken, context=context)
    return rhc.create_comment(case, comment)


@mcp.tool()
def get_attachments(context: Context,
                    case: str, path: str = '/tmp'):
    """Get attachments"""
    offlinetoken = get_http_headers().get('offlinetoken')
    rhc = RHsupportClient(offlinetoken, context=context)
    return rhc.get_attachments(case, path)


@mcp.tool()
def get_case(context: Context,
             case: str) -> dict:
    """Retrieve information on case"""
    offlinetoken = get_http_headers().get('offlinetoken')
    rhc = RHsupportClient(offlinetoken, context=context)
    return rhc.get_case(case)


@mcp.tool()
def list_cases(context: Context,
               parameters: list = {}) -> list:
    """List cases"""
    offlinetoken = get_http_headers().get('offlinetoken')
    rhc = RHsupportClient(offlinetoken, context=context)
    return rhc.list_cases(parameters)


@mcp.tool()
def list_customers(context: Context,
                   account: str = None) -> list:
    """List customers"""
    offlinetoken = get_http_headers().get('offlinetoken')
    rhc = RHsupportClient(offlinetoken, context=context)
    return rhc.list_customers(account)


@mcp.tool()
def list_partners(context: Context,
                  account: str = None) -> list:
    """List partners"""
    offlinetoken = get_http_headers().get('offlinetoken')
    rhc = RHsupportClient(offlinetoken, context=context)
    return rhc.list_partners(account)


@mcp.tool()
def list_contacts(context: Context,
                  account: str = None) -> list:
    """List contacts"""
    offlinetoken = get_http_headers().get('offlinetoken')
    rhc = RHsupportClient(offlinetoken, context=context)
    return rhc.list_accounts(account)


@mcp.tool()
def search_cases(context: Context,
                 q: str) -> list:
    """Search cases"""
    offlinetoken = get_http_headers().get('offlinetoken')
    rhc = RHsupportClient(offlinetoken, context=context)
    return rhc.search_cases({'q': q})


@mcp.tool()
def search_history(context: Context,
                   q: str, num_sources: int = 1, only_high_similarity_nodes: bool = False) -> str:
    """Search history"""
    history_url = get_http_headers().get('history_url')
    offlinetoken = get_http_headers().get('offlinetoken')
    rhc = RHsupportClient(offlinetoken, history_url=history_url, context=context)
    return rhc.search_history({'q': q, 'num_sources': 1, 'only_high_similarity_nodes': only_high_similarity_nodes})


@mcp.tool()
def search_kcs(context: Context,
               q: str) -> list:
    """Search kcs"""
    offlinetoken = get_http_headers().get('offlinetoken')
    rhc = RHsupportClient(offlinetoken, context=context)
    return rhc.search_kcs({'q': q})


@mcp.tool()
def update_case(context: Context,
                case: str, parameters: dict) -> dict:
    """Update case"""
    offlinetoken = get_http_headers().get('offlinetoken')
    rhc = RHsupportClient(offlinetoken, context=context)
    return rhc.update_case(case, parameters)


def main():
    parser = argparse.ArgumentParser(description="rhsupportmcp")
    parser.add_argument("--port", type=int, default=8000, help="Localhost port to listen on")
    parser.add_argument("-s", "--stdio", action='store_true')
    args = parser.parse_args()
    if args.stdio:
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="http", host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
