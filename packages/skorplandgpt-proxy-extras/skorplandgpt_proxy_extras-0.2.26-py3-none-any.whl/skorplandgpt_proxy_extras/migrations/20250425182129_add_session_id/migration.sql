-- AlterTable
ALTER TABLE "SkorplandGPT_SpendLogs" ADD COLUMN     "proxy_server_request" JSONB DEFAULT '{}',
ADD COLUMN     "session_id" TEXT;

