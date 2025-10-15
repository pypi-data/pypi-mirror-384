-- Add health check fields to MCP server table
ALTER TABLE "SkorplandGPT_MCPServerTable" ADD COLUMN "status" TEXT DEFAULT 'unknown';
ALTER TABLE "SkorplandGPT_MCPServerTable" ADD COLUMN "last_health_check" TIMESTAMP(3);
ALTER TABLE "SkorplandGPT_MCPServerTable" ADD COLUMN "health_check_error" TEXT; 