-- AlterTable
ALTER TABLE "SkorplandGPT_MCPServerTable" ADD COLUMN     "allowed_tools" TEXT[] DEFAULT ARRAY[]::TEXT[];

