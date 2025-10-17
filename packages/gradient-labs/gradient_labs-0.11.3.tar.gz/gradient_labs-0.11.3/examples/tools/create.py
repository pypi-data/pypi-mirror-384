import os

from gradient_labs import (
    Client,
    Tool,
    ToolParameter,
    ParameterType,
    ParameterOption,
    HTTPDefinition,
    HTTPBodyDefinition,
    BodyEncoding,
)


def main():
    client = Client(
        api_key=os.environ["GLABS_LOCAL_MGMT_KEY"],
        base_url="http://127.0.0.1:4000",
    )
    tool = client.create_tool(
        tool=Tool(
            name="Launch",
            description="Send the rocket into the stratosphere",
            parameters=[
                ToolParameter(
                    name="speed",
                    description="How fast the rocket will be launched",
                    type=ParameterType.STRING,
                    required=True,
                    options=[
                        ParameterOption(value="slow", text="Slow"),
                        ParameterOption(value="medium", text="Medium"),
                        ParameterOption(value="warp-speed", text="Warp Speed"),
                    ],
                )
            ],
            http=HTTPDefinition(
                method="POST",
                url_template="https://a0e6-2a00-23c4-ca02-4601-4d6f-e46c-76bc-3167.ngrok-free.app/launch",
                body=HTTPBodyDefinition(
                    encoding=BodyEncoding.JSON.value,
                    json_template='{"speed":"${params.speed}"}',
                ),
            ),
        )
    )
    print(f"Created: {tool.id}")


if __name__ == "__main__":
    main()
