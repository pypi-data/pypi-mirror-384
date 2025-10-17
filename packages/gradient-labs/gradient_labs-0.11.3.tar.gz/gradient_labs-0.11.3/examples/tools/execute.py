import os

from gradient_labs import (
    Client,
    ToolExecuteParams,
    Argument,
)


def main():
    client = Client(
        api_key=os.environ["GLABS_LOCAL_MGMT_KEY"],
        base_url="http://127.0.0.1:4000",
    )

    tools = client.list_tools()
    for tool in tools:
        if tool.name == "Launch":
            print(f"Executing {tool.name}")
            rsp = client.execute_tool(
                params=ToolExecuteParams(
                    id=tool.id,
                    arguments=[
                        Argument(name="speed", value="slow"),
                    ],
                ),
            )
            print(f"Response: {rsp}")
    print("Done")


if __name__ == "__main__":
    main()
