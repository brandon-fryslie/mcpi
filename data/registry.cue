// MCP Server Registry Schema
// This defines the exact format for registry.json

// Each server entry must have exactly these fields
#MCPServer: {
	description: string & !=""  // Non-empty description
	command:     string & !=""  // Non-empty command (e.g., "npx", "python", "node")
	args:        [...string]     // Array of string arguments
	repository:  string | null   // Optional repository URL
}

// The registry is a flat map of server_id -> MCPServer
{
	[string]: #MCPServer
}