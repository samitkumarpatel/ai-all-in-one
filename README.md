# ai-all-in-one

In this repo we will have demo for 

- mcp:
	- Open protocol
	- It's a way your llm to interact to the data (tools , function)
	- mcp local (stdio, streamable http transport)
	- mcp remote  (streamable http transport)
	- sdk (fast-MCP, spring AI, sdk's from openai, claude and etc ...)
	- mcp inspector
	- mcp registry
	- Tools - Tools enable AI models to interact with external systems. Each tools define a specific operations with input and output
	- Resources - Resources provide read-only access to data that the AI application can retrive and provide as context to models. @mcp.resource(file://.....) or @mcp.resource(config://settings)
	- Prompts - Provide reusable prompts for a domain or showcase how to best use the MCP server. @mcp.prompt(title="")
	- Elicitation
	- Progress Reporting and Monitoring
- mcp apps:

- ai agent: 
	- agents are combination of model + Instruction
- a2a:
	- a2a i.e. agent2agent protocol is an Open protocol from google that standardizes how agents running on diverse frameworks and platforms communicate
	- communitcate between two or more agent using their own stack
	- There are many sdk
	- a2a inspector
	- How a2a works? (Discovery + Interactions + Agent Executor)
	- agent card - is a Json , describe about agent like what agent can do, URL and etc..
		- Capabilities [I can do streaming, push notification]
		- Skills [A, B, ..]
		- Authentication: [oauth2]
			```sh
				agent_card = { name:..., description:...,url:....,version:....}
			```	
	- agent executor
- a2a client:
	- a chat interface / CLI to interact to tools, agent and etc...

- ag-ui:
	- all about how the event travel
	- Open protocol
	- It's an light weight protocol.
	- Copilot Kit
	- AG-UI interactive Dojo

- a2ui: 
	- generate interactive UI
	- A2UI is a gen UI protocol, from google that enables AI agent rich, interactive user interface across web, mobile and desktop
	- transport agnostic
	- Four core message : createSurface, updateComponent, updateDataModel, dataSurface
		- createSurface: Create a new surface and specify it's catalog
		- updateComponents - Add or update UI components in a surface
		- updateDataModel - Update application state
		- deleteSurface - Remove an UI surface.
	- Catalog of UI components
		- Layout: Row, Column, List - arrange other components.
		- Display: text, image, icon, video, Divider - show information.
		- Interactivity: Button, textField, checkbox, dateTimeInput, Slider - userInput
		- Container: card, tabs. Modal - group and organize content
	- a2ui composer - https://a2ui-composer.ag-ui.com


- a2ui spec, mcp-ui spec, Open-JSON-UI spec, Your own custom spec


