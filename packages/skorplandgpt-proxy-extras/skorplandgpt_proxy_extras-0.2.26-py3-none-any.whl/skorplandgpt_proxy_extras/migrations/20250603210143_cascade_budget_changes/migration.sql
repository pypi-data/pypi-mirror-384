-- DropForeignKey
ALTER TABLE "SkorplandGPT_TeamMembership" DROP CONSTRAINT "SkorplandGPT_TeamMembership_budget_id_fkey";

-- AddForeignKey
ALTER TABLE "SkorplandGPT_TeamMembership" ADD CONSTRAINT "SkorplandGPT_TeamMembership_budget_id_fkey" FOREIGN KEY ("budget_id") REFERENCES "SkorplandGPT_BudgetTable"("budget_id") ON DELETE CASCADE ON UPDATE CASCADE;

