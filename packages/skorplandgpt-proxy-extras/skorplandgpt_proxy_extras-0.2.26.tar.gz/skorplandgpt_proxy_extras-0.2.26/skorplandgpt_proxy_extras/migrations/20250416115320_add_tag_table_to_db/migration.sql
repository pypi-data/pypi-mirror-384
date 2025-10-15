-- AlterTable
ALTER TABLE "SkorplandGPT_DailyTeamSpend" ADD COLUMN     "cache_creation_input_tokens" INTEGER NOT NULL DEFAULT 0,
ADD COLUMN     "cache_read_input_tokens" INTEGER NOT NULL DEFAULT 0;

-- CreateTable
CREATE TABLE "SkorplandGPT_DailyTagSpend" (
    "id" TEXT NOT NULL,
    "tag" TEXT NOT NULL,
    "date" TEXT NOT NULL,
    "api_key" TEXT NOT NULL,
    "model" TEXT NOT NULL,
    "model_group" TEXT,
    "custom_llm_provider" TEXT,
    "prompt_tokens" INTEGER NOT NULL DEFAULT 0,
    "completion_tokens" INTEGER NOT NULL DEFAULT 0,
    "cache_read_input_tokens" INTEGER NOT NULL DEFAULT 0,
    "cache_creation_input_tokens" INTEGER NOT NULL DEFAULT 0,
    "spend" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "api_requests" INTEGER NOT NULL DEFAULT 0,
    "successful_requests" INTEGER NOT NULL DEFAULT 0,
    "failed_requests" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "SkorplandGPT_DailyTagSpend_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "SkorplandGPT_DailyTagSpend_tag_key" ON "SkorplandGPT_DailyTagSpend"("tag");

-- CreateIndex
CREATE INDEX "SkorplandGPT_DailyTagSpend_date_idx" ON "SkorplandGPT_DailyTagSpend"("date");

-- CreateIndex
CREATE INDEX "SkorplandGPT_DailyTagSpend_tag_idx" ON "SkorplandGPT_DailyTagSpend"("tag");

-- CreateIndex
CREATE INDEX "SkorplandGPT_DailyTagSpend_api_key_idx" ON "SkorplandGPT_DailyTagSpend"("api_key");

-- CreateIndex
CREATE INDEX "SkorplandGPT_DailyTagSpend_model_idx" ON "SkorplandGPT_DailyTagSpend"("model");

-- CreateIndex
CREATE UNIQUE INDEX "SkorplandGPT_DailyTagSpend_tag_date_api_key_model_custom_llm_pro_key" ON "SkorplandGPT_DailyTagSpend"("tag", "date", "api_key", "model", "custom_llm_provider");

