-- AlterTable
ALTER TABLE "SkorplandGPT_DailyUserSpend" ADD COLUMN     "cache_creation_input_tokens" INTEGER NOT NULL DEFAULT 0,
ADD COLUMN     "cache_read_input_tokens" INTEGER NOT NULL DEFAULT 0;

