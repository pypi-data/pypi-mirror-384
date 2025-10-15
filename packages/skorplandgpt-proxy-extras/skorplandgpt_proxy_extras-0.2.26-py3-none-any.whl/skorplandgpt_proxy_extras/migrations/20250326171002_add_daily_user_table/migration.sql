-- CreateTable
CREATE TABLE "SkorplandGPT_DailyUserSpend" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "date" TEXT NOT NULL,
    "api_key" TEXT NOT NULL,
    "model" TEXT NOT NULL,
    "model_group" TEXT,
    "custom_llm_provider" TEXT,
    "prompt_tokens" INTEGER NOT NULL DEFAULT 0,
    "completion_tokens" INTEGER NOT NULL DEFAULT 0,
    "spend" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "SkorplandGPT_DailyUserSpend_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "SkorplandGPT_DailyUserSpend_date_idx" ON "SkorplandGPT_DailyUserSpend"("date");

-- CreateIndex
CREATE INDEX "SkorplandGPT_DailyUserSpend_user_id_idx" ON "SkorplandGPT_DailyUserSpend"("user_id");

-- CreateIndex
CREATE INDEX "SkorplandGPT_DailyUserSpend_api_key_idx" ON "SkorplandGPT_DailyUserSpend"("api_key");

-- CreateIndex
CREATE INDEX "SkorplandGPT_DailyUserSpend_model_idx" ON "SkorplandGPT_DailyUserSpend"("model");

-- CreateIndex
CREATE UNIQUE INDEX "SkorplandGPT_DailyUserSpend_user_id_date_api_key_model_custom_ll_key" ON "SkorplandGPT_DailyUserSpend"("user_id", "date", "api_key", "model", "custom_llm_provider");

