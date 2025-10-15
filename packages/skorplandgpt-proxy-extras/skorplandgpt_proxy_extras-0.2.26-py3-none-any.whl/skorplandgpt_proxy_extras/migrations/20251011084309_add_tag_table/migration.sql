-- CreateTable
CREATE TABLE "SkorplandGPT_TagTable" (
    "tag_name" TEXT NOT NULL,
    "description" TEXT,
    "models" TEXT[],
    "model_info" JSONB,
    "spend" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    "budget_id" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_by" TEXT,
    "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "SkorplandGPT_TagTable_pkey" PRIMARY KEY ("tag_name")
);

-- AddForeignKey
ALTER TABLE "SkorplandGPT_TagTable" ADD CONSTRAINT "SkorplandGPT_TagTable_budget_id_fkey" FOREIGN KEY ("budget_id") REFERENCES "SkorplandGPT_BudgetTable"("budget_id") ON DELETE SET NULL ON UPDATE CASCADE;

