"""mcp_seniverse_weather package"""
from .server import mcp
def main():
    """Entry point for mcp_seniverse_weather package"""
    mcp.run(transport='stdio')
if __name__ == '__main__':
    main()