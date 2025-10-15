-- AlterTable
ALTER TABLE "SkorplandGPT_DailyTagSpend" ALTER COLUMN "tag" DROP NOT NULL;

-- AlterTable
ALTER TABLE "SkorplandGPT_DailyTeamSpend" ALTER COLUMN "team_id" DROP NOT NULL;

-- AlterTable
ALTER TABLE "SkorplandGPT_DailyUserSpend" ALTER COLUMN "user_id" DROP NOT NULL;

