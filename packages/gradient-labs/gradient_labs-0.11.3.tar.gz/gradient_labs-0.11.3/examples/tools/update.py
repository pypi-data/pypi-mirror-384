import os

from gradient_labs import (
    Client,
    ToolParameter,
    ParameterType,
    ParameterOption,
    HTTPDefinition,
    HTTPBodyDefinition,
    BodyEncoding,
    ToolUpdateParams,
)


def main():
    client = Client(
        api_key=os.environ["GLABS_LOCAL_MGMT_KEY"],
        base_url="http://127.0.0.1:4000",
    )
    tool = client.update_tool(
        params=ToolUpdateParams(
            id="tool_01jq7crsj3em6byad308knw2c5",
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
                url_template="https://b4f8-2a00-23c4-ca02-4601-4d6f-e46c-76bc-3167.ngrok-free.app/launch",
                header_templates={"Content-Type": "application/json"},
                body=HTTPBodyDefinition(
                    encoding=BodyEncoding.JSON.value,
                    json_template='{"speed":"${params.speed}"}',
                ),
            ),
        )
    )
    print(f"Updated: {tool.id}")


if __name__ == "__main__":
    main()
