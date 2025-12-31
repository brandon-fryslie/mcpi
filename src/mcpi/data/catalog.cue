// MCP Server Catalog Schema
// This defines the exact format for catalog.json

// stdio transport: local server spawned as subprocess
#StdioServer: {
	type:        "stdio"
	description: string & !=""            // Non-empty description
	command:     string & !=""            // Non-empty command (e.g., "npx", "python", "node")
	args:        [...string]              // Array of string arguments
	env?:        {[string]: string}       // Optional environment variables
	repository:  string | null            // Optional repository URL
	categories?: [...string]              // Optional array of category strings
}

// http transport: remote server accessed via HTTP/SSE
#HttpServer: {
	type:        "http"
	description: string & !=""      // Non-empty description
	url:         string & !=""      // Non-empty URL endpoint
	headers?:    {[string]: string} // Optional HTTP headers (e.g., Authorization)
	repository:  string | null      // Optional repository URL
	categories?: [...string]        // Optional array of category strings
}

// An MCP server can be either stdio or http transport
#MCPServer: #StdioServer | #HttpServer

// The catalog is a flat map of server_id -> MCPServer
{
	[string]: #MCPServer
}
