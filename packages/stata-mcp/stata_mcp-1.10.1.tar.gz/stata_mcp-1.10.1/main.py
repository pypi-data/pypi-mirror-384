from stata_mcp import stata_mcp as mcp


def main(transport: str = "stdio"):
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
