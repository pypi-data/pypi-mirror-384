-- AlterTable
ALTER TABLE "SkorplandGPT_OrganizationTable" ADD COLUMN     "object_permission_id" TEXT;

-- AlterTable
ALTER TABLE "SkorplandGPT_TeamTable" ADD COLUMN     "object_permission_id" TEXT;

-- AlterTable
ALTER TABLE "SkorplandGPT_UserTable" ADD COLUMN     "object_permission_id" TEXT;

-- AlterTable
ALTER TABLE "SkorplandGPT_VerificationToken" ADD COLUMN     "object_permission_id" TEXT;

-- CreateTable
CREATE TABLE "SkorplandGPT_ObjectPermissionTable" (
    "object_permission_id" TEXT NOT NULL,
    "mcp_servers" TEXT[] DEFAULT ARRAY[]::TEXT[],

    CONSTRAINT "SkorplandGPT_ObjectPermissionTable_pkey" PRIMARY KEY ("object_permission_id")
);

-- AddForeignKey
ALTER TABLE "SkorplandGPT_OrganizationTable" ADD CONSTRAINT "SkorplandGPT_OrganizationTable_object_permission_id_fkey" FOREIGN KEY ("object_permission_id") REFERENCES "SkorplandGPT_ObjectPermissionTable"("object_permission_id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "SkorplandGPT_TeamTable" ADD CONSTRAINT "SkorplandGPT_TeamTable_object_permission_id_fkey" FOREIGN KEY ("object_permission_id") REFERENCES "SkorplandGPT_ObjectPermissionTable"("object_permission_id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "SkorplandGPT_UserTable" ADD CONSTRAINT "SkorplandGPT_UserTable_object_permission_id_fkey" FOREIGN KEY ("object_permission_id") REFERENCES "SkorplandGPT_ObjectPermissionTable"("object_permission_id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "SkorplandGPT_VerificationToken" ADD CONSTRAINT "SkorplandGPT_VerificationToken_object_permission_id_fkey" FOREIGN KEY ("object_permission_id") REFERENCES "SkorplandGPT_ObjectPermissionTable"("object_permission_id") ON DELETE SET NULL ON UPDATE CASCADE;

