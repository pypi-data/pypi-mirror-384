-- AlterTable
ALTER TABLE "SkorplandGPT_ObjectPermissionTable" ADD COLUMN     "vector_stores" TEXT[] DEFAULT ARRAY[]::TEXT[];

