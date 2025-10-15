-- AlterTable
ALTER TABLE "SkorplandGPT_VerificationToken" ADD COLUMN     "allowed_routes" TEXT[] DEFAULT ARRAY[]::TEXT[];

